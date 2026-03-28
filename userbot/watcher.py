from telethon import events
from telethon.tl.functions.messages import ExportChatInviteRequest
from telethon.tl.functions.channels import CreateChannelRequest
from telethon.errors import ChatAdminRequiredError, ChatNotModifiedError
from database.db import SessionLocal
from database.models import TelegramEntity, BackupMapping
from feature.scanner.models import FoundLink
from datetime import datetime
import asyncio
from userbot.backup_manager import (
    get_dest_channel,
    increment_message_count
)
from userbot.config import SCAN_LIMIT_PER_RUN, JOIN_LIMIT_PER_RUN, JOIN_DELAY_SECONDS
from feature.scanner.service import scan_chat, get_pending_links, mark_link_result, ensure_entity_for_chat
from feature.scanner.joiner import join_from_link
from feature.scanner.limiter import safe_delay

def register_handlers(client):
    """Registra los manejadores de eventos del userbot"""

    @client.on(events.NewMessage(pattern='/scan'))
    async def scan_handler(event):
        """Comando para escanear todos los grupos y canales actuales"""
        await event.respond("🔍 Escaneando todos tus grupos y canales...")
        
        session = SessionLocal()
        count = 0
        count_with_link = 0
        count_without_link = 0
        count_updated = 0
        errors = []
        
        try:
            async for dialog in client.iter_dialogs():
                try:
                    chat = dialog.entity

                    # Bots (users con flag bot=True)
                    if getattr(chat, 'bot', False):
                        invite_link = None
                        try:
                            if getattr(chat, 'username', None):
                                invite_link = f"https://t.me/{chat.username}"
                                count_with_link += 1
                            else:
                                count_without_link += 1
                        except Exception:
                            count_without_link += 1

                        try:
                            existing = session.query(TelegramEntity).filter_by(telegram_id=chat.id).first()

                            if existing:
                                existing.title = getattr(chat, 'first_name', None) or getattr(chat, 'username', None)
                                existing.username = getattr(chat, 'username', None)
                                existing.invite_link = invite_link or existing.invite_link
                                existing.entity_type = "bot"
                                existing.is_private = not getattr(chat, 'username', None)
                                existing.last_seen = datetime.utcnow()
                                count_updated += 1
                            else:
                                entity = TelegramEntity(
                                    telegram_id=chat.id,
                                    title=getattr(chat, 'first_name', None) or getattr(chat, 'username', None),
                                    username=getattr(chat, 'username', None),
                                    invite_link=invite_link,
                                    entity_type="bot",
                                    is_private=not getattr(chat, 'username', None),
                                    last_seen=datetime.utcnow()
                                )
                                session.add(entity)

                            # Asegurar entrada en FoundLink para que /directorio use también estos enlaces
                            if invite_link:
                                fl_existing = (
                                    session.query(FoundLink)
                                    .filter_by(source_chat_id=chat.id, link=invite_link)
                                    .first()
                                )
                                if not fl_existing:
                                    fl_item = FoundLink(
                                        source_chat_id=chat.id,
                                        message_id=0,
                                        link=invite_link,
                                    )
                                    session.add(fl_item)

                            session.commit()
                            count += 1
                            title = getattr(chat, 'first_name', None) or getattr(chat, 'username', 'Bot sin nombre')
                            print(f"🤖 {count}. {title} - {invite_link or 'Sin enlace'}")

                        except Exception as db_error:
                            session.rollback()
                            error_msg = f"Error guardando bot {getattr(chat, 'username', 'bot')}: {str(db_error)[:100]}"
                            errors.append(error_msg)
                            print(f"❌ {error_msg}")

                        continue

                    # Grupos y canales (tienen title)
                    if not hasattr(chat, 'title'):
                        # Ignorar chats privados normales
                        continue

                    # Intentar obtener el link de invitación
                    invite_link = None
                    try:
                        if hasattr(chat, 'username') and chat.username:
                            invite_link = f"https://t.me/{chat.username}"
                            count_with_link += 1
                        else:
                            # Intentar exportar invite link si tenemos permisos
                            result = await client(ExportChatInviteRequest(chat.id))
                            invite_link = result.link
                            count_with_link += 1
                    except:
                        count_without_link += 1

                    try:
                        # Verificar si ya existe
                        existing = session.query(TelegramEntity).filter_by(telegram_id=chat.id).first()

                        if existing:
                            # Actualizar existente
                            existing.title = getattr(chat, 'title', None)
                            existing.username = getattr(chat, 'username', None)
                            existing.invite_link = invite_link or existing.invite_link
                            existing.entity_type = "channel" if getattr(chat, 'broadcast', False) else "group"
                            existing.is_private = not getattr(chat, 'username', None)
                            existing.last_seen = datetime.utcnow()
                            count_updated += 1
                        else:
                            # Crear nuevo
                            entity = TelegramEntity(
                                telegram_id=chat.id,
                                title=getattr(chat, 'title', None),
                                username=getattr(chat, 'username', None),
                                invite_link=invite_link,
                                entity_type="channel" if getattr(chat, 'broadcast', False) else "group",
                                is_private=not getattr(chat, 'username', None),
                                last_seen=datetime.utcnow()
                            )
                            session.add(entity)

                        # Asegurar entrada en FoundLink para que /directorio use también estos enlaces
                        if invite_link:
                            fl_existing = (
                                session.query(FoundLink)
                                .filter_by(source_chat_id=chat.id, link=invite_link)
                                .first()
                            )
                            if not fl_existing:
                                fl_item = FoundLink(
                                    source_chat_id=chat.id,
                                    message_id=0,
                                    link=invite_link,
                                )
                                session.add(fl_item)

                        session.commit()
                        count += 1
                        title = getattr(chat, 'title', 'Sin título')
                        print(f"✅ {count}. {title} - {invite_link or 'Sin enlace'}")

                    except Exception as db_error:
                        session.rollback()
                        error_msg = f"Error guardando {getattr(chat, 'title', 'grupo')}: {str(db_error)[:100]}"
                        errors.append(error_msg)
                        print(f"❌ {error_msg}")

                except Exception as e:
                    error_msg = f"Error procesando diálogo: {str(e)[:100]}"
                    errors.append(error_msg)
                    print(f"❌ {error_msg}")
            
            result_msg = (
                f"✅ Escaneo completado:\n\n"
                f"📊 Total procesado: {count} entidades\n"
                f"🆕 Nuevos: {count - count_updated}\n"
                f"🔄 Actualizados: {count_updated}\n"
                f"✅ Con enlace: {count_with_link}\n"
                f"⚠️ Sin enlace: {count_without_link}\n"
            )
            
            if errors:
                result_msg += f"\n⚠️ Errores: {len(errors)}\n"
            
            result_msg += "\n💡 Usa el bot de control para ver la lista completa."
            
            await event.respond(result_msg)
        except Exception as e:
            await event.respond(f"❌ Error durante el escaneo: {str(e)[:200]}")
        finally:
            session.close()

    @client.on(events.NewMessage(pattern='/scanchat'))
    async def controlled_scan_handler(event):
        """Escaneo controlado de un chat concreto: /scanchat <chat_id>"""
        try:
            parts = event.raw_text.split(maxsplit=1)
            if len(parts) < 2:
                await event.respond("❌ Uso: /scanchat <chat_id>")
                return

            chat_id_str = parts[1].strip()
            chat_id = int(chat_id_str)

            await event.respond(f"🔍 Escaneando chat {chat_id} (límite {SCAN_LIMIT_PER_RUN} mensajes)...")

            new_links = await scan_chat(client, chat_id, limit=SCAN_LIMIT_PER_RUN)

            await event.respond(
                f"✅ Escaneo completado para {chat_id}\n"
                f"🔗 Nuevos enlaces encontrados: {new_links}"
            )
        except ValueError:
            await event.respond("❌ El chat_id debe ser un número válido")
        except Exception as e:
            await event.respond(f"❌ Error en /scanchat: {str(e)[:200]}")

    async def process_pending_backups():
        """Procesa backups pendientes y crea los canales necesarios"""
        await client.get_me()
        
        while True:
            try:
                session = SessionLocal()
                try:
                    pending = session.query(BackupMapping).filter_by(dest_chat_id=0, enabled=True).all()
                    
                    for mapping in pending:
                        try:
                            entity = session.query(TelegramEntity).filter_by(telegram_id=mapping.source_chat_id).first()
                            if not entity:
                                continue
                            
                            print(f"📦 Creando canal de backup para: {entity.title}")
                            
                            result = await client(CreateChannelRequest(
                                title=f"📦 Backup - {entity.title[:50]}",
                                about=f"Backup automático de multimedia\n🤖 Grupo: {entity.title}\n🆔 ID: {mapping.source_chat_id}",
                                megagroup=False
                            ))
                            
                            dest_channel = result.chats[0]
                            
                            mapping.dest_chat_id = dest_channel.id
                            mapping.dest_chat_title = f"📦 Backup - {entity.title[:50]}"
                            session.commit()
                            
                            print(f"✅ Canal creado: {mapping.dest_chat_title}")
                            
                        except Exception as e:
                            print(f"❌ Error creando canal para {mapping.source_chat_id}: {str(e)[:100]}")
                            session.rollback()
                finally:
                    session.close()
                
                await asyncio.sleep(30)
                
            except Exception as e:
                print(f"❌ Error en process_pending_backups: {str(e)[:100]}")
                await asyncio.sleep(60)

    async def process_historial_requests():
        """Procesa solicitudes pendientes de descarga de historial"""
        from userbot.config import CONTROL_BOT_ID
        
        async def download_historial(source_chat_id, dest_chat_id, title):
            """Descarga el historial de un grupo específico"""
            try:
                print(f"📚 Iniciando descarga de historial: {title}")
                
                try:
                    await client.send_message(
                        CONTROL_BOT_ID,
                        f"📚 Descargando historial de: {title}\n\n⏳ Este proceso puede tomar varios minutos..."
                    )
                except:
                    pass
                
                count = 0
                errors = 0
                last_notification = 0
                
                # Obtener la entidad del canal primero
                dest_entity = None
                
                # Intentar con get_entity primero (más rápido)
                try:
                    dest_entity = await client.get_entity(dest_chat_id)
                    print(f"✅ Canal encontrado con get_entity: {dest_chat_id}")
                except Exception as e:
                    print(f"⚠️ get_entity falló, buscando en diálogos: {str(e)[:50]}")
                    # Si falla, buscar en diálogos
                    async for dialog in client.iter_dialogs():
                        if dialog.id == dest_chat_id:
                            dest_entity = dialog.entity
                            break
                
                if not dest_entity:
                    print(f"❌ No se encontró el canal de backup para {title}")
                    return
                
                async for message in client.iter_messages(source_chat_id, limit=None, reverse=True):
                    if message.media:
                        try:
                            # Intentar reenviar directamente primero
                            try:
                                await client.send_message(dest_entity, message)
                            except Exception as forward_error:
                                # Si falla (protección de reenvío), descargar y subir
                                if "protected chat" in str(forward_error).lower():
                                    # Descargar archivo a bytes
                                    file_bytes = await client.download_media(message, file=bytes)
                                    
                                    # Obtener atributos del archivo
                                    attributes = []
                                    if message.document:
                                        attributes = message.document.attributes
                                    elif message.photo:
                                        # Para fotos, no hay atributos especiales
                                        pass
                                    elif message.video:
                                        attributes = message.video.attributes
                                    
                                    # Subir al canal de backup preservando atributos
                                    await client.send_file(
                                        dest_entity,
                                        file_bytes,
                                        caption=message.message if message.message else None,
                                        attributes=attributes if attributes else None,
                                        force_document=message.document is not None
                                    )
                                else:
                                    raise forward_error
                            
                            count += 1
                            increment_message_count(source_chat_id)
                            
                            if count % 50 == 0:
                                print(f"📊 {title}: {count} archivos")
                                
                                if count - last_notification >= 100:
                                    try:
                                        await client.send_message(
                                            CONTROL_BOT_ID,
                                            f"📊 Progreso: {count} archivos descargados de {title}"
                                        )
                                        last_notification = count
                                    except:
                                        pass
                            
                            if count % 20 == 0:
                                await asyncio.sleep(1)
                                
                        except Exception as e:
                            errors += 1
                            if errors <= 3:
                                print(f"⚠️ Error en {title}: {str(e)[:100]}")
                
                print(f"✅ Historial completado: {title} - {count} archivos (errores: {errors})")
                
                try:
                    await client.send_message(
                        CONTROL_BOT_ID,
                        f"✅ Historial completado: {title}\n\n"
                        f"📦 Total descargado: {count} archivos\n"
                        f"⚠️ Errores: {errors}\n\n"
                        f"🔄 El backup automático sigue activo para nuevos archivos."
                    )
                except:
                    pass
                    
            except Exception as e:
                print(f"❌ Error procesando historial de {title}: {str(e)[:100]}")
        
        while True:
            try:
                await asyncio.sleep(10)
                
                session = SessionLocal()
                try:
                    pending = session.query(BackupMapping).filter_by(
                        historial_pending=True,
                        enabled=True
                    ).all()
                    
                    tasks_to_create = []
                    
                    for mapping in pending:
                        if mapping.dest_chat_id == 0:
                            continue
                        
                        entity = session.query(TelegramEntity).filter_by(
                            telegram_id=mapping.source_chat_id
                        ).first()
                        
                        if not entity:
                            continue
                        
                        source_id = mapping.source_chat_id
                        dest_id = mapping.dest_chat_id
                        title = entity.title
                        
                        mapping.historial_pending = False
                        session.commit()
                        
                        tasks_to_create.append((source_id, dest_id, title))
                    
                    session.close()
                    
                    for source_id, dest_id, title in tasks_to_create:
                        client.loop.create_task(download_historial(source_id, dest_id, title))
                        await asyncio.sleep(2)
                        
                except Exception as db_error:
                    print(f"❌ Error de base de datos: {str(db_error)[:100]}")
                finally:
                    try:
                        session.close()
                    except:
                        pass
                    
            except Exception as e:
                print(f"❌ Error en process_historial_requests: {str(e)[:100]}")
                await asyncio.sleep(30)

    async def process_pending_joins():
        """Procesa de forma controlada los enlaces pendientes en found_links."""
        while True:
            try:
                session, links = get_pending_links(limit=JOIN_LIMIT_PER_RUN)
            except Exception as e:
                print(f"❌ Error obteniendo enlaces pendientes: {str(e)[:100]}")
                await asyncio.sleep(30)
                continue

            try:
                if not links:
                    session.close()
                    await asyncio.sleep(30)
                    continue

                processed = 0
                for link_obj in links:
                    # Saltar enlaces de carpetas (addlist)
                    if "addlist" in (link_obj.link or "").lower():
                        mark_link_result(session, link_obj, joined=False, failed=True)
                        continue

                    try:
                        await safe_delay(JOIN_DELAY_SECONDS)
                        print(f"🔗 Intentando unirse a: {link_obj.link}")
                        result = await join_from_link(client, link_obj.link)

                        # Intentar obtener info del chat al que nos unimos
                        joined_chat = None
                        try:
                            if hasattr(result, 'chats') and result.chats:
                                joined_chat = result.chats[0]
                            elif hasattr(result, 'user'):
                                joined_chat = result.user
                        except Exception:
                            joined_chat = None

                        if joined_chat is not None and hasattr(joined_chat, 'id'):
                            title = getattr(joined_chat, 'title', None) or getattr(joined_chat, 'first_name', None)
                            username = getattr(joined_chat, 'username', None)
                            ensure_entity_for_chat(joined_chat.id, title, username)

                        mark_link_result(session, link_obj, joined=True, failed=False)
                        processed += 1
                    except Exception as e:
                        print(f"❌ Error al unirse desde enlace {link_obj.link}: {str(e)[:100]}")
                        mark_link_result(session, link_obj, joined=False, failed=True)

                if processed:
                    session.commit()
                else:
                    session.close()

            except Exception as e:
                print(f"❌ Error procesando enlaces pendientes: {str(e)[:100]}")
                try:
                    session.rollback()
                    session.close()
                except Exception:
                    pass

            await asyncio.sleep(10)

    async def start_background_tasks():
        """Inicia todas las tareas en segundo plano"""
        await asyncio.sleep(5)
        client.loop.create_task(process_pending_backups())
        client.loop.create_task(process_historial_requests())
        client.loop.create_task(process_pending_joins())
    
    client.loop.create_task(start_background_tasks())

    @client.on(events.NewMessage())
    async def backup_media_handler(event):
        """Escucha todos los mensajes y respalda multimedia automáticamente"""
        
        if not event.is_group and not event.is_channel:
            return
        if event.message.message and event.message.message.startswith('/'):
            return
        
        if not event.message.media:
            return
        
        source_chat_id = event.chat_id
        
        dest_chat_id = get_dest_channel(source_chat_id)
        if not dest_chat_id:
            return
        
        if dest_chat_id == 0:
            print(f"⚠️ Canal de backup aún no creado para chat {source_chat_id}")
            return
        
        try:
            chat = await event.get_chat()
            chat_title = getattr(chat, 'title', 'Grupo sin nombre')
            
            # Obtener el canal de destino
            dest_entity = None
            
            # Intentar con get_entity primero (más rápido)
            try:
                dest_entity = await client.get_entity(dest_chat_id)
            except:
                # Si falla, buscar en diálogos
                async for dialog in client.iter_dialogs():
                    if dialog.id == dest_chat_id:
                        dest_entity = dialog.entity
                        break
            
            if not dest_entity:
                print(f"⚠️ No se encontró el canal de backup para {chat_title}")
                return
            
            # Intentar reenviar directamente primero
            try:
                await client.send_message(dest_entity, event.message)
            except Exception as forward_error:
                # Si falla (protección de reenvío), descargar y subir
                if "protected chat" in str(forward_error).lower():
                    message = event.message
                    # Descargar archivo a bytes
                    file_bytes = await client.download_media(message, file=bytes)
                    
                    # Obtener atributos del archivo
                    attributes = []
                    if message.document:
                        attributes = message.document.attributes
                    elif message.photo:
                        # Para fotos, no hay atributos especiales
                        pass
                    elif message.video:
                        attributes = message.video.attributes
                    
                    # Subir al canal de backup preservando atributos
                    await client.send_file(
                        dest_entity,
                        file_bytes,
                        caption=message.message if message.message else None,
                        attributes=attributes if attributes else None,
                        force_document=message.document is not None
                    )
                else:
                    raise forward_error
            
            increment_message_count(source_chat_id)
            
            print(f"💾 Backup: {chat_title} → archivo guardado")
            
        except Exception as e:
            print(f"❌ Error en backup automático: {str(e)[:100]}")
    
    print("✅ Handlers del userbot registrados (incluyendo backup automático)")

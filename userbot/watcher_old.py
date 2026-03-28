from telethon import events
from telethon.tl.functions.messages import ExportChatInviteRequest
from telethon.tl.functions.channels import CreateChannelRequest
from telethon.errors import ChatAdminRequiredError, ChatNotModifiedError
from database.db import SessionLocal
from database.models import TelegramEntity, BackupMapping
from datetime import datetime
import asyncio
from userbot.backup_manager import (
    get_dest_channel,
    increment_message_count
)

# Cache global de entidades de canales de backup
backup_channels_cache = {}

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
                    
                    # Solo grupos y canales
                    if not hasattr(chat, 'title'):
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
                            existing.invite_link = invite_link or existing.invite_link  # Mantener el anterior si no hay nuevo
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

    async def process_pending_backups():
        """Procesa backups pendientes y crea los canales necesarios"""
        # Esperar a que el cliente esté conectado
        await client.get_me()
        
        while True:
            try:
                session = SessionLocal()
                try:
                    # Buscar mapeos pendientes (dest_chat_id == 0)
                    pending = session.query(BackupMapping).filter_by(dest_chat_id=0, enabled=True).all()
                    
                    for mapping in pending:
                        try:
                            # Obtener info del grupo origen
                            entity = session.query(TelegramEntity).filter_by(telegram_id=mapping.source_chat_id).first()
                            if not entity:
                                continue
                            
                            print(f"📦 Creando canal de backup para: {entity.title}")
                            
                            # Crear canal privado
                            result = await client(CreateChannelRequest(
                                title=f"📦 Backup - {entity.title[:50]}",
                                about=f"Backup automático de multimedia\n🤖 Grupo: {entity.title}\n🆔 ID: {mapping.source_chat_id}",
                                megagroup=False
                            ))
                            
                            dest_channel = result.chats[0]
                            
                            # Guardar en cache
                            backup_channels_cache[dest_channel.id] = dest_channel
                            
                            # Actualizar el mapeo
                            mapping.dest_chat_id = dest_channel.id
                            mapping.dest_chat_title = f"📦 Backup - {entity.title[:50]}"
                            session.commit()
                            
                            print(f"✅ Canal creado: {mapping.dest_chat_title}")
                            
                        except Exception as e:
                            print(f"❌ Error creando canal para {mapping.source_chat_id}: {str(e)[:100]}")
                            session.rollback()
                finally:
                    session.close()
                
                # Revisar cada 30 segundos
                await asyncio.sleep(30)
                
            except Exception as e:
                print(f"❌ Error en process_pending_backups: {str(e)[:100]}")
                await asyncio.sleep(60)

    async def process_historial_requests():
        """Procesa solicitudes pendientes de descarga de historial"""
        # Obtener el ID del bot de control desde variables de entorno
        from userbot.config import CONTROL_BOT_ID
        
        async def download_historial(source_chat_id, dest_chat_id, title):
            """Descarga el historial de un grupo específico"""
            try:
                print(f"📚 Iniciando descarga de historial: {title}")
                
                # Notificar inicio al usuario
                try:
                    await client.send_message(
                        CONTROL_BOT_ID,
                        f"📚 Descargando historial de: {title}\n\n"
                        f"⏳ Este proceso puede tomar varios minutos..."
                    )
                except:
                    pass
                
                # Procesar historial
                count = 0
                errors = 0
                last_notification = 0
                
                # Buscar el canal de destino (primero en cache, luego en diálogos)
                dest_entity = backup_channels_cache.get(dest_chat_id)
                
                if not dest_entity:
                    try:
                        dest_entity = await client.get_entity(dest_chat_id)
                        backup_channels_cache[dest_chat_id] = dest_entity
                    except:
                        # Si falla, buscar en los diálogos por ID
                        print(f"🔍 Buscando canal de backup en diálogos...")
                        async for dialog in client.iter_dialogs():
                            if dialog.id == dest_chat_id:
                                dest_entity = dialog.entity
                                backup_channels_cache[dest_chat_id] = dest_entity
                                print(f"✅ Canal encontrado: {dialog.name}")
                                break
                
                if not dest_entity:
                    print(f"❌ No se encontró el canal de backup para {title}")
                    return
                
                async for message in client.iter_messages(
                    source_chat_id,
                    limit=None,
                    reverse=True
                ):
                    if message.media:
                        try:
                            await client.send_message(
                                dest_entity,
                                message
                            )
                            count += 1
                            increment_message_count(source_chat_id)
                            
                            # Notificar progreso cada 50 archivos
                            if count % 50 == 0:
                                print(f"📊 {title}: {count} archivos")
                                
                                # Notificar al usuario cada 100 archivos
                                if count - last_notification >= 100:
                                    try:
                                        await client.send_message(
                                            CONTROL_BOT_ID,
                                            f"📊 Progreso: {count} archivos descargados de {title}"
                                        )
                                        last_notification = count
                                    except:
                                        pass
                            
                            # Pequeño delay para evitar flood
                            if count % 20 == 0:
                                await asyncio.sleep(1)
                                
                        except Exception as e:
                            errors += 1
                            if errors <= 3:
                                print(f"⚠️ Error en {title}: {str(e)[:100]}")
                
                print(f"✅ Historial completado: {title} - {count} archivos (errores: {errors})")
                
                # Notificar finalización al usuario
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
        
        # Loop principal
        while True:
            try:
                await asyncio.sleep(10)  # Revisar cada 10 segundos
                
                session = SessionLocal()
                try:
                    # Buscar solicitudes pendientes
                    pending = session.query(BackupMapping).filter_by(
                        historial_pending=True,
                        enabled=True
                    ).all()
                    
                    # Crear lista de tareas a procesar
                    tasks_to_create = []
                    
                    for mapping in pending:
                        if mapping.dest_chat_id == 0:
                            continue  # Canal no creado aún
                        
                        # Obtener info del grupo
                        entity = session.query(TelegramEntity).filter_by(
                            telegram_id=mapping.source_chat_id
                        ).first()
                        
                        if not entity:
                            continue
                        
                        # Guardar datos necesarios
                        source_id = mapping.source_chat_id
                        dest_id = mapping.dest_chat_id
                        title = entity.title
                        
                        # Marcar como procesando
                        mapping.historial_pending = False
                        session.commit()
                        
                        # Agregar a la lista de tareas
                        tasks_to_create.append((source_id, dest_id, title))
                    
                    session.close()
                    
                    # Crear tareas en paralelo para cada historial
                    for source_id, dest_id, title in tasks_to_create:
                        client.loop.create_task(download_historial(source_id, dest_id, title))
                        await asyncio.sleep(2)  # Delay entre tareas para evitar conflictos
                        
                except Exception as db_error:
                    print(f"❌ Error de base de datos: {str(db_error)[:100]}")
                finally:
                    try:
                        session.close()
                    except:
                        pass
                    
            except Exception as e:
                print(f"❌ Error en process_historial_requests: {str(e)[:100]}")
                await asyncio.sleep(30)  # Esperar más si hay error

    # Iniciar procesadores en segundo plano
    async def start_background_tasks():
        """Inicia todas las tareas en segundo plano"""
        await asyncio.sleep(5)  # Esperar a que el cliente esté completamente conectado
        
        # Cargar canales de backup existentes en el cache
        print("🔄 Cargando canales de backup existentes...")
        async for dialog in client.iter_dialogs():
            if dialog.name and dialog.name.startswith("📦 Backup"):
                backup_channels_cache[dialog.id] = dialog.entity
                print(f"✅ Canal cargado: {dialog.name}")
        
        print(f"📦 {len(backup_channels_cache)} canales en cache")
        
        client.loop.create_task(process_pending_backups())
        client.loop.create_task(process_historial_requests())
    
    client.loop.create_task(start_background_tasks())

    @client.on(events.NewMessage())
    async def backup_media_handler(event):
        """Escucha todos los mensajes y respalda multimedia automáticamente"""
        
        # Ignorar mensajes privados y comandos
        if not event.is_group and not event.is_channel:
            return
        if event.message.message and event.message.message.startswith('/'):
            return
        
        # Solo procesar si tiene multimedia
        if not event.message.media:
            return
        
        source_chat_id = event.chat_id
        
        # Verificar si tiene backup activo
        dest_chat_id = get_dest_channel(source_chat_id)
        if not dest_chat_id:
            return
        
        # Saltar si el destino es temporal (0)
        if dest_chat_id == 0:
            return
        
        try:
            # Obtener info del chat origen
            chat = await event.get_chat()
            chat_title = getattr(chat, 'title', 'Grupo sin nombre')
            
            # Buscar el canal de destino (primero en cache)
            dest_entity = backup_channels_cache.get(dest_chat_id)
            
            if not dest_entity:
                try:
                    dest_entity = await client.get_entity(dest_chat_id)
                    backup_channels_cache[dest_chat_id] = dest_entity
                except:
                    # Si falla, buscar en los diálogos
                    async for dialog in client.iter_dialogs():
                        if dialog.id == dest_chat_id:
                            dest_entity = dialog.entity
                            backup_channels_cache[dest_chat_id] = dest_entity
                            break
            
            if not dest_entity:
                print(f"⚠️ No se encontró el canal de backup para {chat_title}")
                return
            
            # Reenviar el mensaje completo al canal de backup
            await client.send_message(
                dest_entity,
                event.message
            )
            
            # Incrementar contador
            increment_message_count(source_chat_id)
            
            print(f"💾 Backup: {chat_title} → archivo guardado")
            
        except Exception as e:
            # No mostrar errores al usuario, solo log
            print(f"❌ Error en backup automático: {str(e)[:100]}")
    
    print("✅ Handlers del userbot registrados (incluyendo backup automático)")




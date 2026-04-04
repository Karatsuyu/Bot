from aiogram import types, F
from aiogram.filters import Command
from database.db import SessionLocal
from database.models import TelegramEntity, BackupMapping
from sqlalchemy import func
from feature.scanner.service import scan_chat, get_pending_links, mark_link_result
from feature.scanner.models import FoundLink, LinkRule
from userbot.main import get_client as get_userbot_client
from bot.keyboards.pagination import directory_keyboard

def _get_args(message: types.Message) -> str:
    """Helper para obtener los argumentos de un comando en Aiogram v3."""
    if not message.text:
        return ""
    parts = message.text.split(maxsplit=1)
    return parts[1] if len(parts) > 1 else ""

async def cmd_start(message: types.Message):
    """Comando /start - Mensaje de bienvenida"""
    welcome_text = (
        "🤖 Bot de Gestión de Telegram\n\n"
        "📋 Comandos de consulta:\n"
        "• /listar - Lista todas las entidades guardadas\n"
        "• /sinlink - Muestra entidades sin enlace\n"
        "• /categorias - Muestra entidades por categoría\n"
        "• /stats - Estadísticas del sistema\n"
        "• /scan - Instrucciones para escanear grupos (userbot)\n"
        "• /scanchat <ID> - Escanear enlaces de un chat concreto\n"
        "• /links_chat <ID> - Ver enlaces encontrados de un chat\n"
        "• /links_estado [estado] - Ver enlaces por estado (pending/joined/failed)\n"
        "• /links_resumen [ID] - Resumen global o por chat\n\n"
        "🔧 Comandos de gestión:\n"
        "• /addlink - Agregar enlace a una entidad\n"
        "• /unir_guardados [cantidad] - Unirse a enlaces ya guardados (anti-ban)\n"
        "• /escanear_y_unir <ID> - Escanear chat y unir automáticamente a enlaces\n\n"
        "📦 Comandos de backup:\n"
        "• /backup_lista - Ver grupos disponibles con IDs\n"
        "• /backup_activar [ID] - Activar backup automático\n"
        "• /backup_desactivar [ID] - Desactivar backup\n"
        "• /backup_historial [ID] - Descargar archivos antiguos\n"
        "• /backup_estado - Ver estado de todos los backups\n"
        "• /backup_info - Ayuda sobre backups\n\n"
        "⚙️ Reglas de enlaces:\n"
        "• /linkrule_add <pattern> <whitelist|blacklist> - Añadir/actualizar regla\n"
        "• /linkrule_list - Ver reglas activas\n"
        "• /linkrule_toggle <id> - Activar/desactivar regla\n\n"
        "• /help - Muestra esta ayuda\n\n"
        "💡 Tip: Todos los comandos usan IDs, no necesitas escribir en grupos"
    )
    await message.answer(welcome_text)

async def cmd_help(message: types.Message):
    """Comando /help - Ayuda"""
    await cmd_start(message)

async def cmd_listar(message: types.Message):
    """Comando /listar - Lista todas las entidades"""
    session = SessionLocal()
    
    try:
        entities = session.query(TelegramEntity).order_by(TelegramEntity.title).all()
        
        if not entities:
            await message.answer("📭 No hay entidades registradas aún.\n\n💡 Usa /scan para escanear todos tus grupos actuales.")
            return
        
        text = "📋 Entidades Registradas:\n\n"
        
        for e in entities:
            emoji = "📢" if e.entity_type == "channel" else "👥"
            privacy = "🔒" if e.is_private else "🔓"
            username_text = f"@{e.username}" if e.username else "Sin username"
            # Escapar caracteres especiales de Markdown
            title = (e.title or 'Sin título').replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`', '\\`')
            
            text += f"{emoji} {privacy} {title}\n"
            text += f"   ├ Tipo: {e.entity_type}\n"
            text += f"   ├ Username: {username_text}\n"
            text += f"   ├ Categoría: {e.category}\n"
            text += f"   ├ ID: {e.telegram_id}\n"
            if e.invite_link:
                text += f"   └ Link: {e.invite_link}\n\n"
            else:
                text += f"   └ Link: Sin enlace\n\n"
        
        # Dividir mensaje si es muy largo
        if len(text) > 4000:
            parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
            for part in parts:
                await message.answer(part)
        else:
            await message.answer(text)
    
    except Exception as e:
        await message.answer(f"❌ Error al listar entidades: {str(e)}")
    finally:
        session.close()

async def cmd_categorias(message: types.Message):
    """Comando /categorias - Lista entidades por categoría"""
    session = SessionLocal()
    
    try:
        result = session.query(
            TelegramEntity.category,
            func.count(TelegramEntity.id)
        ).group_by(TelegramEntity.category).all()
        
        if not result:
            await message.answer("📭 No hay entidades registradas aún.")
            return
        
        text = "📊 Entidades por Categoría:\n\n"
        
        for category, count in result:
            text += f"📁 {category}: {count} entidades\n"
        
        await message.answer(text)
    
    except Exception as e:
        await message.answer(f"❌ Error al listar categorías: {str(e)}")
    finally:
        session.close()

async def cmd_stats(message: types.Message):
    """Comando /stats - Estadísticas del sistema"""
    session = SessionLocal()
    
    try:
        total = session.query(TelegramEntity).count()
        grupos = session.query(TelegramEntity).filter_by(entity_type="group").count()
        canales = session.query(TelegramEntity).filter_by(entity_type="channel").count()
        privados = session.query(TelegramEntity).filter_by(is_private=True).count()
        publicos = session.query(TelegramEntity).filter_by(is_private=False).count()
        
        con_enlace = session.query(TelegramEntity).filter(TelegramEntity.invite_link.isnot(None)).count()
        sin_enlace = total - con_enlace
        
        text = (
            "📊 Estadísticas del Sistema\n\n"
            "📈 Totales:\n"
            f"• Total de entidades: {total}\n"
            f"• Grupos: {grupos} 👥\n"
            f"• Canales: {canales} 📢\n\n"
            "🔒 Privacidad:\n"
            f"• Privados: {privados} 🔒\n"
            f"• Públicos: {publicos} 🔓\n\n"
            "🔗 Enlaces:\n"
            f"• Con enlace: {con_enlace} ✅\n"
            f"• Sin enlace: {sin_enlace} ⚠️"
        )
        
        await message.answer(text)
    
    except Exception as e:
        await message.answer(f"❌ Error al obtener estadísticas: {str(e)}")
    finally:
        session.close()

async def cmd_addlink(message: types.Message):
    """Comando /addlink - Agregar enlace a una entidad"""
    try:
        parts = message.text.split(maxsplit=2)
        
        if len(parts) < 3:
            await message.answer(
                "❌ Formato incorrecto.\n\n"
                "Uso:\n"
                "/addlink ID_o_nombre https://t.me/+abc123\n\n"
                "Ejemplos:\n"
                "• /addlink -1001234567890 https://t.me/+abc123\n"
                "• /addlink MiGrupo https://t.me/+abc123\n\n"
                "💡 Usa /listar para ver los IDs de tus grupos."
            )
            return
        
        identifier = parts[1]
        link = parts[2]
        
        if 't.me' not in link:
            await message.answer("❌ El enlace debe ser de Telegram (t.me)")
            return
        
        session = SessionLocal()
        
        entity = None
        if identifier.lstrip('-').isdigit():
            entity = session.query(TelegramEntity).filter_by(telegram_id=int(identifier)).first()
        else:
            entity = session.query(TelegramEntity).filter(TelegramEntity.title.ilike(f"%{identifier}%")).first()
        
        if not entity:
            await message.answer(f"❌ No se encontró ninguna entidad con: {identifier}")
            session.close()
            return
        
        entity.invite_link = link
        session.commit()
        
        await message.answer(f"✅ Enlace actualizado para:\n{entity.title}\n🔗 {link}")
        session.close()
        
    except Exception as e:
        await message.answer(f"❌ Error al agregar enlace: {str(e)}")

async def cmd_sinlink(message: types.Message):
    """Comando /sinlink - Listar entidades sin enlace"""
    session = SessionLocal()
    
    try:
        entities = session.query(TelegramEntity).filter(TelegramEntity.invite_link.is_(None)).order_by(TelegramEntity.title).all()
        
        if not entities:
            await message.answer("✅ Todas las entidades tienen enlace guardado.")
            return
        
        text = "⚠️ Entidades sin enlace:\n\n"
        
        for e in entities:
            emoji = "📢" if e.entity_type == "channel" else "👥"
            # Escapar caracteres especiales
            title = (e.title or 'Sin título').replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`', '\\`')
            text += f"{emoji} {title}\n"
            text += f"   └ ID: {e.telegram_id}\n\n"
        
        text += "\n💡 Usa /addlink ID enlace para agregar el enlace."
        
        if len(text) > 4000:
            parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
            for part in parts:
                await message.answer(part)
        else:
            await message.answer(text)
    
    except Exception as e:
        await message.answer(f"❌ Error al buscar entidades sin enlace: {str(e)}")
    finally:
        session.close()

async def cmd_scan(message: types.Message):
    """Comando /scan - Escanear grupos del usuario desde el bot"""
    await message.answer(
        "⚠️ Este comando sigue siendo el escaneo global con /scan desde tu cuenta personal.\n\n"
        "📌 Nuevo escaneo controlado disponible:\n"
        "• Usa /scanchat <chat_id> para escanear un chat concreto.\n"
        "• Usa /joinlinks para procesar enlaces pendientes de forma controlada."
    )


async def cmd_scanchat(message: types.Message):
    """Comando /scanchat <chat_id> - Escanea un chat concreto usando el userbot"""
    args = _get_args(message)
    if not args:
        await message.answer("❌ Uso: /scanchat <chat_id>")
        return

    try:
        chat_id = int(args.strip())
    except ValueError:
        await message.answer("❌ El chat_id debe ser numérico")
        return

    client = get_userbot_client()
    if client is None or not client.is_connected():
        await message.answer("❌ El userbot no está conectado. Asegúrate de que run_userbot.py esté en ejecución.")
        return

    from userbot.config import SCAN_LIMIT_PER_RUN

    await message.answer(f"🔍 Escaneando chat {chat_id} (límite {SCAN_LIMIT_PER_RUN} mensajes)...")

    try:
        new_links = await scan_chat(client, chat_id, limit=SCAN_LIMIT_PER_RUN)
        await message.answer(
            f"✅ Escaneo completado para {chat_id}\n"
            f"🔗 Nuevos enlaces encontrados: {new_links}"
        )
    except Exception as e:
        await message.answer(f"❌ Error en /scanchat: {str(e)[:200]}")


async def cmd_joinlinks(message: types.Message):
    """Comando /joinlinks - Procesa enlaces pendientes de found_links"""
    client = get_userbot_client()
    if client is None or not client.is_connected():
        await message.answer("❌ El userbot no está conectado. Asegúrate de que run_userbot.py esté en ejecución.")
        return

    from userbot.config import JOIN_LIMIT_PER_RUN
    session, links = get_pending_links(limit=JOIN_LIMIT_PER_RUN)

    if not links:
        session.close()
        await message.answer("✅ No hay enlaces pendientes por procesar.")
        return

    from feature.scanner.joiner import join_from_link
    from feature.scanner.limiter import safe_delay
    from feature.scanner.service import ensure_entity_for_chat

    processed = 0
    for link_obj in links:
        # Saltar enlaces de carpetas (addlist)
        if "addlist" in (link_obj.link or "").lower():
            mark_link_result(session, link_obj, joined=False, failed=True)
            continue

        try:
            await safe_delay()
            await message.answer(f"🔗 Intentando unirse a: {link_obj.link}")
            result = await join_from_link(client, link_obj.link)

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
            mark_link_result(session, link_obj, joined=False, failed=True)
            await message.answer(f"❌ Error al procesar {link_obj.link}: {str(e)[:100]}")

    if processed:
        session.commit()
    else:
        session.close()

    await message.answer(f"✅ Links procesados: {processed}")


async def cmd_unir_guardados(message: types.Message):
    """Comando /unir_guardados [cantidad] - Se une a enlaces ya guardados en BD con rate limiting anti-ban"""
    client = get_userbot_client()
    if client is None or not client.is_connected():
        await message.answer("❌ El userbot no está conectado. Asegúrate de que run_userbot.py esté en ejecución.")
        return

    # Obtener cantidad de enlaces a procesar (default 20 para evitar bans)
    args = _get_args(message).strip()
    limit = 20  # Default seguro para evitar bans
    
    if args and args.isdigit():
        limit = int(args)
        if limit > 50:
            limit = 50  # Límite máximo por seguridad
            await message.answer("⚠️ Límite máximo ajustado a 50 para evitar bans.")

    from userbot.config import JOIN_DELAY_SECONDS
    from feature.scanner.joiner import join_from_link
    from feature.scanner.limiter import safe_delay
    from feature.scanner.service import ensure_entity_for_chat

    session, links = get_pending_links(limit=limit)

    if not links:
        session.close()
        await message.answer("✅ No hay enlaces pendientes por procesar.")
        return

    total_links = len(links)
    await message.answer(
        f"🔗 Iniciando unión a {total_links} enlaces guardados...\n\n"
        f"⏱️ Tiempo estimado: ~{total_links * JOIN_DELAY_SECONDS // 60} minutos\n"
        f"⚠️ Este proceso es lento para evitar bans de Telegram."
    )

    processed = 0
    success = 0
    failed = 0

    for link_obj in links:
        # Saltar enlaces de carpetas (addlist)
        if "addlist" in (link_obj.link or "").lower():
            mark_link_result(session, link_obj, joined=False, failed=True)
            failed += 1
            processed += 1
            continue

        try:
            await safe_delay(JOIN_DELAY_SECONDS)
            print(f"🔗 Uniéndose a: {link_obj.link}")
            result = await join_from_link(client, link_obj.link)

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
            success += 1
            processed += 1
        except Exception as e:
            mark_link_result(session, link_obj, joined=False, failed=True)
            failed += 1
            processed += 1
            print(f"❌ Error al unirse desde {link_obj.link}: {str(e)[:100]}")

    if processed:
        session.commit()
    else:
        session.close()

    await message.answer(
        f"✅ Unión completada:\n\n"
        f"📊 Total procesados: {processed}\n"
        f"✅ Exitosos: {success}\n"
        f"❌ Fallidos: {failed}"
    )


async def cmd_escanear_y_unir(message: types.Message):
    """Comando /escanear_y_unir <ID> - Escanea un chat, guarda enlaces y se une automáticamente"""
    args = _get_args(message)
    if not args:
        await message.answer("❌ Uso: /escanear_y_unir <chat_id>")
        return

    try:
        chat_id = int(args.strip())
    except ValueError:
        await message.answer("❌ El chat_id debe ser numérico")
        return

    client = get_userbot_client()
    if client is None or not client.is_connected():
        await message.answer("❌ El userbot no está conectado. Asegúrate de que run_userbot.py esté en ejecución.")
        return

    from userbot.config import SCAN_LIMIT_PER_RUN, JOIN_DELAY_SECONDS
    from feature.scanner.joiner import join_from_link
    from feature.scanner.limiter import safe_delay
    from feature.scanner.service import ensure_entity_for_chat

    # Paso 1: Escanear el chat
    await message.answer(f"🔍 Escaneando chat {chat_id} (límite {SCAN_LIMIT_PER_RUN} mensajes)...")

    try:
        new_links_count = await scan_chat(client, chat_id, limit=SCAN_LIMIT_PER_RUN)
        await message.answer(f"📊 Enlaces encontrados: {new_links_count}")

        if new_links_count == 0:
            await message.answer("ℹ️ No se encontraron enlaces nuevos en este chat.")
            return

        # Paso 2: Obtener los enlaces recién guardados (los últimos)
        session = SessionLocal()
        try:
            recent_links = (
                session.query(FoundLink)
                .filter_by(processed=False, source_chat_id=chat_id)
                .order_by(FoundLink.created_at.desc())
                .limit(new_links_count)
                .all()
            )
        finally:
            session.close()

        if not recent_links:
            await message.answer("ℹ️ No hay enlaces pendientes para unir.")
            return

        # Paso 3: Unirse automáticamente a los enlaces encontrados
        await message.answer(
            f"🔗 Uniéndose automáticamente a {len(recent_links)} enlaces encontrados...\n\n"
            f"⏱️ Esto tomará ~{len(recent_links) * JOIN_DELAY_SECONDS // 60} minutos."
        )

        processed = 0
        success = 0
        failed = 0

        for link_obj in recent_links:
            # Saltar enlaces de carpetas (addlist)
            if "addlist" in (link_obj.link or "").lower():
                mark_link_result(session, link_obj, joined=False, failed=True)
                failed += 1
                processed += 1
                continue

            try:
                await safe_delay(JOIN_DELAY_SECONDS)
                print(f"🔗 Uniéndose a: {link_obj.link}")
                result = await join_from_link(client, link_obj.link)

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
                success += 1
                processed += 1
            except Exception as e:
                mark_link_result(session, link_obj, joined=False, failed=True)
                failed += 1
                processed += 1
                print(f"❌ Error al unirse desde {link_obj.link}: {str(e)[:100]}")

        if processed:
            session.commit()
        else:
            session.close()

        await message.answer(
            f"✅ Escaneo y unión completada:\n\n"
            f"📊 Total procesados: {processed}\n"
            f"✅ Exitosos: {success}\n"
            f"❌ Fallidos: {failed}"
        )

    except Exception as e:
        await message.answer(f"❌ Error en /escanear_y_unir: {str(e)[:200]}")


async def cmd_backup_lista(message: types.Message):
    """Comando /backup_lista - Lista grupos disponibles para backup"""
    session = SessionLocal()
    
    try:
        entities = session.query(TelegramEntity).filter(
            TelegramEntity.entity_type.in_(['group', 'channel'])
        ).order_by(TelegramEntity.title).all()
        
        if not entities:
            await message.answer("📭 No hay grupos/canales registrados.\n\n💡 Usa /scan primero para escanear tus grupos.")
            return
        
        text = "📋 Grupos y Canales Disponibles:\n\n"
        
        for e in entities:
            # Verificar si tiene backup activo
            backup = session.query(BackupMapping).filter_by(source_chat_id=e.telegram_id).first()
            
            emoji = "📢" if e.entity_type == "channel" else "👥"
            status = ""
            if backup:
                status = " ✅" if backup.enabled else " ⏸️"
            
            title = (e.title or 'Sin título')[:40]
            text += f"{emoji}{status} {title}\n"
            text += f"   └ ID: {e.telegram_id}\n\n"
        
        text += "\n💡 Usa: /backup_activar [ID] para activar el backup"
        
        if len(text) > 4000:
            parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
            for part in parts:
                await message.answer(part)
        else:
            await message.answer(text)
    
    except Exception as e:
        await message.answer(f"❌ Error: {str(e)[:200]}")
    finally:
        session.close()

async def cmd_backup_activar(message: types.Message):
    """Comando /backup_activar [ID] - Activa backup para un grupo"""
    try:
        # Extraer el ID del comando
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer(
                "❌ Uso incorrecto\n\n"
                "✅ Uso correcto: /backup_activar [ID]\n\n"
                "Ejemplo: /backup_activar -1001234567890\n\n"
                "💡 Usa /backup_lista para ver los IDs disponibles"
            )
            return
        
        chat_id = int(parts[1])
        
        # Verificar que el grupo existe en la base de datos
        session = SessionLocal()
        try:
            entity = session.query(TelegramEntity).filter_by(telegram_id=chat_id).first()
            if not entity:
                await message.answer(
                    "❌ No se encontró ese grupo/canal.\n\n"
                    "💡 Primero usa /scan en tu cuenta de Telegram\n"
                    "💡 Luego usa /backup_lista para ver los IDs"
                )
                return
            
            # Verificar si ya tiene backup (modo canal)
            existing = session.query(BackupMapping).filter_by(
                source_chat_id=chat_id
            ).filter(
                (BackupMapping.storage_mode == 'channel') | (BackupMapping.storage_mode.is_(None))
            ).first()
            if existing and existing.enabled:
                await message.answer(
                    f"⚠️ Este grupo ya tiene backup activo (modo canal)\n\n"
                    f"📦 Canal: {existing.dest_chat_title}\n"
                    f"📨 Archivos respaldados: {existing.message_count}"
                )
                return
            
            await message.answer(
                "⏳ Activando backup automático...\n\n"
                "ℹ️ El canal de backup se creará cuando el userbot procese esta solicitud.\n"
                "📝 Esto puede tardar unos segundos."
            )
            
            # Crear el mapeo como "pendiente"
            if existing:
                existing.enabled = True
            else:
                # Marcar como pendiente - el userbot lo procesará
                new_mapping = BackupMapping(
                    source_chat_id=chat_id,
                    dest_chat_id=0,  # Temporal, el userbot lo actualizará
                    dest_chat_title=f"⏳ Pendiente: {entity.title}",
                    enabled=True
                )
                session.add(new_mapping)
            
            session.commit()
            
            await message.answer(
                f"✅ Backup marcado como activo\n\n"
                f"📦 Grupo: {entity.title}\n"
                f"🆔 ID: {chat_id}\n\n"
                f"💡 El userbot creará el canal de backup automáticamente\n"
                f"💡 Usa /backup_estado en unos segundos para verificar"
            )
            
        finally:
            session.close()
        
    except ValueError:
        await message.answer("❌ El ID debe ser un número.\n\nEjemplo: /backup_activar -1001234567890")
    except Exception as e:
        await message.answer(f"❌ Error: {str(e)[:200]}")

async def cmd_backup_desactivar(message: types.Message):
    """Comando /backup_desactivar [ID] - Desactiva backup para un grupo"""
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer(
                "❌ Uso incorrecto\n\n"
                "✅ Uso correcto: /backup_desactivar [ID]\n\n"
                "Ejemplo: /backup_desactivar -1001234567890\n\n"
                "💡 Usa /backup_estado para ver los backups activos"
            )
            return
        
        chat_id = int(parts[1])
        
        from userbot.backup_manager import disable_backup
        
        result = await disable_backup(chat_id)
        await message.answer(result['message'])
        
    except ValueError:
        await message.answer("❌ El ID debe ser un número.\n\nEjemplo: /backup_desactivar -1001234567890")
    except Exception as e:
        await message.answer(f"❌ Error: {str(e)[:200]}")

async def cmd_backup_estado(message: types.Message):
    """Comando /backup_estado - Muestra estado de todos los backups"""
    session = SessionLocal()
    
    try:
        mappings = session.query(BackupMapping).order_by(BackupMapping.enabled.desc()).all()
        
        if not mappings:
            await message.answer(
                "⚠️ No hay backups configurados\n\n"
                "💡 Usa /backup_lista para ver grupos disponibles\n"
                "💡 Usa /backup_activar [ID] para activar un backup"
            )
            return
        
        activos = [m for m in mappings if m.enabled]
        pausados = [m for m in mappings if not m.enabled]
        
        text = f"📊 Estado de Backups ({len(mappings)} total)\n\n"
        
        if activos:
            text += f"✅ Activos ({len(activos)}):\n\n"
            for m in activos:
                title = (m.dest_chat_title or 'Sin título')[:40]
                mode = m.storage_mode or 'channel'
                
                # Indicar si está pendiente
                if m.dest_chat_id == 0:
                    status = "⏳ PENDIENTE"
                else:
                    status = "✅ ACTIVO"
                
                mode_emoji = "📢" if mode == 'channel' else "📌"
                text += f"{status} {mode_emoji} [{mode.upper()}] {title}\n"
                text += f"   ├ ID Origen: {m.source_chat_id}\n"
                text += f"   ├ Archivos: {m.message_count}\n"
                
                if mode == 'topic' and m.topic_id:
                    text += f"   ├ Tema ID: {m.topic_id}\n"
                
                if m.dest_chat_id != 0:
                    dest_label = "Tema en" if mode == 'topic' else "Canal"
                    text += f"   └ {dest_label}: {m.dest_chat_id}\n\n"
                else:
                    text += f"   └ El {'tema' if mode == 'topic' else 'canal'} se está creando...\n\n"
        
        if pausados:
            text += f"\n⏸️ Pausados ({len(pausados)}):\n\n"
            for m in pausados:
                title = (m.dest_chat_title or 'Sin título')[:40]
                text += f"📦 {title}\n"
                text += f"   ├ ID: {m.source_chat_id}\n"
                text += f"   └ Archivos: {m.message_count}\n\n"
        
        text += "\n💡 Usa /backup_desactivar [ID] para pausar un backup"
        text += "\n💡 Usa /backup_activar [ID] para reactivar uno pausado"
        text += "\n💡 Envía /backup_historial en el grupo para descargar archivos antiguos"
        
        if len(text) > 4000:
            parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
            for part in parts:
                await message.answer(part)
        else:
            await message.answer(text)
    
    except Exception as e:
        await message.answer(f"❌ Error: {str(e)[:200]}")
    finally:
        session.close()

async def cmd_backup_info(message: types.Message):
    """Comando /backup_info - Información sobre cómo descargar historial"""
    info_text = (
        "📚 Descargar Historial de Multimedia\n\n"
        "Para descargar todo el contenido multimedia antiguo de un grupo:\n\n"
        "1️⃣ Obtén el ID del grupo:\n"
        "   • /backup_lista\n\n"
        "2️⃣ Inicia la descarga del historial:\n"
        "   • /backup_historial [ID]\n\n"
        "3️⃣ Espera a que termine (puede tardar minutos)\n\n"
        "Ejemplo:\n"
        "/backup_historial -1001234567890\n\n"
        "⚠️ Notas importantes:\n"
        "• Descarga TODOS los archivos multimedia del grupo\n"
        "• Puede tardar mucho si hay miles de archivos\n"
        "• Funciona incluso en canales donde no puedes escribir\n"
        "• El proceso continúa en segundo plano\n\n"
        "💡 Los archivos nuevos se respaldan automáticamente, el historial es opcional"
    )
    await message.answer(info_text)

async def cmd_backup_historial(message: types.Message):
    """Comando /backup_historial [ID] - Descarga el historial completo de un grupo"""
    try:
        # Extraer el ID del comando
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer(
                "❌ Uso incorrecto\n\n"
                "✅ Uso correcto: /backup_historial [ID]\n\n"
                "Ejemplo: /backup_historial -1001234567890\n\n"
                "💡 Usa /backup_lista para ver los IDs disponibles"
            )
            return
        
        chat_id = int(parts[1])
        
        # Verificar que existe en la base de datos
        session = SessionLocal()
        try:
            entity = session.query(TelegramEntity).filter_by(telegram_id=chat_id).first()
            if not entity:
                await message.answer(
                    "❌ No se encontró ese grupo/canal.\n\n"
                    "💡 Primero usa /scan en tu cuenta de Telegram\n"
                    "💡 Luego usa /backup_lista para ver los IDs"
                )
                return
            
            # Verificar si tiene backup activo
            mapping = session.query(BackupMapping).filter_by(source_chat_id=chat_id, enabled=True).first()
            if not mapping or mapping.dest_chat_id == 0:
                await message.answer(
                    f"❌ Este grupo no tiene backup activo.\n\n"
                    f"💡 Primero actívalo con: /backup_activar {chat_id}"
                )
                return
            
            await message.answer(
                f"⏳ Iniciando descarga del historial...\n\n"
                f"📦 Grupo: {entity.title}\n"
                f"🆔 ID: {chat_id}\n\n"
                f"📊 Esto puede tardar varios minutos.\n"
                f"💡 El proceso continúa en segundo plano.\n"
                f"💡 Usa /backup_estado para ver el progreso."
            )
            
            # Marcar como pendiente en la base de datos
            mapping.historial_pending = True
            session.commit()
            
            await message.answer(
                "✅ Solicitud registrada\n\n"
                "📊 El userbot procesará el historial automáticamente\n"
                "💡 Usa /backup_estado para ver el progreso en tiempo real"
            )
            
        finally:
            session.close()
        
    except ValueError:
        await message.answer("❌ El ID debe ser un número.\n\nEjemplo: /backup_historial -1001234567890")
    except Exception as e:
        await message.answer(f"❌ Error: {str(e)[:200]}")


async def cmd_backup_topic_activar(message: types.Message):
    """Comando /backup_topic_activar [ID] - Activa backup en modo tema (supergrupo con temas)"""
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer(
                "❌ Uso incorrecto\n\n"
                "✅ Uso correcto: /backup_topic_activar [ID]\n\n"
                "Ejemplo: /backup_topic_activar -1001234567890\n\n"
                "💡 Usa /backup_lista para ver los IDs disponibles"
            )
            return
        
        chat_id = int(parts[1])
        
        # Verificar que el grupo existe en la base de datos
        session = SessionLocal()
        try:
            entity = session.query(TelegramEntity).filter_by(telegram_id=chat_id).first()
            if not entity:
                await message.answer(
                    "❌ No se encontró ese grupo/canal.\n\n"
                    "💡 Primero usa /scan en tu cuenta de Telegram\n"
                    "💡 Luego usa /backup_lista para ver los IDs"
                )
                return
            
            # Verificar BACKUP_GROUP_ID
            from userbot.config import BACKUP_GROUP_ID
            if not BACKUP_GROUP_ID:
                await message.answer(
                    "❌ BACKUP_GROUP_ID no configurado en .env\n\n"
                    "💡 Debes configurar un supergrupo con temas activados"
                )
                session.close()
                return
            
            # Verificar si ya tiene backup en modo topic
            from database.models import BackupMapping
            existing = session.query(BackupMapping).filter_by(
                source_chat_id=chat_id,
                storage_mode='topic'
            ).first()
            
            if existing and existing.enabled:
                await message.answer(
                    f"⚠️ El backup en modo tema ya está activo\n\n"
                    f"📦 Supergrupo: {BACKUP_GROUP_ID}\n"
                    f"📌 Tema ID: {existing.topic_id}\n"
                    f"📨 Archivos respaldados: {existing.message_count}"
                )
                session.close()
                return
            
            await message.answer(
                "⏳ Activando backup en modo tema...\n\n"
                "ℹ️ Se creará un tema en el supergrupo de backup.\n"
                "📝 Esto puede tardar unos segundos."
            )
            
            # Importar función del userbot
            from userbot.backup_topic.service import backup_to_topic
            from userbot.main import get_client as get_userbot_client
            
            userbot_client = get_userbot_client()
            if not userbot_client or not userbot_client.is_connected():
                await message.answer("❌ El userbot no está conectado. Asegúrate de que run_userbot.py esté en ejecución.")
                session.close()
                return
            
            # Activar backup en modo topic
            result = await backup_to_topic(userbot_client, chat_id, entity.title)
            
            if result['success']:
                await message.answer(result['message'])
            else:
                await message.answer(result['message'])
            
        finally:
            session.close()
        
    except ValueError:
        await message.answer("❌ El ID debe ser un número.\n\nEjemplo: /backup_topic_activar -1001234567890")
    except Exception as e:
        await message.answer(f"❌ Error: {str(e)[:200]}")


async def cmd_backup_topic_info(message: types.Message):
    """Comando /backup_topic_info - Información sobre backup en modo tema"""
    from userbot.config import BACKUP_GROUP_ID, BACKUP_MODE
    
    info_text = (
        "📦 **Backup en Modo Tema (Supergrupo)**\n\n"
        "Este modo guarda los backups en **temas** dentro de un supergrupo compartido.\n\n"
        "**Configuración actual**:\n"
        f"• BACKUP_MODE: `{BACKUP_MODE}`\n"
        f"• BACKUP_GROUP_ID: `{BACKUP_GROUP_ID or 'No configurado'}`\n\n"
        "**Ventajas del modo tema**:\n"
        "• ✅ Más organizado (un tema por grupo)\n"
        "• ✅ Todo en un solo lugar\n"
        "• ✅ Fácil de navegar\n"
        "• ✅ Ideal para backups masivos\n\n"
        "**Requisitos**:\n"
        "1️⃣ Crear un supergrupo\n"
        "2️⃣ Activar **Temas** en la configuración\n"
        "3️⃣ Añadir el userbot como administrador\n"
        "4️⃣ Configurar BACKUP_GROUP_ID en .env\n\n"
        "**Comandos**:\n"
        "• /backup_topic_activar [ID] - Activar backup en modo tema\n"
        "• /backup_activar [ID] - Activar backup en modo canal (tradicional)\n"
        "• /backup_estado - Ver todos los backups\n\n"
        "💡 **Puedes tener ambos modos activos para el mismo grupo**"
    )
    await message.answer(info_text, parse_mode="Markdown")


async def cmd_backup_topic_historial(message: types.Message):
    """Comando /backup_topic_historial [ID] - Descarga el historial completo a un tema"""
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer(
                "❌ Uso incorrecto\n\n"
                "✅ Uso correcto: /backup_topic_historial [ID]\n\n"
                "Ejemplo: /backup_topic_historial -1001234567890\n\n"
                "💡 Usa /backup_lista para ver los IDs disponibles"
            )
            return
        
        chat_id = int(parts[1])
        
        session = SessionLocal()
        try:
            entity = session.query(TelegramEntity).filter_by(telegram_id=chat_id).first()
            if not entity:
                await message.answer(
                    "❌ No se encontró ese grupo/canal.\n\n"
                    "💡 Primero usa /scan en tu cuenta de Telegram\n"
                    "💡 Luego usa /backup_lista para ver los IDs"
                )
                return
            
            # Verificar si tiene backup activo en modo topic
            mapping = session.query(BackupMapping).filter_by(
                source_chat_id=chat_id,
                enabled=True,
                storage_mode='topic'
            ).first()
            
            if not mapping or not mapping.topic_id:
                await message.answer(
                    f"❌ Este grupo no tiene backup activo en modo tema.\n\n"
                    f"💡 Primero actívalo con: /backup_topic_activar {chat_id}"
                )
                return
            
            await message.answer(
                f"⏳ Iniciando descarga del historial al tema...\n\n"
                f"📦 Grupo: {entity.title}\n"
                f"🆔 ID: {chat_id}\n"
                f"📌 Tema ID: {mapping.topic_id}\n\n"
                f"📊 Esto puede tardar varios minutos.\n"
                f"💡 El proceso continúa en segundo plano."
            )
            
            # Lanzar la descarga del historial
            from userbot.backup_topic.service import download_historial_to_topic
            from userbot.main import get_client as get_userbot_client
            
            userbot_client = get_userbot_client()
            if not userbot_client or not userbot_client.is_connected():
                await message.answer("❌ El userbot no está conectado.")
                return
            
            import asyncio
            asyncio.create_task(
                download_historial_to_topic(
                    userbot_client, chat_id, mapping.topic_id, entity.title
                )
            )
            
            await message.answer(
                "✅ Descarga de historial iniciada\n\n"
                "📊 El proceso continúa en segundo plano\n"
                "💡 Recibirás notificaciones de progreso"
            )
            
        finally:
            session.close()
        
    except ValueError:
        await message.answer("❌ El ID debe ser un número.\n\nEjemplo: /backup_topic_historial -1001234567890")
    except Exception as e:
        await message.answer(f"❌ Error: {str(e)[:200]}")


async def cmd_links_chat(message: types.Message):
    """/links_chat <chat_id> - Ver enlaces encontrados para un chat"""
    args = _get_args(message)
    if not args:
        await message.answer("❌ Uso: /links_chat <chat_id>\nEjemplo: /links_chat 123456789")
        return

    try:
        chat_id = int(args.strip())
    except ValueError:
        await message.answer("❌ El chat_id debe ser numérico")
        return

    session = SessionLocal()
    try:
        q = session.query(FoundLink).filter(FoundLink.source_chat_id == chat_id)
        total = q.count()
        if total == 0:
            await message.answer("📭 No hay enlaces registrados para ese chat.")
            return

        # Mostrar últimos 20
        links = (
            q.order_by(FoundLink.created_at.desc())
            .limit(20)
            .all()
        )

        text = (
            f"🔗 Enlaces encontrados para chat {chat_id}\n"
            f"📊 Total: {total}\n\n"
        )
        for l in links:
            status = "🟢 joined" if l.joined else ("🔴 failed" if l.failed else "⏳ pending")
            text += f"{status} — {l.link}\n"

        await message.answer(text)
    except Exception as e:
        await message.answer(f"❌ Error en /links_chat: {str(e)[:200]}")
    finally:
        session.close()


async def cmd_links_estado(message: types.Message):
    """/links_estado [estado] - Ver enlaces por estado (pending|joined|failed)"""
    args_text = _get_args(message)
    args = args_text.strip().lower() if args_text else "pending"

    session = SessionLocal()
    try:
        q = session.query(FoundLink)
        if args == "joined":
            q = q.filter(FoundLink.joined.is_(True))
        elif args == "failed":
            q = q.filter(FoundLink.failed.is_(True))
        else:
            q = q.filter(FoundLink.processed.is_(False))
            args = "pending"

        total = q.count()
        if total == 0:
            await message.answer(f"📭 No hay enlaces con estado {args}.")
            return

        links = q.order_by(FoundLink.created_at.desc()).limit(20).all()

        text = (
            f"🔗 Enlaces estado {args}\n"
            f"📊 Total: {total}\n\n"
        )
        for l in links:
            text += f"[{l.source_chat_id}] {l.link}\n"

        await message.answer(text)
    except Exception as e:
        await message.answer(f"❌ Error en /links_estado: {str(e)[:200]}")
    finally:
        session.close()


async def cmd_linkrule_add(message: types.Message):
    """/linkrule_add <pattern> <whitelist|blacklist> - Añadir regla de enlaces"""
    args = _get_args(message)
    if not args:
        await message.answer(
            "❌ Uso: /linkrule_add <pattern> <whitelist|blacklist>\n"
            "Ejemplo: /linkrule_add t.me/mi_can whitelist"
        )
        return

    parts = args.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❌ Debes indicar patrón y tipo (whitelist|blacklist)")
        return

    pattern = parts[0].strip()
    kind = parts[1].strip().lower()
    is_whitelist = kind != "blacklist"

    session = SessionLocal()
    try:
        existing = session.query(LinkRule).filter_by(pattern=pattern).first()
        if existing:
            existing.is_whitelist = is_whitelist
            existing.enabled = True
        else:
            rule = LinkRule(pattern=pattern, is_whitelist=is_whitelist, enabled=True)
            session.add(rule)

        session.commit()
        await message.answer(
            f"✅ Regla guardada: {pattern} → {'whitelist' if is_whitelist else 'blacklist'}"
        )
    except Exception as e:
        session.rollback()
        await message.answer(f"❌ Error en /linkrule_add: {str(e)[:200]}")
    finally:
        session.close()


async def cmd_linkrule_list(message: types.Message):
    """/linkrule_list - Ver reglas de enlaces"""
    session = SessionLocal()
    try:
        rules = session.query(LinkRule).order_by(LinkRule.id.asc()).all()
        if not rules:
            await message.answer("📭 No hay reglas de enlaces definidas.")
            return

        text = "📜 Reglas de enlaces:\n\n"
        for r in rules:
            status = "✅" if r.enabled else "⏸️"
            kind = "whitelist" if r.is_whitelist else "blacklist"
            text += f"{status} [{r.id}] {kind} → {r.pattern}\n"

        await message.answer(text)
    except Exception as e:
        await message.answer(f"❌ Error en /linkrule_list: {str(e)[:200]}")
    finally:
        session.close()


async def cmd_linkrule_toggle(message: types.Message):
    """/linkrule_toggle <id> - Activar/desactivar una regla"""
    args_text = _get_args(message)
    args = args_text.strip() if args_text else ""
    if not args.isdigit():
        await message.answer("❌ Uso: /linkrule_toggle <id>")
        return

    rule_id = int(args)

    session = SessionLocal()
    try:
        rule = session.query(LinkRule).filter_by(id=rule_id).first()
        if not rule:
            await message.answer("❌ No se encontró una regla con ese ID.")
            return

        rule.enabled = not rule.enabled
        session.commit()

        await message.answer(
            f"✅ Regla {rule_id} ahora está {'activa' if rule.enabled else 'desactivada'}."
        )
    except Exception as e:
        session.rollback()
        await message.answer(f"❌ Error en /linkrule_toggle: {str(e)[:200]}")
    finally:
        session.close()


DIR_PER_PAGE = 5


def format_directory(items, page: int, per_page: int) -> str:
    """Devuelve el texto formateado del directorio para una página concreta.

    items: lista de tuplas (title, link)
    """
    if page < 1:
        page = 1

    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    chunk = items[start:end]

    text = f"📂 Directorio de enlaces (Página {page})\n\n"

    if not chunk:
        text += "No hay enlaces en esta página."
        return text

    for i, (title, link) in enumerate(chunk, start=1):
        safe_title = title or "Sin título"
        text += f"{i}. {safe_title}\n   🔗 {link}\n"

    return text


async def cmd_directorio(message: types.Message):
    """/directorio - Directorio paginado de enlaces encontrados"""
    session = SessionLocal()
    try:
        # Si todavía no hay enlaces en FoundLink, inicializarlos a partir de las entidades
        total_found = session.query(FoundLink).count()
        if total_found == 0:
            # Copiar enlaces ya guardados por /scan (TelegramEntity.invite_link)
            entities_with_link = (
                session.query(TelegramEntity)
                .filter(TelegramEntity.invite_link.isnot(None))
                .all()
            )

            for e in entities_with_link:
                link = e.invite_link
                if not link:
                    continue

                exists = (
                    session.query(FoundLink)
                    .filter_by(source_chat_id=e.telegram_id, link=link)
                    .first()
                )
                if not exists:
                    item = FoundLink(
                        source_chat_id=e.telegram_id,
                        message_id=0,
                        link=link,
                    )
                    session.add(item)

            session.commit()

        links_q = session.query(FoundLink).order_by(FoundLink.created_at.desc())
        found = links_q.all()

        if not found:
            await message.answer("📭 No hay enlaces guardados en el directorio.")
            return

        # Mapear títulos de entidades para mostrar nombre + enlace
        chat_ids = {l.source_chat_id for l in found}
        entities = (
            session.query(TelegramEntity)
            .filter(TelegramEntity.telegram_id.in_(chat_ids))
            .all()
        )
        titles_by_id = {
            e.telegram_id: (e.title or e.username or str(e.telegram_id)) for e in entities
        }

        items = [
            (titles_by_id.get(l.source_chat_id, str(l.source_chat_id)), l.link)
            for l in found
        ]

        page = 1
        total_pages = (len(items) + DIR_PER_PAGE - 1) // DIR_PER_PAGE

        text = format_directory(items, page, DIR_PER_PAGE)
        entries = [(l.id, l.link) for l in found[:DIR_PER_PAGE]]

        await message.answer(
            text,
            reply_markup=directory_keyboard(entries, page, total_pages)
        )
    except Exception as e:
        await message.answer(f"❌ Error en /directorio: {str(e)[:200]}")
    finally:
        session.close()


async def directory_paginate_callback(callback: types.CallbackQuery):
    """Callback para cambiar de página en el directorio de enlaces."""
    try:
        data = callback.data or ""
        parts = data.split(":", maxsplit=1)
        if len(parts) != 2:
            await callback.answer()
            return

        page = int(parts[1])
    except ValueError:
        await callback.answer()
        return

    session = SessionLocal()
    try:
        links_q = session.query(FoundLink).order_by(FoundLink.created_at.desc())
        found = links_q.all()

        if not found:
            await callback.answer("No hay enlaces.", show_alert=True)
            return

        chat_ids = {l.source_chat_id for l in found}
        entities = (
            session.query(TelegramEntity)
            .filter(TelegramEntity.telegram_id.in_(chat_ids))
            .all()
        )
        titles_by_id = {
            e.telegram_id: (e.title or e.username or str(e.telegram_id)) for e in entities
        }

        items = [
            (titles_by_id.get(l.source_chat_id, str(l.source_chat_id)), l.link)
            for l in found
        ]

        total_pages = (len(items) + DIR_PER_PAGE - 1) // DIR_PER_PAGE

        # Clamp de página
        if page < 1:
            page = 1
        if page > total_pages:
            page = total_pages

        text = format_directory(items, page, DIR_PER_PAGE)

        start = (page - 1) * DIR_PER_PAGE
        end = start + DIR_PER_PAGE
        entries = [(l.id, l.link) for l in found[start:end]]

        try:
            await callback.message.edit_text(
                text,
                reply_markup=directory_keyboard(entries, page, total_pages)
            )
        except Exception as e:
            # Errores menores como "message is not modified" se silencian
            if "message is not modified" in str(e).lower():
                await callback.answer()
                return
            await callback.answer("Error al cambiar de página", show_alert=True)
            return

        await callback.answer()
    except Exception as e:
        # Mostrar el error real para poder depurarlo mejor
        await callback.answer(f"Error al cambiar de página: {str(e)[:80]}", show_alert=True)
    finally:
        session.close()


async def directory_join_callback(callback: types.CallbackQuery):
    """Callback para unirse a un enlace concreto desde el directorio."""
    data = callback.data or ""
    parts = data.split(":", maxsplit=1)
    if len(parts) != 2:
        await callback.answer()
        return

    try:
        link_id = int(parts[1])
    except ValueError:
        await callback.answer()
        return

    client = get_userbot_client()
    if client is None or not client.is_connected():
        await callback.answer(
            "El userbot no está conectado. Ejecuta run_userbot.py.",
            show_alert=True,
        )
        return

    from feature.scanner.joiner import join_from_link
    from feature.scanner.limiter import safe_delay
    from feature.scanner.service import ensure_entity_for_chat
    from userbot.config import JOIN_DELAY_SECONDS

    session = SessionLocal()
    try:
        link_obj = session.query(FoundLink).filter_by(id=link_id).first()
        if not link_obj:
            await callback.answer("Enlace no encontrado.", show_alert=True)
            return

        # No intentar unirse a enlaces de carpetas (addlist)
        if "addlist" in (link_obj.link or "").lower():
            mark_link_result(session, link_obj, joined=False, failed=True)
            session.commit()
            await callback.answer(
                "Este tipo de enlace (carpeta/addlist) no se procesa.",
                show_alert=True,
            )
            return

        await safe_delay(JOIN_DELAY_SECONDS)

        try:
            result = await join_from_link(client, link_obj.link)

            joined_chat = None
            try:
                if hasattr(result, "chats") and result.chats:
                    joined_chat = result.chats[0]
                elif hasattr(result, "user"):
                    joined_chat = result.user
            except Exception:
                joined_chat = None

            if joined_chat is not None and hasattr(joined_chat, "id"):
                title = getattr(joined_chat, "title", None) or getattr(
                    joined_chat, "first_name", None
                )
                username = getattr(joined_chat, "username", None)
                ensure_entity_for_chat(joined_chat.id, title, username)

            mark_link_result(session, link_obj, joined=True, failed=False)
            session.commit()
            await callback.answer("Unido correctamente.", show_alert=True)
        except Exception as e:
            mark_link_result(session, link_obj, joined=False, failed=True)
            session.commit()
            await callback.answer(
                f"Error al unirse: {str(e)[:80]}",
                show_alert=True,
            )
    finally:
        session.close()


async def cmd_links_resumen(message: types.Message):
    """/links_resumen [chat_id] - Resumen de enlaces global o por chat"""
    args = _get_args(message)

    session = SessionLocal()
    try:
        if args and args.lstrip("-").isdigit():
            chat_id = int(args)
            base_q = session.query(FoundLink).filter(FoundLink.source_chat_id == chat_id)
            scope_title = f"para chat {chat_id}"
        else:
            chat_id = None
            base_q = session.query(FoundLink)
            scope_title = "global"

        total = base_q.count()
        if total == 0:
            await message.answer(f"📭 No hay enlaces registrados {scope_title}.")
            return

        pending = base_q.filter(FoundLink.processed.is_(False)).count()
        joined = base_q.filter(FoundLink.joined.is_(True)).count()
        failed = base_q.filter(FoundLink.failed.is_(True)).count()

        text = (
            f"📊 Resumen de enlaces {scope_title}\n\n"
            f"🔗 Total: {total}\n"
            f"⏳ Pendientes: {pending}\n"
            f"🟢 Join OK: {joined}\n"
            f"🔴 Fallidos: {failed}\n"
        )

        if chat_id is None:
            # Top chats por cantidad total
            from sqlalchemy import func

            top_chats = (
                session.query(FoundLink.source_chat_id, func.count(FoundLink.id))
                .group_by(FoundLink.source_chat_id)
                .order_by(func.count(FoundLink.id).desc())
                .limit(10)
                .all()
            )

            if top_chats:
                text += "\n🏆 Top chats por enlaces:\n"
                for cid, cnt in top_chats:
                    text += f"• {cid}: {cnt} enlaces\n"

        await message.answer(text)
    except Exception as e:
        await message.answer(f"❌ Error en /links_resumen: {str(e)[:200]}")
    finally:
        session.close()

def register_handlers(dp):
    """Registra todos los handlers del bot"""
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_help, Command("help"))
    dp.message.register(cmd_listar, Command("listar"))
    dp.message.register(cmd_categorias, Command("categorias"))
    dp.message.register(cmd_stats, Command("stats"))
    dp.message.register(cmd_addlink, Command("addlink"))
    dp.message.register(cmd_sinlink, Command("sinlink"))
    dp.message.register(cmd_scan, Command("scan"))
    dp.message.register(cmd_scanchat, Command("scanchat"))
    dp.message.register(cmd_joinlinks, Command("joinlinks"))
    dp.message.register(cmd_unir_guardados, Command("unir_guardados"))
    dp.message.register(cmd_escanear_y_unir, Command("escanear_y_unir"))
    dp.message.register(cmd_directorio, Command("directorio"))
    
    # Comandos de backup
    dp.message.register(cmd_backup_lista, Command("backup_lista"))
    dp.message.register(cmd_backup_activar, Command("backup_activar"))
    dp.message.register(cmd_backup_desactivar, Command("backup_desactivar"))
    dp.message.register(cmd_backup_estado, Command("backup_estado"))
    dp.message.register(cmd_backup_info, Command("backup_info"))
    dp.message.register(cmd_backup_historial, Command("backup_historial"))
    dp.message.register(cmd_backup_topic_activar, Command("backup_topic_activar"))
    dp.message.register(cmd_backup_topic_info, Command("backup_topic_info"))
    dp.message.register(cmd_backup_topic_historial, Command("backup_topic_historial"))
    # Scanner links
    dp.message.register(cmd_links_chat, Command("links_chat"))
    dp.message.register(cmd_links_estado, Command("links_estado"))
    dp.message.register(cmd_linkrule_add, Command("linkrule_add"))
    dp.message.register(cmd_linkrule_list, Command("linkrule_list"))
    dp.message.register(cmd_linkrule_toggle, Command("linkrule_toggle"))
    dp.message.register(cmd_links_resumen, Command("links_resumen"))
    # Callbacks inline
    dp.callback_query.register(directory_paginate_callback, F.data.startswith("dir:"))
    dp.callback_query.register(directory_join_callback, F.data.startswith("join:"))
    
    print("✅ Handlers del bot registrados")


"""
Servicio principal de backup en modo tema (topic mode)
"""
from database.db import SessionLocal
from database.models import BackupMapping, TelegramEntity
from userbot.backup_topic.topics import get_or_create_topic
from userbot.backup_topic.sender import (
    forward_to_topic, send_file_to_topic, send_welcome_message,
    _get_full_group_id, _ensure_entity_loaded, extract_file_info
)
from userbot.config import BACKUP_GROUP_ID, CONTROL_BOT_ID
import logging
import asyncio

logger = logging.getLogger(__name__)


async def backup_to_topic(client, source_chat_id, source_title):
    """
    Activa el backup en modo tema para un chat origen.
    Incluye descarga automática del historial completo.

    Args:
        client: Cliente de Telethon
        source_chat_id: ID del chat origen
        source_title: Título del chat origen

    Returns:
        dict: Resultado de la operación
    """
    if not BACKUP_GROUP_ID:
        return {
            'success': False,
            'message': '❌ BACKUP_GROUP_ID no configurado en .env'
        }

    session = SessionLocal()
    try:
        # Verificar si ya tiene backup en modo topic
        existing = session.query(BackupMapping).filter_by(
            source_chat_id=source_chat_id,
            storage_mode='topic'
        ).first()

        if existing and existing.enabled:
            session.close()
            return {
                'success': False,
                'message': f'⚠️ El backup en modo tema ya está activo\n📦 Tema ID: {existing.topic_id}'
            }

        # Obtener o crear el tema
        topic_id = await get_or_create_topic(client, BACKUP_GROUP_ID, source_chat_id, source_title)

        if not topic_id:
            session.close()
            return {
                'success': False,
                'message': '❌ No se pudo crear el tema. Verifica que el grupo tenga temas activados.'
            }

        # Enviar mensaje de bienvenida
        try:
            await send_welcome_message(client, BACKUP_GROUP_ID, topic_id, source_title, source_chat_id)
        except Exception as e:
            logger.warning(f"⚠️ No se pudo enviar mensaje de bienvenida: {str(e)[:100]}")

        session.close()

        # 📚 INICIAR DESCARGA DEL HISTORIAL EN BACKGROUND
        asyncio.create_task(
            download_historial_to_topic(client, source_chat_id, topic_id, source_title)
        )

        return {
            'success': True,
            'message': f'✅ Backup en modo tema activado\n📦 Supergrupo: {BACKUP_GROUP_ID}\n📌 Tema ID: {topic_id}\n📚 Descargando historial completo...\n💾 Los nuevos archivos multimedia se guardarán automáticamente en este tema'
        }

    except Exception as e:
        session.rollback()
        session.close()
        return {
            'success': False,
            'message': f'❌ Error: {str(e)[:200]}'
        }


async def process_pending_topic_backups(client):
    """
    Procesa backups pendientes en modo tema y crea los temas necesarios.
    Se ejecuta en segundo plano similar al process_pending_backups de canales.
    """
    await client.get_me()
    
    while True:
        try:
            session = SessionLocal()
            try:
                # Buscar backups topic pendientes (dest_chat_id = 0 o topic_id = None)
                pending = session.query(BackupMapping).filter_by(
                    dest_chat_id=0,
                    enabled=True,
                    storage_mode='topic'
                ).all()
                
                for mapping in pending:
                    try:
                        entity = session.query(TelegramEntity).filter_by(
                            telegram_id=mapping.source_chat_id
                        ).first()
                        
                        if not entity:
                            continue
                        
                        logger.info(f"📦 Creando tema de backup para: {entity.title}")
                        
                        topic_id = await get_or_create_topic(
                            client,
                            BACKUP_GROUP_ID,
                            mapping.source_chat_id,
                            entity.title
                        )
                        
                        if topic_id:
                            # Usar ID completo con -100 para dest_chat_id
                            full_group_id = _get_full_group_id(BACKUP_GROUP_ID)
                            mapping.dest_chat_id = full_group_id
                            mapping.dest_chat_title = f"📦 Topic: {entity.title[:40]}"
                            mapping.topic_id = topic_id
                            session.commit()
                            logger.info(f"✅ Tema creado: {mapping.dest_chat_title} (ID: {topic_id})")
                        else:
                            logger.error(f"❌ Error creando tema para {mapping.source_chat_id}")
                            session.rollback()
                            
                    except Exception as e:
                        logger.error(f"❌ Error creando tema para {mapping.source_chat_id}: {str(e)[:100]}")
                        session.rollback()
                        
            finally:
                session.close()
            
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"❌ Error en process_pending_topic_backups: {str(e)[:100]}")
            await asyncio.sleep(60)


async def download_historial_to_topic(client, source_chat_id, topic_id, title):
    """
    Descarga el historial completo de un grupo a un tema específico.
    Usa reenvío directo (ForwardMessagesRequest con top_msg_id) cuando es posible.
    Cuando el chat está protegido, descarga y re-sube preservando el formato original.

    Args:
        client: Cliente de Telethon
        source_chat_id: ID del chat origen
        topic_id: ID del tema destino
        title: Título del chat origen
    """
    try:
        logger.info(f"📚 Iniciando descarga de historial al tema: {title}")

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
        
        # Pre-cargar la entidad del grupo de backups
        full_group_id = await _ensure_entity_loaded(client, BACKUP_GROUP_ID)

        async for message in client.iter_messages(source_chat_id, limit=None, reverse=True):
            if message.media:
                try:
                    # Intentar reenvío directo (rápido, sin descarga)
                    success = await forward_to_topic(
                        client, BACKUP_GROUP_ID, topic_id, message, source_chat_id
                    )

                    if not success:
                        # Fallback: descargar y re-subir preservando formato
                        file_bytes = await client.download_media(message, file=bytes)
                        
                        if not file_bytes:
                            errors += 1
                            continue

                        # Extraer info del archivo original para preservar el formato
                        info = extract_file_info(message)
                        
                        if info['is_voice']:
                            # Notas de voz: enviar como voice_note
                            await client.send_file(
                                full_group_id,
                                file_bytes,
                                caption=message.message,
                                reply_to=topic_id,
                                voice_note=True,
                                attributes=info['attributes']
                            )
                        else:
                            # Todo lo demás: usar send_file_to_topic con atributos completos
                            await send_file_to_topic(
                                client,
                                BACKUP_GROUP_ID,
                                topic_id,
                                file_bytes,
                                caption=message.message,
                                attributes=info['attributes'],
                                force_document=info['force_document'],
                                mime_type=info['mime_type'],
                                file_name=info['file_name']
                            )

                    count += 1
                    
                    # Actualizar last_message_id para rastreo
                    if count % 50 == 0:
                        _update_last_message_id(source_chat_id, message.id)
                        logger.info(f"📊 {title}: {count} archivos")

                        if count - last_notification >= 100:
                            try:
                                await client.send_message(
                                    CONTROL_BOT_ID,
                                    f"📊 Progreso: {count} archivos descargados de {title}"
                                )
                                last_notification = count
                            except:
                                pass

                    # Rate limiting
                    if count % 10 == 0:
                        await asyncio.sleep(1)

                except Exception as e:
                    errors += 1
                    if errors <= 5:
                        logger.warning(f"⚠️ Error en {title}: {str(e)[:150]}")

        # Actualizar last_message_id final
        _update_last_message_id(source_chat_id, None, final=True)
        
        logger.info(f"✅ Historial completado: {title} - {count} archivos (errores: {errors})")
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
        logger.error(f"❌ Error procesando historial de {title}: {str(e)[:200]}")


def _update_last_message_id(source_chat_id, message_id, final=False):
    """Actualiza el last_message_id en la base de datos para evitar duplicados"""
    session = SessionLocal()
    try:
        mapping = session.query(BackupMapping).filter_by(
            source_chat_id=source_chat_id,
            storage_mode='topic'
        ).first()
        if mapping:
            if message_id:
                mapping.last_message_id = message_id
            if final:
                mapping.historial_pending = False
            session.commit()
    except:
        session.rollback()
    finally:
        session.close()

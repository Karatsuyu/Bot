"""Funciones para gestión de backup automático de multimedia"""
from telethon.tl.functions.channels import CreateChannelRequest
from database.db import SessionLocal
from database.models import BackupMapping, TelegramEntity
from datetime import datetime


async def create_backup_channel(client, source_chat_id, source_title):
    """
    Crea un canal privado para hacer backup de un grupo origen
    
    Args:
        client: Cliente de Telethon
        source_chat_id: ID del chat origen
        source_title: Título del chat origen
    
    Returns:
        tuple: (dest_chat_id, dest_chat_title)
    """
    try:
        # Crear canal privado
        result = await client(CreateChannelRequest(
            title=f"📦 Backup - {source_title[:50]}",
            about=f"Backup automático de multimedia del grupo: {source_title}\n🤖 ID Origen: {source_chat_id}",
            megagroup=False  # False = Canal, True = Supergrupo
        ))
        
        dest_channel = result.chats[0]
        return dest_channel.id, dest_channel.title
        
    except Exception as e:
        print(f"❌ Error creando canal de backup: {str(e)}")
        return None, None


async def enable_backup(client, source_chat_id):
    """
    Activa el backup para un grupo/canal
    
    Args:
        client: Cliente de Telethon
        source_chat_id: ID del chat origen
    
    Returns:
        dict: Resultado de la operación
    """
    session = SessionLocal()
    try:
        # Verificar que existe en entities
        source_entity = session.query(TelegramEntity).filter_by(telegram_id=source_chat_id).first()
        if not source_entity:
            return {
                'success': False,
                'message': '❌ Primero debes escanear ese grupo con /scan'
            }
        
        # Verificar si ya tiene backup configurado (modo canal)
        existing = session.query(BackupMapping).filter_by(
            source_chat_id=source_chat_id
        ).filter(
            (BackupMapping.storage_mode == 'channel') | (BackupMapping.storage_mode.is_(None))
        ).first()
        
        if existing:
            if existing.enabled:
                return {
                    'success': False,
                    'message': f'⚠️ El backup ya está activo\n📦 Canal: {existing.dest_chat_title}'
                }
            else:
                # Reactivar
                existing.enabled = True
                session.commit()
                return {
                    'success': True,
                    'message': f'✅ Backup reactivado\n📦 Canal: {existing.dest_chat_title}'
                }
        
        # Crear nuevo canal de backup
        dest_id, dest_title = await create_backup_channel(client, source_chat_id, source_entity.title)
        
        if not dest_id:
            return {
                'success': False,
                'message': '❌ No se pudo crear el canal de backup'
            }
        
        # Guardar en DB
        backup_mapping = BackupMapping(
            source_chat_id=source_chat_id,
            dest_chat_id=dest_id,
            dest_chat_title=dest_title,
            enabled=True
        )
        session.add(backup_mapping)
        session.commit()
        
        return {
            'success': True,
            'message': f'✅ Backup activado\n📦 Canal creado: {dest_title}\n💾 Los nuevos archivos multimedia se guardarán automáticamente'
        }
        
    except Exception as e:
        session.rollback()
        return {
            'success': False,
            'message': f'❌ Error: {str(e)[:200]}'
        }
    finally:
        session.close()


async def disable_backup(source_chat_id):
    """
    Desactiva el backup para un grupo/canal (no elimina el canal)
    
    Args:
        source_chat_id: ID del chat origen
    
    Returns:
        dict: Resultado de la operación
    """
    session = SessionLocal()
    try:
        mapping = session.query(BackupMapping).filter_by(
            source_chat_id=source_chat_id
        ).filter(
            (BackupMapping.storage_mode == 'channel') | (BackupMapping.storage_mode.is_(None))
        ).first()
        
        if not mapping:
            return {
                'success': False,
                'message': '⚠️ Este grupo no tiene backup configurado'
            }
        
        if not mapping.enabled:
            return {
                'success': False,
                'message': '⚠️ El backup ya está desactivado'
            }
        
        mapping.enabled = False
        session.commit()
        
        return {
            'success': True,
            'message': f'✅ Backup desactivado\n📦 Canal: {mapping.dest_chat_title}\n💡 El canal sigue existiendo pero no se guardarán nuevos archivos'
        }
        
    except Exception as e:
        session.rollback()
        return {
            'success': False,
            'message': f'❌ Error: {str(e)[:200]}'
        }
    finally:
        session.close()


def get_backup_status(source_chat_id=None):
    """
    Obtiene el estado de backup de un grupo específico o todos
    
    Args:
        source_chat_id: ID del chat origen (opcional)
    
    Returns:
        list o dict: Lista de configuraciones o una específica
    """
    session = SessionLocal()
    try:
        if source_chat_id:
            mapping = session.query(BackupMapping).filter_by(source_chat_id=source_chat_id).first()
            if not mapping:
                return None
            return {
                'source_chat_id': mapping.source_chat_id,
                'dest_chat_id': mapping.dest_chat_id,
                'dest_chat_title': mapping.dest_chat_title,
                'enabled': mapping.enabled,
                'message_count': mapping.message_count
            }
        else:
            mappings = session.query(BackupMapping).all()
            return [{
                'source_chat_id': m.source_chat_id,
                'dest_chat_id': m.dest_chat_id,
                'dest_chat_title': m.dest_chat_title,
                'enabled': m.enabled,
                'message_count': m.message_count
            } for m in mappings]
            
    finally:
        session.close()


def get_dest_channel(source_chat_id):
    """
    Obtiene el ID del canal destino para un chat origen si está activo
    
    Args:
        source_chat_id: ID del chat origen
    
    Returns:
        int o None: ID del canal destino si está activo
    """
    session = SessionLocal()
    try:
        mapping = session.query(BackupMapping).filter_by(
            source_chat_id=source_chat_id,
            enabled=True
        ).filter(
            (BackupMapping.storage_mode == 'channel') | (BackupMapping.storage_mode.is_(None))
        ).first()
        
        if mapping:
            return mapping.dest_chat_id
        return None
        
    finally:
        session.close()


def increment_message_count(source_chat_id):
    """
    Incrementa el contador de mensajes respaldados
    
    Args:
        source_chat_id: ID del chat origen
    """
    session = SessionLocal()
    try:
        mapping = session.query(BackupMapping).filter_by(
            source_chat_id=source_chat_id
        ).filter(
            (BackupMapping.storage_mode == 'channel') | (BackupMapping.storage_mode.is_(None))
        ).first()
        if mapping:
            mapping.message_count += 1
            session.commit()
    except:
        session.rollback()
    finally:
        session.close()


async def start_historial_backup(client, source_chat_id, dest_chat_id, chat_title):
    """
    Inicia la descarga del historial completo de un grupo

    Args:
        client: Cliente de Telethon
        source_chat_id: ID del chat origen
        dest_chat_id: ID del canal destino
        chat_title: Título del chat
    """
    count = 0
    errors = 0

    print(f"📚 Iniciando descarga de historial: {chat_title}")

    try:
        # Iterar por todos los mensajes con multimedia (del más antiguo al más nuevo)
        async for message in client.iter_messages(source_chat_id, limit=None, reverse=True):
            if message.media:
                try:
                    # Reenviar al canal de backup
                    await client.send_message(
                        dest_chat_id,
                        message
                    )
                    count += 1

                    # Incrementar contador en DB
                    increment_message_count(source_chat_id)

                    # Log cada 50 archivos
                    if count % 50 == 0:
                        print(f"📊 Progreso: {count} archivos de {chat_title}")

                except Exception as e:
                    errors += 1
                    if errors == 1:
                        print(f"⚠️ Error en backup: {str(e)[:100]}")

        print(f"✅ Historial completado: {count} archivos de {chat_title} (errores: {errors})")

    except Exception as e:
        print(f"❌ Error fatal en backup_historial de {chat_title}: {str(e)[:200]}")


def get_dest_topic(source_chat_id):
    """
    Obtiene el ID del tema destino para un chat origen si está activo en modo topic

    Args:
        source_chat_id: ID del chat origen

    Returns:
        int o None: topic_id si está activo en modo topic
    """
    session = SessionLocal()
    try:
        mapping = session.query(BackupMapping).filter_by(
            source_chat_id=source_chat_id,
            enabled=True,
            storage_mode='topic'
        ).first()

        if mapping and mapping.topic_id:
            return mapping.topic_id
        return None

    finally:
        session.close()

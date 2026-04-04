"""
Envío de mensajes y multimedia a temas en supergrupos
"""
from telethon.tl.functions.messages import ForwardMessagesRequest
from telethon.tl.types import DocumentAttributeFilename
import logging
import random

logger = logging.getLogger(__name__)


def _get_full_group_id(group_id):
    """
    Convierte cualquier formato de ID de supergrupo al formato completo -100XXXXXXXXXX
    que Telethon necesita para resolver entidades de tipo Channel/Supergrupo.
    
    Args:
        group_id: ID del grupo (string o int, con o sin -100)
    
    Returns:
        int: ID completo con formato -100XXXXXXXXXX (entero negativo)
    """
    try:
        id_str = str(group_id).strip()
        
        if id_str.startswith("-100"):
            return int(id_str)
        elif id_str.startswith("-"):
            raw = id_str[1:]
            return int(f"-100{raw}")
        elif id_str.startswith("100") and len(id_str) > 10:
            raw = id_str[3:]
            return int(f"-100{raw}")
        else:
            return int(f"-100{id_str}")
    except Exception:
        return int(group_id)


async def _ensure_entity_loaded(client, group_id):
    """
    Asegura que la entidad del supergrupo esté cargada en el cliente.
    Retorna el ID completo (negativo con -100) que Telethon puede resolver.
    """
    full_id = _get_full_group_id(group_id)
    
    # Intentar cargar la entidad con el ID completo
    try:
        entity = await client.get_entity(full_id)
        return full_id
    except Exception:
        pass
    
    # Intentar con el ID original
    try:
        entity = await client.get_entity(int(group_id))
        return int(group_id)
    except Exception:
        pass
    
    # Último recurso: buscar en diálogos
    raw_id = abs(full_id) % (10**10)  # Extraer el ID sin prefijo
    try:
        async for dialog in client.iter_dialogs():
            if dialog.id == full_id or dialog.id == raw_id:
                return full_id
    except Exception:
        pass
    
    return full_id


async def forward_to_topic(client, group_id, topic_id, message, from_peer=None):
    """
    Reenvía un mensaje a un tema específico usando la API directa de Telegram.
    Usa ForwardMessagesRequest con top_msg_id para colocar el mensaje en el topic correcto.

    Args:
        client: Cliente de Telethon
        group_id: ID del supergrupo
        topic_id: ID del tema
        message: Mensaje a reenviar (objeto Message de Telethon)
        from_peer: Peer origen (se obtiene del mensaje si no se proporciona)

    Returns:
        bool: True si se reenvió correctamente, False si necesita fallback
    """
    try:
        full_id = await _ensure_entity_loaded(client, group_id)
        to_peer = await client.get_input_entity(full_id)
        
        # Obtener el peer origen del mensaje
        if from_peer is not None:
            source_peer = await client.get_input_entity(from_peer)
        else:
            # Extraer el chat_id del mensaje
            msg_chat_id = message.chat_id
            if msg_chat_id is None and hasattr(message, 'peer_id'):
                from telethon import utils
                msg_chat_id = utils.get_peer_id(message.peer_id)
            source_peer = await client.get_input_entity(msg_chat_id)
        
        random_id = random.randint(1, 2**63 - 1)
        
        await client(ForwardMessagesRequest(
            from_peer=source_peer,
            id=[message.id],
            to_peer=to_peer,
            top_msg_id=topic_id,
            random_id=[random_id]
        ))
        return True
        
    except Exception as e:
        error_msg = str(e).lower()
        if "chat_forwards_restricted" in error_msg or "protected" in error_msg:
            return False  # Necesita fallback (download + upload)
        logger.debug(f"⚠️ Forward a tema {topic_id} falló: {str(e)[:100]}")
        return False


async def send_file_to_topic(client, group_id, topic_id, file_bytes, 
                              caption=None, attributes=None, force_document=False,
                              mime_type=None, file_name=None):
    """
    Envía un archivo a un tema específico preservando su formato original.

    Args:
        client: Cliente de Telethon
        group_id: ID del supergrupo
        topic_id: ID del tema
        file_bytes: Bytes del archivo
        caption: Pie de foto/video opcional
        attributes: Lista de DocumentAttribute* del archivo original
        force_document: Si True, enviar como documento (no como media)
        mime_type: MIME type del archivo (ej: 'video/mp4', 'image/jpeg')
        file_name: Nombre del archivo original
    """
    full_id = await _ensure_entity_loaded(client, group_id)

    try:
        # Construir kwargs para send_file
        kwargs = {
            'entity': full_id,
            'file': file_bytes,
            'caption': caption,
            'reply_to': topic_id,
            'force_document': force_document,
        }
        
        # Agregar atributos si existen
        if attributes:
            kwargs['attributes'] = attributes
        
        # Agregar file_name si existe (ayuda a Telethon a detectar el tipo)
        if file_name:
            kwargs['file_name'] = file_name
        
        await client.send_file(**kwargs)
        
    except Exception as e:
        logger.error(f"❌ Error enviando archivo al tema {topic_id}: {str(e)[:100]}")
        raise


async def send_to_topic(client, group_id, topic_id, message):
    """
    Envía un mensaje de texto a un tema específico.
    """
    full_id = await _ensure_entity_loaded(client, group_id)

    try:
        await client.send_message(
            entity=full_id,
            message=message,
            reply_to=topic_id
        )
    except Exception as e:
        logger.error(f"❌ Error enviando al tema {topic_id}: {str(e)[:100]}")
        raise


async def send_welcome_message(client, group_id, topic_id, source_title, source_chat_id):
    """
    Envía mensaje de bienvenida al tema nuevo.
    """
    welcome_text = (
        f"📦 **Backup Iniciado**\n\n"
        f"👥 Grupo/Canal: {source_title}\n"
        f"🆔 ID: {source_chat_id}\n\n"
        f"💾 Los nuevos archivos multimedia se guardarán automáticamente en este tema."
    )

    try:
        await send_to_topic(client, group_id, topic_id, welcome_text)
    except Exception as e:
        logger.error(f"⚠️ No se pudo enviar mensaje de bienvenida: {str(e)[:100]}")


def extract_file_info(message):
    """
    Extrae información del archivo de un mensaje de Telegram.
    Retorna (file_name, mime_type, attributes, force_document, is_voice)
    
    Args:
        message: Mensaje de Telethon con media
    
    Returns:
        dict con: file_name, mime_type, attributes, force_document, is_voice
    """
    file_name = None
    mime_type = None
    attributes = None
    force_document = False
    is_voice = False
    
    if message.document:
        mime_type = message.document.mime_type
        attributes = list(message.document.attributes) if message.document.attributes else []
        
        # Extraer file_name de los atributos
        for attr in (message.document.attributes or []):
            if isinstance(attr, DocumentAttributeFilename):
                file_name = attr.file_name
                break
        
        # Detectar tipos especiales
        if message.voice:
            is_voice = True
            force_document = False
        elif message.video or message.video_note:
            force_document = False
        elif message.audio:
            force_document = False
        elif message.sticker:
            force_document = False
        else:
            # Documento genérico
            force_document = True
    elif message.photo:
        mime_type = 'image/jpeg'
        force_document = False
    
    return {
        'file_name': file_name,
        'mime_type': mime_type,
        'attributes': attributes,
        'force_document': force_document,
        'is_voice': is_voice,
    }

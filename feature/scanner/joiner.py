from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.errors import ChatAdminRequiredError, UsernameNotOccupiedError, UserNotParticipantError
import logging

logger = logging.getLogger(__name__)


async def join_from_link(client, link: str):
    """
    Intenta unirse a un chat/canal a partir de un enlace de Telegram.
    
    Soporta los siguientes formatos:
    - t.me/+abc123 (enlace de invitación privado)
    - t.me/joinchat/abc123 (enlace de invitación antiguo)
    - t.me/username (canal/grupo público)
    - @username (mención de canal/grupo)
    
    Args:
        client: Cliente de Telethon
        link: Enlace de Telegram en cualquier formato soportado
        
    Returns:
        Result de la petición de unión, o None si falla
    """
    if not link:
        logger.warning("❌ Enlace vacío")
        return None
    
    # Normalizar el enlace
    link = link.strip()
    
    # Convertir @username a formato t.me/username
    if link.startswith("@"):
        link = f"t.me/{link[1:]}"
    
    # Extraer la parte relevante del enlace
    try:
        # Quitar protocolo y dominio
        clean_link = link.replace("https://", "").replace("http://", "").replace("telegram.me", "t.me")
        
        # Extraer username o invite_code
        if clean_link.startswith("t.me/"):
            target = clean_link.replace("t.me/", "")
        else:
            target = clean_link
        
        # Si hay más segmentos (ej: t.me/username/123), tomar solo el primero
        if "/" in target:
            target = target.split("/")[0]
        
        if not target:
            logger.warning(f"❌ Enlace inválido: {link}")
            return None
        
        # 1. Intentar como enlace de invitación privado (+ o joinchat)
        if "joinchat" in target or target.startswith("+"):
            invite_code = target.replace("joinchat/", "").replace("+", "")
            logger.info(f"🔗 Uniéndose mediante invite code: {invite_code[:10]}...")
            return await client(ImportChatInviteRequest(invite_code))
        
        # 2. Intentar como username público
        else:
            username = target
            logger.info(f"🔗 Uniéndose a canal/grupo público: @{username}")
            return await client(JoinChannelRequest(username))
            
    except UsernameNotOccupiedError:
        logger.warning(f"⚠️ El username no existe o es un contacto privado")
        return None
    except ChatAdminRequiredError:
        logger.warning(f"⚠️ Se requieren permisos de administrador para unirse")
        return None
    except UserNotParticipantError:
        logger.warning(f"⚠️ No se pudo unir al canal (puede ser privado)")
        return None
    except ValueError as e:
        logger.error(f"❌ Error de valor: {str(e)[:100]}")
        return None
    except Exception as e:
        logger.error(f"❌ Error al unirse: {str(e)[:200]}")
        return None

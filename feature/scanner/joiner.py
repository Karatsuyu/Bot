from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest


async def join_from_link(client, link: str):
    """Intenta unirse a un chat/canal a partir de un enlace de Telegram."""
    if not link:
        return None

    if "joinchat" in link or "+" in link:
        # Enlace de invitación privada
        hash_ = link.split("/")[-1].replace("+", "")
        return await client(ImportChatInviteRequest(hash_))
    else:
        # Enlace público tipo https://t.me/username
        username = link.split("/")[-1]
        return await client(JoinChannelRequest(username))

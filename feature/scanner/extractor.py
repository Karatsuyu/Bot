import re

# Aceptar tanto enlaces con esquema (https://t.me/...) como sin él (t.me/...)
TG_LINK_REGEX = r"((?:https?://)?t\.me/[^\s]+)"


def extract_links(text: str) -> list[str]:
    """Extrae enlaces de Telegram de un texto"""
    if not text:
        return []
    return re.findall(TG_LINK_REGEX, text)

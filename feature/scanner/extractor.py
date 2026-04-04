import re

# Patrones para diferentes formatos de enlaces de Telegram
TG_LINK_REGEX = r"((?:https?://)?(?:t\.me|telegram\.me)/[^\s]+)"
USERNAME_REGEX = r"@([a-zA-Z0-9_]{5,32})"
TG_JOIN_REGEX = r"(?:joinchat/|\+)([a-zA-Z0-9_-]{6,})"


def extract_links(text: str) -> list:
    """
    Extrae enlaces de Telegram de un texto en múltiples formatos:
    - https://t.me/+abc123
    - t.me/+abc123
    - https://t.me/username
    - t.me/username
    - https://telegram.me/...
    - @username (menciones)
    - Enlaces a mensajes específicos: t.me/username/123
    
    Returns:
        list: Lista de enlaces normalizados en formato t.me/...
    """
    if not text:
        return []
    
    found_links = set()  # Usar set para evitar duplicados
    
    # 1. Extraer enlaces t.me y telegram.me
    url_matches = re.findall(TG_LINK_REGEX, text, re.IGNORECASE)
    for match in url_matches:
        link = match.strip()
        
        # Quitar protocolo
        link = link.replace("https://", "").replace("http://", "")
        
        # Normalizar dominio
        link = link.replace("telegram.me/", "t.me/")
        
        # Asegurar que empieza con t.me/
        if not link.startswith("t.me/"):
            link = "t.me/" + link
        
        # Si es enlace a mensaje específico (t.me/username/123), extraer solo el canal
        parts = link.split("/")
        if len(parts) > 2:
            # parts = ['t.me', 'username', '123']
            username = parts[1]
            # Verificar si el último segmento es un número (ID de mensaje)
            if parts[-1].isdigit():
                link = f"t.me/{username}"
            else:
                link = f"t.me/{username}"
        
        found_links.add(link)
    
    # 2. Extraer menciones @username
    username_matches = re.findall(USERNAME_REGEX, text)
    for username in username_matches:
        # Filtrar usernames que parezcan contactos personales o inválidos
        if not _is_personal_contact(username):
            found_links.add(f"t.me/{username}")
    
    # 3. Extraer enlaces de invitación (joinchat o +)
    join_matches = re.findall(TG_JOIN_REGEX, text, re.IGNORECASE)
    for invite_code in join_matches:
        if invite_code:
            found_links.add(f"t.me/+{invite_code}")
    
    # Convertir a lista y filtrar enlaces inválidos
    result = []
    for link in found_links:
        if _is_valid_telegram_link(link):
            result.append(link)
    
    return result


def _is_personal_contact(username: str) -> bool:
    """
    Intenta detectar si un username es probablemente un contacto personal
    en lugar de un canal/grupo público.
    
    Criterios para considerar como contacto personal:
    - Usernames muy cortos (< 5 caracteres después de filtrar)
    - Patrones comunes de nombres personales
    """
    # Ya filtramos por longitud en el regex (5-32 caracteres)
    # Pero podemos añadir más lógica si es necesario
    return False  # Por defecto, asumimos que es un canal/grupo


def _is_valid_telegram_link(link: str) -> bool:
    """
    Valida que un enlace sea un enlace de Telegram válido
    
    Returns:
        bool: True si es válido, False si es contacto personal o inválido
    """
    if not link:
        return False
    
    # Ignorar enlaces a carpetas (addlist)
    if "addlist" in link.lower():
        return False
    
    # Ignorar enlaces que parezcan contactos personales
    # (esto es opcional, se puede ajustar según necesidad)
    personal_patterns = [
        r"t\.me/[a-z]{1,4}$",  # Usernames muy cortos (1-4 letras)
    ]
    
    for pattern in personal_patterns:
        if re.match(pattern, link, re.IGNORECASE):
            return False
    
    return True

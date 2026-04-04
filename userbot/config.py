import os
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
CONTROL_BOT_ID = os.getenv("CONTROL_BOT_ID", "me")

# Límites de escaneo / join controlado
SCAN_LIMIT_PER_RUN = int(os.getenv("SCAN_LIMIT_PER_RUN", "200"))
JOIN_LIMIT_PER_RUN = int(os.getenv("JOIN_LIMIT_PER_RUN", "10"))
JOIN_DELAY_SECONDS = int(os.getenv("JOIN_DELAY_SECONDS", "30"))

# Configuración de backup en modo tema (topic)
BACKUP_GROUP_ID = os.getenv("BACKUP_GROUP_ID")  # ID del supergrupo con temas para backup
BACKUP_MODE = os.getenv("BACKUP_MODE", "channel")  # 'channel' | 'topic'

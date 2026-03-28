from telethon import TelegramClient
from telethon.sessions import SQLiteSession
from userbot.config import API_ID, API_HASH
from userbot.watcher import register_handlers
from database.db import init_db
import asyncio
import sqlite3
import os

# Cliente global para acceso desde otros módulos
client = None

def get_client():
    """Retorna el cliente de Telethon"""
    return client

async def preload_dialogs(client):
    """Precarga diálogos después de conectar"""
    await asyncio.sleep(3)
    print("🔄 Precargando diálogos...")
    try:
        dialogs_count = 0
        async for dialog in client.iter_dialogs(limit=100):
            dialogs_count += 1
        print(f"✅ {dialogs_count} diálogos precargados")
    except Exception as e:
        print(f"⚠️ Error precargando diálogos: {str(e)[:100]}")

def main():
    """Función principal del userbot"""
    global client
    
    print("🚀 Iniciando userbot...")
    
    # Inicializar base de datos
    init_db()
    
    # Configurar sesión SQLite con WAL mode para evitar locks
    session_file = "userbot_session.session"
    if os.path.exists(session_file):
        try:
            conn = sqlite3.connect(session_file, timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=30000")
            conn.commit()
            conn.close()
            print("✅ Sesión configurada en modo WAL")
        except Exception as e:
            print(f"⚠️ Error configurando sesión: {str(e)[:100]}")
    
    # Crear cliente de Telegram
    client = TelegramClient("userbot_session", API_ID, API_HASH)
    
    # Registrar handlers
    register_handlers(client)
    
    print("✅ Userbot iniciado correctamente")
    print("📝 Usa /scan para escanear todos tus grupos y canales actuales")
    
    # Iniciar cliente
    client.start()
    
    # Precargar diálogos después de conectar
    client.loop.create_task(preload_dialogs(client))
    
    client.run_until_disconnected()

if __name__ == "__main__":
    main()

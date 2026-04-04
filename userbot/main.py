from telethon import TelegramClient
from telethon.sessions import SQLiteSession
from userbot.config import API_ID, API_HASH, BACKUP_GROUP_ID
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
    
    # Precargar supergrupo de backups si está configurado
    if BACKUP_GROUP_ID:
        await preload_backup_group(client, BACKUP_GROUP_ID)

async def preload_backup_group(client, group_id):
    """
    Precarga el supergrupo de backups para evitar errores de entidad
    """
    print(f"📦 Precargando supergrupo de backups: {group_id}...")
    try:
        # Normalizar ID
        id_str = str(group_id)
        if id_str.startswith("-100"):
            normalized_id = int(id_str[4:])
        elif id_str.startswith("100"):
            normalized_id = int(id_str[3:])
        else:
            normalized_id = int(id_str)
        
        # Intentar obtener la entidad
        try:
            entity = await client.get_entity(normalized_id)
            print(f"✅ Supergrupo encontrado: {getattr(entity, 'title', 'Desconocido')}")
            return
        except Exception:
            pass
        
        # Intentar con -100prefijo
        try:
            full_id = int(f"-100{normalized_id}")
            entity = await client.get_entity(full_id)
            print(f"✅ Supergrupo encontrado: {getattr(entity, 'title', 'Desconocido')}")
            return
        except Exception:
            pass
        
        # Buscar en diálogos
        print("🔍 Buscando supergrupo en diálogos...")
        async for dialog in client.iter_dialogs():
            dialog_id = str(dialog.id).replace("-100", "")
            if dialog_id == str(normalized_id):
                print(f"✅ Supergrupo encontrado en diálogos: {getattr(dialog.entity, 'title', 'Desconocido')}")
                return
        
        print(f"⚠️ No se encontró el supergrupo {group_id}. Asegúrate de que el userbot esté unido al grupo de backups.")
        
    except Exception as e:
        print(f"⚠️ Error precargando supergrupo de backups: {str(e)[:100]}")

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

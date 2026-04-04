"""
Script para obtener el ID del supergrupo Backups
"""
import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

async def main():
    client = TelegramClient('session_get_id', API_ID, API_HASH)
    await client.start()
    
    print("📋 Listando todos tus diálogos...\n")
    
    async for dialog in client.iter_dialogs():
        try:
            if dialog.is_group or dialog.is_channel:
                chat_type = "📢 Canal" if dialog.is_channel else "👥 Grupo"
                print(f"{chat_type}: {dialog.name}")
                print(f"   ID: {dialog.id}")
                print()
        except Exception as e:
            pass
    
    await client.disconnect()
    
    print("\n" + "="*60)
    print("💡 Busca el supergrupo 'Backups' en la lista y copia su ID")
    print("   Ese ID debes ponerlo en BACKUP_GROUP_ID en el .env")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())

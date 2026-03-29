import asyncio
import logging
import uvicorn
import os
import sqlite3
from aiogram import Bot, Dispatcher
from telethon import TelegramClient

from userbot.config import API_ID, API_HASH
from bot.config import BOT_TOKEN
from database.db import init_db

# Evitar imports circulares antes de setear el cliente global
import userbot.main
from userbot.main import register_handlers as userbot_handlers, preload_dialogs
from bot.main import set_bot_commands
from bot.handlers import register_handlers as bot_handlers
from web.app import app

# Configuración básica de logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AmeBot-Runner")

async def main():
    logger.info("🚀 Iniciando sistema completo Ame Bot (Web + Bot + Userbot)...")
    
    # 1. Inicializar base de datos
    init_db()
    
    # 2. Configurar base de datos SQLite del Userbot (WAL + Timeout)
    session_file = "userbot_session.session"
    if os.path.exists(session_file):
        try:
            conn = sqlite3.connect(session_file, timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=30000")
            conn.commit()
            conn.close()
            logger.info("✅ Sesión de Telethon configurada en modo WAL")
        except Exception as e:
            logger.error(f"⚠️ Error configurando sesión: {str(e)[:100]}")
            
    # --- Configurar componentes ---
    
    # Userbot (Telethon)
    client = TelegramClient("userbot_session", API_ID, API_HASH)
    # INYECTAR el cliente globalmente para que bot.handlers.py pueda importarlo via `get_userbot_client()`
    userbot.main.client = client
    userbot_handlers(client)
    
    # Bot Regular (Aiogram)
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    await set_bot_commands(bot)
    bot_handlers(dp)
    
    # Web Dashboard (FastAPI / Uvicorn)
    config = uvicorn.Config(app=app, host="0.0.0.0", port=8000, loop="asyncio")
    server = uvicorn.Server(config)
    
    # --- Iniciar ejecución ---
    
    # Iniciar conexión de Telethon
    await client.start()
    client.loop.create_task(preload_dialogs(client))
    
    logger.info("✅ Todos los servicios listos para iniciar.")
    logger.info("🌐 Panel Web disponible en: http://localhost:8000")
    
    # Agrupar las corrutinas principales
    try:
        await asyncio.gather(
            dp.start_polling(bot, skip_updates=True),
            client.run_until_disconnected(),
            server.serve()
        )
    except asyncio.CancelledError:
        logger.info("🛑 Deteniendo servicios...")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Sistema detenido de manera segura por el usuario.")

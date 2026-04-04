import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from bot.config import BOT_TOKEN
from bot.handlers import register_handlers
from database.db import init_db

async def set_bot_commands(bot: Bot):
    """Configura el menú de comandos del bot"""
    commands = [
        BotCommand(command="start", description="🏠 Inicio y ayuda"),
        BotCommand(command="help", description="❓ Ayuda"),
        BotCommand(command="listar", description="📋 Listar todas las entidades"),
        BotCommand(command="sinlink", description="🔗 Entidades sin enlace"),
        BotCommand(command="categorias", description="📂 Ver por categorías"),
        BotCommand(command="stats", description="📊 Estadísticas"),
        BotCommand(command="scan", description="🔍 Escanear grupos"),
        BotCommand(command="scanchat", description="🔍 Escanear un chat concreto"),
        BotCommand(command="addlink", description="➕ Agregar enlace"),
        BotCommand(command="unir_guardados", description="🔗 Unirse a enlaces guardados"),
        BotCommand(command="escanear_y_unir", description="🔍 Escanear y unir a enlaces"),
        BotCommand(command="backup_lista", description="📦 Lista de grupos para backup"),
        BotCommand(command="backup_activar", description="✅ Activar backup (canal)"),
        BotCommand(command="backup_desactivar", description="❌ Desactivar backup"),
        BotCommand(command="backup_historial", description="📚 Descargar historial"),
        BotCommand(command="backup_estado", description="📊 Estado de backups"),
        BotCommand(command="backup_info", description="ℹ️ Info sobre backups"),
        BotCommand(command="backup_topic_activar", description="📌 Activar backup (tema)"),
        BotCommand(command="backup_topic_info", description="ℹ️ Info backup tema"),
        BotCommand(command="joinlinks", description="🔗 Procesar enlaces encontrados"),
        BotCommand(command="links_chat", description="🔗 Ver enlaces por chat"),
        BotCommand(command="links_estado", description="🔗 Ver enlaces por estado"),
        BotCommand(command="linkrule_add", description="⚙️ Añadir regla de enlaces"),
        BotCommand(command="links_resumen", description="📊 Resumen de enlaces"),
        BotCommand(command="directorio", description="📂 Directorio paginado de enlaces"),
    ]
    await bot.set_my_commands(commands)

async def main():
    """Función principal del bot"""
    print("🤖 Iniciando bot de control...")
    
    # Inicializar base de datos
    init_db()
    
    # Crear bot y dispatcher
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # Configurar menú de comandos
    await set_bot_commands(bot)
    
    # Registrar handlers
    register_handlers(dp)
    
    print("✅ Bot iniciado correctamente")
    print("📝 El bot está listo para recibir comandos")
    
    # Iniciar polling
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())

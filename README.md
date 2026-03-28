# 🤖 Ame Bot - Bot de Telegram con Detección Automática

Bot profesional de Telegram con sistema de detección automática de grupos y canales, usando Userbot para captura y Bot regular para control.

## 📋 Características

✅ **Detección automática** al entrar a grupos/canales  
✅ **Clasificación por tipo** (grupo, canal, bot)  
✅ **Persistencia total** en PostgreSQL  
✅ **Historial completo** incluso si sales del grupo  
✅ **Separación Userbot / Bot** para máxima funcionalidad  
✅ **Escalable y profesional**  

## 🚀 Instalación

### 1. Crear entorno virtual

```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 2. Instalar dependencias

```powershell
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

Edita el archivo `.env` con tus credenciales:

```env
API_ID=tu_api_id                    # Obtén desde https://my.telegram.org/apps
API_HASH=tu_api_hash                # Obtén desde https://my.telegram.org/apps
BOT_TOKEN=tu_bot_token              # Obtén desde @BotFather
DATABASE_URL=postgresql://user:password@localhost/telegram_archive
```

### 4. Configurar PostgreSQL

Instala PostgreSQL y crea la base de datos:

```sql
CREATE DATABASE telegram_archive;
CREATE USER tu_usuario WITH PASSWORD 'tu_password';
GRANT ALL PRIVILEGES ON DATABASE telegram_archive TO tu_usuario;
```

### 5. Inicializar base de datos

```powershell
python init_db.py
```

## 🎮 Uso

### Ejecutar el Userbot (Detección Automática)

```powershell
python run_userbot.py
```

El userbot detectará automáticamente cuando te unan a grupos o canales.

**Comandos del userbot:**
- `/scan` - Escanea todos tus grupos y canales actuales

### Ejecutar el Bot de Control

```powershell
python run_bot.py
```

**Comandos del bot:**
- `/start` - Mensaje de bienvenida
- `/listar` - Lista todas las entidades guardadas
- `/categorias` - Muestra entidades por categoría
- `/stats` - Estadísticas del sistema
- `/help` - Ayuda

## 📁 Estructura del Proyecto

```
Ame Bot/
├── database/              # Capa de base de datos
│   ├── __init__.py
│   ├── db.py             # Configuración SQLAlchemy
│   └── models.py         # Modelos de datos
│
├── userbot/              # Userbot de detección
│   ├── __init__.py
│   ├── config.py         # Configuración
│   ├── watcher.py        # Manejadores de eventos
│   └── main.py           # Punto de entrada
│
├── bot/                  # Bot de control
│   ├── __init__.py
│   ├── config.py         # Configuración
│   ├── handlers.py       # Comandos del bot
│   └── main.py           # Punto de entrada
│
├── .env                  # Variables de entorno (NO COMPARTIR)
├── .env.example          # Ejemplo de variables
├── .gitignore           # Archivos ignorados por git
├── requirements.txt      # Dependencias del proyecto
├── init_db.py           # Script de inicialización DB
├── run_userbot.py       # Ejecutar userbot
├── run_bot.py           # Ejecutar bot
└── README.md            # Este archivo
```

## 🗄️ Modelo de Datos

**TelegramEntity**
- `id` - ID interno (autoincremental)
- `telegram_id` - ID de Telegram (único)
- `title` - Título del grupo/canal
- `username` - Username (si es público)
- `invite_link` - Link de invitación
- `entity_type` - Tipo (group/channel/bot)
- `category` - Categoría personalizable
- `is_private` - Si es privado o público
- `last_seen` - Última vez visto

## 🔧 Tecnologías

- **Telethon** - Librería para Userbot
- **Aiogram** - Framework para Bot de Telegram
- **SQLAlchemy** - ORM para base de datos
- **PostgreSQL** - Base de datos
- **Python-dotenv** - Gestión de variables de entorno

## 📝 Notas Importantes

1. **API_ID y API_HASH**: Obtén estas credenciales en https://my.telegram.org/apps
2. **BOT_TOKEN**: Crea un bot con @BotFather en Telegram
3. **Userbot vs Bot**: El userbot usa tu cuenta personal, el bot usa una cuenta de bot
4. **Permisos**: El userbot necesita estar en los grupos para detectarlos
5. **Privacidad**: Nunca compartas tus credenciales o archivos `.session`

## 🛡️ Seguridad

- Nunca subas el archivo `.env` a repositorios públicos
- Los archivos `.session` contienen información sensible
- Usa contraseñas fuertes para la base de datos
- Mantén las dependencias actualizadas

## 🚀 Ejecución en Producción

Para mantener los bots ejecutándose en segundo plano, considera usar:
- **PM2** (para Node.js, pero funciona con Python)
- **systemd** (Linux)
- **nohup** o **screen** (Unix)
- **Task Scheduler** (Windows)

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o pull request.

## 📧 Soporte

Para preguntas o problemas, abre un issue en el repositorio.

---

**Desarrollado con ❤️ para la comunidad de Telegram**

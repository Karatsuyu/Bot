# Backup en Modo Tema (Topic Mode)

## 📦 Descripción

Este módulo permite realizar backups de multimedia en **temas** dentro de un supergrupo, en lugar de crear canales individuales para cada grupo.

## 🎯 Características

- ✅ **Mismo destino para todos**: Un solo supergrupo con múltiples temas
- ✅ **Más organizado**: Un tema por grupo/canal respaldado
- ✅ **Persistente**: Los mensajes se guardan aunque se vacíe el chat original
- ✅ **Coexiste con backup por canales**: Puedes usar ambos modos simultáneamente
- ✅ **Rate limiting**: Delay entre mensajes para evitar bans

## 📋 Requisitos

1. **Supergrupo con temas activados**:
   - Crear un grupo en Telegram
   - Convertirlo a supergrupo
   - Activar la opción "Temas" en configuración
   - Hacer el grupo privado (recomendado)

2. **Permisos del userbot**:
   - Añadir el userbot como administrador del supergrupo
   - Permiso para crear temas
   - Permiso para enviar mensajes

3. **Configuración en `.env`**:
   ```env
   BACKUP_GROUP_ID=-1001234567890  # ID del supergrupo
   ```

## 🚀 Configuración

### Paso 1: Crear el supergrupo

1. Abre Telegram y crea un nuevo grupo
2. Añade al menos un miembro (puedes eliminarlo después)
3. Ve a Configuración del grupo → Tipo de grupo → **Supergrupo**
4. Activa **Temas** en las opciones
5. Haz el grupo privado (opcional pero recomendado)

### Paso 2: Obtener el ID del supergrupo

1. Añade el bot `@RawDataBot` o `@GetMyIDBot` al supergrupo
2. El bot te dará el ID (ej: `-1001234567890`)
3. Elimina el bot del supergrupo

### Paso 3: Configurar el userbot

1. Añade tu userbot (la cuenta que ejecuta el bot) como administrador
2. Configura en `.env`:
   ```env
   BACKUP_GROUP_ID=-1001234567890
   ```

### Paso 4: Actualizar base de datos

Ejecuta el script para añadir las nuevas columnas:

```bash
python add_topic_columns.py
```

## 📝 Comandos

### Activar backup en modo tema

```
/backup_topic_activar <ID>
```

Ejemplo:
```
/backup_topic_activar -1001234567890
```

### Ver información del modo tema

```
/backup_topic_info
```

### Comandos existentes (siguen funcionando)

- `/backup_activar <ID>` - Backup en modo canal (tradicional)
- `/backup_estado` - Ver todos los backups (canales y temas)
- `/backup_desactivar <ID>` - Desactivar backup
- `/backup_historial <ID>` - Descargar historial completo

## 🔄 Flujo de Funcionamiento

```
1. Usuario: /backup_topic_activar -1001234567890
2. Bot verifica BACKUP_GROUP_ID en .env
3. Bot crea un tema en el supergrupo: "📦 Nombre del Grupo"
4. Guarda topic_id en backup_mappings
5. watcher.py detecta nuevos mensajes con multimedia
6. Reenvía al tema correspondiente usando reply_to=topic_id
7. Los mensajes persisten en el tema aunque se borren del original
```

## 📊 Base de Datos

### Nuevas columnas en `backup_mappings`:

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `topic_id` | BIGINT | ID del tema en el supergrupo |
| `storage_mode` | TEXT | 'channel' o 'topic' |
| `last_message_id` | BIGINT | Último mensaje procesado (para evitar duplicados) |

## 🏗️ Arquitectura

```
userbot/backup_topic/
├── __init__.py          # Exporta funciones públicas
├── topics.py            # Creación y gestión de temas
├── sender.py            # Envío de mensajes a temas
└── service.py           # Servicio principal de backup

Archivos modificados:
├── database/models.py           # Nuevas columnas
├── userbot/config.py            # BACKUP_GROUP_ID
├── userbot/watcher.py           # Handler backup_media_topic_handler
├── userbot/backup_manager.py    # Función get_dest_topic()
├── bot/handlers.py              # Comandos backup_topic_*
├── bot/main.py                  # Menú de comandos
└── .env.example                 # Variables de entorno
```

## 💡 Consejos

1. **Límite de temas**: Telegram permite ~100-200 temas por supergrupo
2. **Nombre del tema**: Se genera automáticamente como "📦 Nombre del Grupo"
3. **Backup dual**: Puedes tener el mismo grupo en modo canal Y modo tema
4. **Rate limiting**: El sistema incluye delays automáticos para evitar bans
5. **Protección de contenido**: Funciona con canales protegidos (descarga y re-subida)

## ⚠️ Consideraciones

- **No eliminar el supergrupo**: Si lo eliminas, pierdes todos los backups
- **Permisos de administrador**: El userbot necesita permisos para crear temas
- **BACKUP_GROUP_ID obligatorio**: Sin esto, el modo tema no funciona
- **Espacio en Telegram**: Los backups cuentan en tu cuota de Telegram

## 🐛 Solución de Problemas

### Error: "BACKUP_GROUP_ID no configurado"
- Verifica que `.env` tenga `BACKUP_GROUP_ID=-100XXXXXXXXXX`
- Reinicia el bot después de cambiar el .env

### Error: "No se pudo crear el tema"
- Verifica que el supergrupo tenga **Temas activados**
- Verifica que el userbot sea **administrador**
- Verifica que no hayas alcanzado el límite de temas

### Error: "Flood wait" o bans
- El sistema ya incluye rate limiting
- Si persiste, aumenta `JOIN_DELAY_SECONDS` en `.env`

## 📞 Soporte

Para reportar errores o sugerencias, revisa los logs en la terminal del userbot.

# 📦 Funcionalidad de Backup Automático - Guía de Uso

## 🎯 ¿Qué hace?

El sistema ahora puede **respaldar automáticamente** toda la multimedia (fotos, videos, documentos, etc.) de grupos/canales específicos en canales privados que actúan como almacenamiento en Telegram.

### ✅ Ventajas
- ✔️ No ocupa espacio en tu disco
- ✔️ Acceso desde cualquier dispositivo
- ✔️ Calidad original preservada
- ✔️ Telegram actúa como CDN
- ✔️ 1 canal privado por cada grupo origen

### ⚠️ Limitaciones
- ❌ Solo funciona si ya estás en el grupo origen
- ❌ No funciona con "Protected Content" activado
- ❌ Respeta límites de Telegram

---

## 🚀 Comandos Disponibles (en el Userbot)

### 1️⃣ `/backup_activar`

**Dónde usar:** Envía este comando en el grupo/canal que quieres respaldar

**Qué hace:**
- Crea automáticamente un canal privado con nombre `📦 Backup - [Nombre del Grupo]`
- Configura el backup automático para ese grupo
- Todos los archivos multimedia nuevos se guardarán automáticamente

**Ejemplo:**
```
/backup_activar
```

**Respuesta esperada:**
```
✅ Backup activado
📦 Canal creado: 📦 Backup - Grupo Anime
💾 Los nuevos archivos multimedia se guardarán automáticamente
```

---

### 2️⃣ `/backup_desactivar`

**Dónde usar:** Envía este comando en el grupo que quieres pausar

**Qué hace:**
- Desactiva el backup automático
- El canal de backup sigue existiendo pero no se guardarán archivos nuevos

**Ejemplo:**
```
/backup_desactivar
```

**Respuesta esperada:**
```
✅ Backup desactivado
📦 Canal: 📦 Backup - Grupo Anime
💡 El canal sigue existiendo pero no se guardarán nuevos archivos
```

---

### 3️⃣ `/backup_estado`

**Dónde usar:** 
- En un grupo específico → muestra el estado de ese grupo
- En tu chat privado → muestra todos los backups configurados

**Qué muestra:**
- Estado (activo/pausado)
- Nombre del canal de backup
- Cantidad de archivos respaldados

**Ejemplo (en un grupo):**
```
/backup_estado
```

**Respuesta esperada:**
```
📊 Estado del backup:

🏷️ Estado: ✅ ACTIVO
📦 Canal: 📦 Backup - Grupo Anime
📨 Archivos respaldados: 47
```

**Ejemplo (en privado):**
```
/backup_estado
```

**Respuesta esperada:**
```
📊 Backups configurados (3):

✅ 📦 Backup - Grupo Anime
   📨 47 archivos

✅ 📦 Backup - Memes Random
   📨 23 archivos

⏸️ 📦 Backup - Canal Música
   📨 15 archivos
```

---

## 🔄 Flujo de Trabajo Típico

### Primer uso:

1. **Escanea tus grupos:**
   ```
   /scan
   ```

2. **Ve a un grupo que quieras respaldar:**
   - Abre el grupo en Telegram
   - Envía `/backup_activar`
   - Espera confirmación

3. **Verifica que funcione:**
   - Espera a que alguien envíe una foto/video en ese grupo
   - Ve a tus "Canales" en Telegram
   - Busca el canal `📦 Backup - [Nombre del Grupo]`
   - Verifica que el archivo se guardó automáticamente

4. **Revisa el estado:**
   ```
   /backup_estado
   ```

---

## 🏗️ Arquitectura Técnica

```
┌─────────────────────────┐
│  GRUPO/CANAL ORIGEN     │
│  (donde estás unido)    │
└───────────┬─────────────┘
            │
            │ Nuevo archivo multimedia detectado
            │
            ▼
┌─────────────────────────┐
│  USERBOT (tu cuenta)    │
│  ├─ Escucha mensajes    │
│  ├─ Detecta multimedia  │
│  └─ Reenvía automát.    │
└───────────┬─────────────┘
            │
            │ Reenviar mensaje
            │
            ▼
┌─────────────────────────┐
│  CANAL DESTINO PRIVADO  │
│  📦 Backup - Grupo X    │
│  (creado automático)    │
└─────────────────────────┘
```

---

## 🗄️ Base de Datos

Nueva tabla: `backup_mappings`

| Campo | Descripción |
|-------|-------------|
| `source_chat_id` | ID del grupo origen |
| `dest_chat_id` | ID del canal de backup |
| `dest_chat_title` | Nombre del canal |
| `enabled` | true/false (activo/pausado) |
| `message_count` | Contador de archivos |

---

## 💡 Tips y Mejores Prácticas

### ✅ Hacer:
- Activar backup solo en grupos con contenido valioso
- Verificar periódicamente con `/backup_estado`
- Crear backups de grupos antes de que sean eliminados
- Usar nombres descriptivos en tus grupos

### ❌ Evitar:
- Activar backup en grupos muy activos (miles de archivos por día)
- Usar en grupos con contenido sensible sin precaución
- Abusar del sistema (Telegram puede limitarte)

---

## 🐛 Troubleshooting

### Problema: "No se pudo crear el canal de backup"
**Solución:** Telegram limita la creación de canales. Espera unos minutos e intenta de nuevo.

### Problema: Los archivos no se guardan automáticamente
**Posibles causas:**
1. El grupo tiene "Protected Content" activado
2. El backup está pausado (usa `/backup_activar`)
3. El userbot no está corriendo (verifica los procesos)

### Problema: "Este grupo no tiene backup configurado"
**Solución:** Usa `/backup_activar` primero en ese grupo.

---

## 📝 Comandos del Bot de Control

Los comandos existentes (`/listar`, `/sinlink`, `/stats`, `/addlink`) siguen funcionando igual.

**Importante:** El backup es una funcionalidad del **userbot**, no del bot de control.

---

## 🔐 Seguridad y Privacidad

- Los canales de backup son **privados** por defecto
- Solo tú tienes acceso a ellos
- Los archivos no se descargan a tu computadora
- Todo permanece en Telegram

---

## 🚨 Importante

Esta funcionalidad:
- ✅ Respeta los términos de servicio de Telegram
- ✅ No bypasea restricciones de contenido protegido
- ✅ Solo funciona con contenido al que ya tienes acceso
- ⚠️ Úsala responsablemente

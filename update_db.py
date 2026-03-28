"""Script para actualizar la base de datos con la nueva tabla de backup_mappings"""
from database.db import engine
from database.models import Base

print("🔄 Actualizando base de datos...")
print("📋 Creando tabla backup_mappings si no existe...")

# Crear solo las tablas nuevas (no borra las existentes)
Base.metadata.create_all(bind=engine)

print("✅ Base de datos actualizada correctamente")
print("📊 La tabla 'backup_mappings' está lista para usar")

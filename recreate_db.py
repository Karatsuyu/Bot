"""
Script para recrear la base de datos con el esquema corregido
"""
from database.db import engine
from database.models import Base
import sqlalchemy

# Eliminar todas las tablas existentes
print("🗑️ Eliminando tablas existentes...")
Base.metadata.drop_all(bind=engine)

# Crear las tablas con el nuevo esquema
print("🗄️ Creando tablas con el esquema corregido...")
Base.metadata.create_all(bind=engine)

print("✅ Base de datos recreada correctamente con BigInteger para telegram_id")

"""
Script de inicialización de la base de datos
Ejecuta este script para crear las tablas necesarias
"""
from database.db import init_db

if __name__ == "__main__":
    print("🗄️ Inicializando base de datos...")
    init_db()
    print("✅ Base de datos lista para usar")

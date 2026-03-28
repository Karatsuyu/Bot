"""Script para agregar la columna historial_pending a la tabla backup_mappings"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Obtener credenciales de la base de datos
db_url = os.getenv("DATABASE_URL")
# Parsear la URL: postgresql://user:password@host:port/database
parts = db_url.replace("postgresql://", "").split("@")
user_pass = parts[0].split(":")
host_db = parts[1].split("/")
host_port = host_db[0].split(":")

user = user_pass[0]
password = user_pass[1]
host = host_port[0]
port = host_port[1]
database = host_db[1]

print("🔧 Conectando a la base de datos...")

try:
    conn = psycopg2.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password
    )
    
    cur = conn.cursor()
    
    print("📋 Agregando columna historial_pending...")
    
    # Agregar la columna si no existe
    cur.execute("""
        ALTER TABLE backup_mappings 
        ADD COLUMN IF NOT EXISTS historial_pending BOOLEAN DEFAULT FALSE;
    """)
    
    conn.commit()
    
    print("✅ Columna agregada correctamente")
    
    cur.close()
    conn.close()
    
    print("✅ Base de datos actualizada")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")

"""
Script para actualizar la base de datos con las nuevas columnas para backup en modo tema
"""
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ Error: DATABASE_URL no configurada en .env")
    exit(1)

import psycopg2

def update_database():
    """Añade las nuevas columnas a la tabla backup_mappings"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("📋 Actualizando tabla backup_mappings...")
        
        # Columna topic_id
        try:
            cur.execute("""
                ALTER TABLE backup_mappings 
                ADD COLUMN IF NOT EXISTS topic_id BIGINT
            """)
            print("✅ Columna 'topic_id' añadida")
        except Exception as e:
            print(f"⚠️ Columna 'topic_id': {str(e)[:100]}")
        
        # Columna storage_mode
        try:
            cur.execute("""
                ALTER TABLE backup_mappings 
                ADD COLUMN IF NOT EXISTS storage_mode TEXT DEFAULT 'channel'
            """)
            print("✅ Columna 'storage_mode' añadida")
        except Exception as e:
            print(f"⚠️ Columna 'storage_mode': {str(e)[:100]}")
        
        # Columna last_message_id
        try:
            cur.execute("""
                ALTER TABLE backup_mappings 
                ADD COLUMN IF NOT EXISTS last_message_id BIGINT
            """)
            print("✅ Columna 'last_message_id' añadida")
        except Exception as e:
            print(f"⚠️ Columna 'last_message_id': {str(e)[:100]}")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print("\n📊 Base de datos actualizada correctamente")
        print("💡 Las nuevas columnas permiten el backup en modo tema (topic)")
        
    except Exception as e:
        print(f"❌ Error actualizando la base de datos: {str(e)}")

if __name__ == "__main__":
    update_database()

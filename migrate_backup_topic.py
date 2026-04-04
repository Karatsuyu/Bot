"""
Script para actualizar la base de datos con las nuevas columnas para backup en modo tema
Ejecutar después de hacer pull de los cambios
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ Error: DATABASE_URL no configurada en .env")
    sys.exit(1)

try:
    import psycopg2
except ImportError:
    print("❌ Error: psycopg2 no está instalado")
    print("💡 Ejecuta: pip install psycopg2-binary")
    sys.exit(1)


def update_database():
    """Añade las nuevas columnas a la tabla backup_mappings si no existen"""
    conn = None
    try:
        print("🔗 Conectando a la base de datos...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("📋 Actualizando tabla backup_mappings...\n")
        
        # Columna topic_id
        try:
            cur.execute("""
                ALTER TABLE backup_mappings 
                ADD COLUMN IF NOT EXISTS topic_id BIGINT
            """)
            print("✅ Columna 'topic_id' añadida o ya existe")
        except Exception as e:
            print(f"⚠️ Columna 'topic_id': {str(e)[:100]}")
        
        # Columna storage_mode con valor por defecto 'channel'
        try:
            cur.execute("""
                ALTER TABLE backup_mappings 
                ADD COLUMN IF NOT EXISTS storage_mode TEXT DEFAULT 'channel'
            """)
            print("✅ Columna 'storage_mode' añadida o ya existe")
        except Exception as e:
            print(f"⚠️ Columna 'storage_mode': {str(e)[:100]}")
        
        # Columna last_message_id
        try:
            cur.execute("""
                ALTER TABLE backup_mappings 
                ADD COLUMN IF NOT EXISTS last_message_id BIGINT
            """)
            print("✅ Columna 'last_message_id' añadida o ya existe")
        except Exception as e:
            print(f"⚠️ Columna 'last_message_id': {str(e)[:100]}")
        
        # Actualizar registros existentes para que tengan storage_mode='channel'
        try:
            cur.execute("""
                UPDATE backup_mappings 
                SET storage_mode = 'channel' 
                WHERE storage_mode IS NULL
            """)
            print("✅ Registros existentes actualizados a 'channel'")
        except Exception as e:
            print(f"⚠️ Actualización de registros: {str(e)[:100]}")
        
        conn.commit()
        cur.close()
        
        print("\n" + "="*50)
        print("📊 Base de datos actualizada correctamente")
        print("="*50)
        print("\n💡 Las nuevas columnas permiten:")
        print("   • Backup en modo tema (topic)")
        print("   • Backup en modo canal (channel) - tradicional")
        print("   • Ambos modos pueden coexistir")
        print("\n📝 Próximos pasos:")
        print("   1. Configura BACKUP_GROUP_ID en .env")
        print("   2. Crea un supergrupo con temas activados")
        print("   3. Usa /backup_topic_activar <ID> para activar")
        
    except psycopg2.OperationalError as e:
        print(f"\n❌ Error de conexión: {str(e)}")
        print("💡 Verifica que DATABASE_URL sea correcta")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error actualizando la base de datos: {str(e)}")
        if conn:
            conn.rollback()
        sys.exit(1)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    print("="*50)
    print("🔄 Migración de Base de Datos - Backup Topic Mode")
    print("="*50)
    print()
    update_database()

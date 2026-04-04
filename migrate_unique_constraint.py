"""
Script para migrar la base de datos:
- Quitar UNIQUE constraint de source_chat_id
- Agregar UNIQUE constraint compuesto (source_chat_id, storage_mode)
- Asegurar que registros existentes tengan storage_mode='channel'
"""
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ Error: DATABASE_URL no configurada en .env")
    exit(1)

import psycopg2

def migrate():
    """Migrar la restricción unique de backup_mappings"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("📋 Migrando tabla backup_mappings...")
        
        # 1. Asegurar que todos los registros existentes tengan storage_mode
        try:
            cur.execute("""
                UPDATE backup_mappings 
                SET storage_mode = 'channel' 
                WHERE storage_mode IS NULL
            """)
            updated = cur.rowcount
            if updated > 0:
                print(f"✅ {updated} registros actualizados con storage_mode='channel'")
            else:
                print("✅ Todos los registros ya tienen storage_mode definido")
        except Exception as e:
            print(f"⚠️ Error actualizando storage_mode: {str(e)[:100]}")
        
        # 2. Quitar el UNIQUE constraint antiguo de source_chat_id
        # Primero buscar el nombre del constraint
        try:
            cur.execute("""
                SELECT conname FROM pg_constraint 
                WHERE conrelid = 'backup_mappings'::regclass 
                AND contype = 'u'
            """)
            constraints = cur.fetchall()
            
            for (constraint_name,) in constraints:
                if constraint_name != 'uq_source_storage_mode':
                    cur.execute(f"ALTER TABLE backup_mappings DROP CONSTRAINT IF EXISTS {constraint_name}")
                    print(f"✅ Constraint '{constraint_name}' eliminado")
        except Exception as e:
            print(f"⚠️ Error quitando constraints: {str(e)[:100]}")
        
        # 3. Quitar el índice único antiguo si existe
        try:
            cur.execute("""
                SELECT indexname FROM pg_indexes 
                WHERE tablename = 'backup_mappings' 
                AND indexdef LIKE '%UNIQUE%source_chat_id%'
                AND indexname != 'uq_source_storage_mode'
            """)
            indexes = cur.fetchall()
            
            for (idx_name,) in indexes:
                cur.execute(f"DROP INDEX IF EXISTS {idx_name}")
                print(f"✅ Índice único '{idx_name}' eliminado")
        except Exception as e:
            print(f"⚠️ Error quitando índices: {str(e)[:100]}")
        
        # 4. Agregar el nuevo UNIQUE constraint compuesto
        try:
            cur.execute("""
                ALTER TABLE backup_mappings 
                ADD CONSTRAINT uq_source_storage_mode 
                UNIQUE (source_chat_id, storage_mode)
            """)
            print("✅ Nuevo constraint UNIQUE(source_chat_id, storage_mode) creado")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("✅ Constraint uq_source_storage_mode ya existe")
            else:
                print(f"⚠️ Error creando constraint compuesto: {str(e)[:100]}")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print("\n📊 Migración completada correctamente")
        print("💡 Ahora puedes tener backup en canal Y en tema para el mismo grupo")
        
    except Exception as e:
        print(f"❌ Error en la migración: {str(e)}")

if __name__ == "__main__":
    migrate()

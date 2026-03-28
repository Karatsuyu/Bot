"""Script para probar que el backup automático funciona"""
from database.db import SessionLocal
from database.models import BackupMapping, TelegramEntity

def test_backup():
    session = SessionLocal()
    try:
        print("🧪 PROBANDO CONFIGURACIÓN DE BACKUP")
        print("=" * 60)
        
        # Verificar backups activos
        active = session.query(BackupMapping).filter_by(enabled=True).all()
        
        print(f"\n📊 Backups activos encontrados: {len(active)}\n")
        
        for mapping in active:
            entity = session.query(TelegramEntity).filter_by(
                telegram_id=mapping.source_chat_id
            ).first()
            
            if entity:
                print(f"✅ {entity.title}")
                print(f"   Source ID: {mapping.source_chat_id}")
                print(f"   Dest ID: {mapping.dest_chat_id}")
                print(f"   Enabled: {mapping.enabled}")
                print(f"   Historial pending: {mapping.historial_pending}")
                
                if mapping.dest_chat_id == 0:
                    print(f"   ⚠️ PROBLEMA: Canal no creado (dest_chat_id = 0)")
                else:
                    print(f"   ✅ Canal OK: {mapping.dest_chat_title}")
                print()
        
        print("\n" + "=" * 60)
        print("📝 INSTRUCCIONES PARA PROBAR:")
        print("=" * 60)
        print("1. El backup automático SOLO funciona con mensajes NUEVOS")
        print("2. Envía una foto/video a uno de los grupos activos")
        print("3. Deberías ver en la terminal del userbot: '💾 Backup: [grupo] → archivo guardado'")
        print("\n4. Para descargar el HISTORIAL, usa en el bot:")
        print("   /backup_historial 3694633617  (Chat hot 🔥💗)")
        print("   /backup_historial 1858875693  (Language: wsytgjc)")
        print("   /backup_historial 3291251256  (Lenguaje Trasladation)")
        print("=" * 60)
        
    finally:
        session.close()

if __name__ == "__main__":
    test_backup()

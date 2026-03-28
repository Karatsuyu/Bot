"""Script para verificar el estado de los backups"""
from database.db import SessionLocal
from database.models import BackupMapping, TelegramEntity

def check_backups():
    session = SessionLocal()
    try:
        print("=" * 60)
        print("📊 ESTADO DE BACKUPS")
        print("=" * 60)
        
        # Backups activos
        active = session.query(BackupMapping).filter_by(enabled=True).all()
        print(f"\n✅ Backups activos: {len(active)}")
        
        for mapping in active:
            entity = session.query(TelegramEntity).filter_by(
                telegram_id=mapping.source_chat_id
            ).first()
            
            if entity:
                status = ""
                if mapping.dest_chat_id == 0:
                    status = "⏳ Pendiente (creando canal)"
                elif mapping.historial_pending:
                    status = "📚 Descargando historial"
                else:
                    status = "✅ Activo"
                
                print(f"\n  📁 {entity.title}")
                print(f"     ID: {entity.telegram_id}")
                print(f"     Estado: {status}")
                print(f"     Archivos: {mapping.message_count}")
                if mapping.dest_chat_id != 0:
                    print(f"     Canal: {mapping.dest_chat_title}")
        
        # Backups con historial pendiente
        historial = session.query(BackupMapping).filter_by(
            historial_pending=True,
            enabled=True
        ).all()
        
        if historial:
            print(f"\n\n📚 Historiales pendientes: {len(historial)}")
            for mapping in historial:
                entity = session.query(TelegramEntity).filter_by(
                    telegram_id=mapping.source_chat_id
                ).first()
                if entity:
                    print(f"  - {entity.title}")
        
        # Backups esperando canal
        pending_channel = session.query(BackupMapping).filter_by(
            dest_chat_id=0,
            enabled=True
        ).all()
        
        if pending_channel:
            print(f"\n\n⏳ Esperando creación de canal: {len(pending_channel)}")
            for mapping in pending_channel:
                entity = session.query(TelegramEntity).filter_by(
                    telegram_id=mapping.source_chat_id
                ).first()
                if entity:
                    print(f"  - {entity.title}")
        
        print("\n" + "=" * 60)
        
    finally:
        session.close()

if __name__ == "__main__":
    check_backups()

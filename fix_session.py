"""
Script para configurar la sesión de Telethon en modo WAL para evitar locks
"""
import sqlite3
import os

session_file = "userbot_session.session"

if os.path.exists(session_file):
    print(f"📁 Configurando {session_file} en modo WAL...")
    try:
        conn = sqlite3.connect(session_file, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.commit()
        conn.close()
        print("✅ Sesión configurada correctamente")
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print(f"⚠️ Archivo {session_file} no existe aún")

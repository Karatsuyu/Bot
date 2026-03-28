from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Crear el motor de base de datos
engine = create_engine(os.getenv("DATABASE_URL"))

# Crear una sesión local
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Inicializa la base de datos creando todas las tablas"""
    from database.models import Base
    # Importar modelos adicionales que usan el mismo Base para que sus tablas
    # también se incluyan en el metadata antes de crear las tablas
    try:
        import feature.scanner.models  # noqa: F401
    except Exception:
        # Si el módulo no existe por cualquier motivo, seguimos con las tablas básicas
        pass
    Base.metadata.create_all(bind=engine)
    print("✅ Base de datos inicializada correctamente")

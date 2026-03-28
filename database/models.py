from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class TelegramEntity(Base):
    """Modelo para almacenar grupos, canales y bots de Telegram"""
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    title = Column(String, nullable=True)
    username = Column(String, nullable=True)
    invite_link = Column(String, nullable=True)
    entity_type = Column(String, nullable=False)  # group, channel, bot
    category = Column(String, default="sin_categoria")
    is_private = Column(Boolean, default=False)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con BackupMapping
    backup_config = relationship("BackupMapping", back_populates="source_entity", uselist=False)

    def __repr__(self):
        return f"<TelegramEntity(title='{self.title}', type='{self.entity_type}', category='{self.category}')>"


class BackupMapping(Base):
    """Mapeo de grupos origen → canales destino para backup automático"""
    __tablename__ = "backup_mappings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_chat_id = Column(BigInteger, ForeignKey('entities.telegram_id'), unique=True, nullable=False)
    dest_chat_id = Column(BigInteger, nullable=False)
    dest_chat_title = Column(String, nullable=True)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    message_count = Column(Integer, default=0)
    historial_pending = Column(Boolean, default=False)  # Nueva columna para solicitud de historial
    
    # Relación con TelegramEntity
    source_entity = relationship("TelegramEntity", back_populates="backup_config")
    
    def __repr__(self):
        return f"<BackupMapping(source={self.source_chat_id}, dest={self.dest_chat_id}, enabled={self.enabled})>"

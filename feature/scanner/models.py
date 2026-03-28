from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime
from datetime import datetime
from database.models import Base


class FoundLink(Base):
    """Enlaces encontrados durante escaneos controlados"""
    __tablename__ = "found_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_chat_id = Column(BigInteger, index=True, nullable=False)
    message_id = Column(BigInteger, nullable=False)
    link = Column(String, nullable=False, index=True)
    processed = Column(Boolean, default=False)
    joined = Column(Boolean, default=False)
    failed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ScanTarget(Base):
    """Control de chats que se pueden escanear"""
    __tablename__ = "scan_targets"

    chat_id = Column(BigInteger, primary_key=True)
    enabled = Column(Boolean, default=True)
    auto_join = Column(Boolean, default=False)
    last_scan = Column(DateTime, nullable=True)


class LinkRule(Base):
    """Reglas de whitelist / blacklist para enlaces o dominios"""
    __tablename__ = "link_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pattern = Column(String, unique=True, nullable=False)  # dominio o patrón simple
    is_whitelist = Column(Boolean, default=True)  # True=whitelist, False=blacklist
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

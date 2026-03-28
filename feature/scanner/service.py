from datetime import datetime
from typing import Optional

from telethon import TelegramClient

from database.db import SessionLocal
from database.models import TelegramEntity
from feature.scanner.extractor import extract_links
from feature.scanner.models import FoundLink, ScanTarget, LinkRule


async def scan_chat(client: TelegramClient, chat_id: int, limit: int = 200) -> int:
    """Escanea mensajes de un chat específico y guarda enlaces encontrados.

    Returns: número de enlaces nuevos almacenados.
    """
    entity = await client.get_entity(chat_id)

    session = SessionLocal()
    new_links = 0

    try:
        # Verificar/crear registro en ScanTarget
        target = session.query(ScanTarget).filter_by(chat_id=chat_id).first()
        if not target:
            target = ScanTarget(chat_id=chat_id, enabled=True, auto_join=False)
            session.add(target)
            session.commit()

        async for message in client.iter_messages(entity, limit=limit):
            text = message.message or ""
            links = extract_links(text)

            for link in links:
                # Filtrar según reglas de whitelist/blacklist
                if not _link_allowed_by_rules(session, link):
                    continue

                # Deduplicar a nivel de enlace+chat+mensaje
                exists = (
                    session.query(FoundLink)
                    .filter_by(source_chat_id=chat_id, message_id=message.id, link=link)
                    .first()
                )

                if exists:
                    continue

                item = FoundLink(
                    source_chat_id=chat_id,
                    message_id=message.id,
                    link=link,
                )
                session.add(item)
                new_links += 1

        # Actualizar last_scan
        target.last_scan = datetime.utcnow()
        session.commit()
        return new_links

    finally:
        session.close()


def get_pending_links(limit: int = 10):
    """Devuelve una lista de FoundLink pendientes de procesar."""
    session = SessionLocal()
    try:
        links = (
            session.query(FoundLink)
            .filter_by(processed=False)
            .order_by(FoundLink.created_at.asc())
            .limit(limit)
            .all()
        )
        # Devolvemos la sesión junto a los objetos para poder marcar luego
        return session, links
    except:
        session.close()
        raise


def mark_link_result(session, link_obj: FoundLink, joined: bool, failed: bool):
    """Marca el resultado de procesar un enlace."""
    link_obj.processed = True
    link_obj.joined = joined
    link_obj.failed = failed
    session.add(link_obj)


def _link_allowed_by_rules(session, link: str) -> bool:
    """Aplica reglas de whitelist/blacklist simples sobre un enlace.

    - Si hay reglas de whitelist activas: al menos una debe coincidir.
    - Luego se aplican reglas de blacklist: si alguna coincide, se bloquea.
    """
    rules = session.query(LinkRule).filter_by(enabled=True).all()
    if not rules:
        return True

    whitelists = [r for r in rules if r.is_whitelist]
    blacklists = [r for r in rules if not r.is_whitelist]

    if whitelists:
        if not any(r.pattern in link for r in whitelists):
            return False

    if any(r.pattern in link for r in blacklists):
        return False

    return True


def ensure_entity_for_chat(telegram_id: int, title: Optional[str], username: Optional[str] = None):
    """Garantiza que exista un TelegramEntity para un chat al que se ha unido.

    Se usa cuando nos unimos desde un enlace para ampliar el directorio.
    """
    from datetime import datetime as _dt

    session = SessionLocal()
    try:
        entity = session.query(TelegramEntity).filter_by(telegram_id=telegram_id).first()
        if not entity:
            entity = TelegramEntity(
                telegram_id=telegram_id,
                title=title,
                username=username,
                invite_link=None,
                entity_type="group",  # por defecto; se puede refinar si se necesita
                is_private=not bool(username),
                last_seen=_dt.utcnow(),
            )
            session.add(entity)
        else:
            # Actualizar datos básicos
            if title:
                entity.title = title
            if username:
                entity.username = username
            entity.last_seen = _dt.utcnow()

        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()

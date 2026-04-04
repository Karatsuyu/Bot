"""
Gestión de temas (topics) en supergrupos para backup
"""
from telethon import functions
from telethon.tl.types import Channel, InputPeerChannel
from database.db import SessionLocal
from database.models import BackupMapping
import logging

logger = logging.getLogger(__name__)

# Límite máximo de temas por supergrupo (Telegram permite hasta ~100-200 temas)
MAX_TOPICS_PER_GROUP = 100


def _normalize_group_id(group_id):
    """
    Convierte group_id (str o int) a dos formas:
      - full_id: entero negativo con prefijo -100 (ej. -1001234567890)
      - raw_id:  entero positivo sin prefijo     (ej.  1234567890)
    """
    gid = int(group_id)
    s = str(gid)

    if s.startswith("-100"):
        raw_id = int(s[4:])
    elif s.startswith("-"):
        raw_id = int(s[1:])
    else:
        raw_id = gid

    full_id = int(f"-100{raw_id}")
    return full_id, raw_id


async def _resolve_supergroup_as_input_peer(client, group_id):
    """
    Resuelve un supergrupo/foro como InputPeerChannel (el único tipo válido
    para CreateForumTopicRequest).

    Los supergrupos con foros son internamente 'Channel' en la API de Telegram,
    incluso si el usuario los ve como grupos. Por eso get_input_peer() a veces
    devuelve InputPeerChat cuando se usa el ID limpio (sin -100), lo que causa:
        "An invalid Peer was used" en CreateForumTopicRequest.

    Esta función garantiza que siempre retorne un InputPeerChannel válido.
    """
    full_id, raw_id = _normalize_group_id(group_id)

    # ── Intento 1: get_input_entity() con el ID completo negativo ─────────────
    try:
        input_peer = await client.get_input_entity(full_id)
        if isinstance(input_peer, InputPeerChannel):
            logger.info(f"✅ InputPeerChannel obtenido por ID completo ({full_id})")
            return input_peer
        else:
            logger.warning(
                f"⚠️ get_input_entity devolvió {type(input_peer).__name__} "
                f"para {full_id} — esperado InputPeerChannel"
            )
    except Exception as e1:
        logger.debug(f"Intento 1 falló ({full_id}): {str(e1)[:80]}")

    # ── Intento 2: get_input_entity() con el ID positivo sin prefijo ──────────
    try:
        input_peer = await client.get_input_entity(raw_id)
        if isinstance(input_peer, InputPeerChannel):
            logger.info(f"✅ InputPeerChannel obtenido por raw_id ({raw_id})")
            return input_peer
    except Exception as e2:
        logger.debug(f"Intento 2 falló ({raw_id}): {str(e2)[:80]}")

    # ── Intento 3: get_entity() y construir InputPeerChannel manualmente ──────
    for attempt_id in [full_id, raw_id]:
        try:
            entity = await client.get_entity(attempt_id)
            if isinstance(entity, Channel):
                input_peer = InputPeerChannel(
                    channel_id=entity.id,
                    access_hash=entity.access_hash
                )
                logger.info(
                    f"✅ InputPeerChannel construido manualmente "
                    f"(id={entity.id}, title={getattr(entity, 'title', '?')})"
                )
                return input_peer
            else:
                logger.warning(
                    f"⚠️ get_entity devolvió {type(entity).__name__} para "
                    f"ID {attempt_id} — no es un Channel/supergrupo"
                )
        except Exception as e3:
            logger.debug(f"Intento 3 con ID {attempt_id} falló: {str(e3)[:80]}")

    # ── Intento 4: buscar en diálogos ─────────────────────────────────────────
    logger.info("🔍 Buscando supergrupo en diálogos abiertos...")
    try:
        async for dialog in client.iter_dialogs():
            entity = dialog.entity
            if not isinstance(entity, Channel):
                continue
            if entity.id == raw_id or entity.id == full_id:
                input_peer = InputPeerChannel(
                    channel_id=entity.id,
                    access_hash=entity.access_hash
                )
                logger.info(
                    f"✅ InputPeerChannel encontrado en diálogos: "
                    f"{getattr(entity, 'title', '?')}"
                )
                return input_peer
    except Exception as e4:
        logger.error(f"Intento 4 (diálogos) falló: {str(e4)[:80]}")

    logger.error(
        f"❌ No se pudo resolver el supergrupo {group_id} como InputPeerChannel.\n"
        f"💡 SOLUCIÓN: Asegúrate de que el userbot esté unido al supergrupo y de que "
        f"el grupo tenga 'Temas' (Topics/Forum) activado en su configuración."
    )
    return None


async def create_topic(client, group_id, title):
    """
    Crea un nuevo tema en un supergrupo con foros activados.

    Returns:
        int: topic_id del tema creado, o None si falla
    """
    try:
        import random

        input_peer = await _resolve_supergroup_as_input_peer(client, group_id)
        if not input_peer:
            return None

        logger.info(f"📌 Creando tema '{title}' en supergrupo (peer={input_peer.channel_id})")

        random_id = random.randint(1, 2**31 - 1)

        result = await client(functions.messages.CreateForumTopicRequest(
            peer=input_peer,
            title=title,
            random_id=random_id
        ))

        # El topic_id está en el primer update con atributo 'id'
        if result and result.updates:
            for update in result.updates:
                topic_id = getattr(update, 'id', None)
                if topic_id:
                    logger.info(f"✅ Tema creado: '{title}' (topic_id={topic_id})")
                    return topic_id

        logger.error(
            f"❌ Respuesta inesperada al crear tema, no se encontró topic_id.\n"
            f"   Updates recibidos: {result.updates if result else 'ninguno'}"
        )
        return None

    except AttributeError as ae:
        logger.error(
            f"❌ CreateForumTopicRequest no disponible en esta versión de Telethon: {str(ae)[:200]}\n"
            f"💡 Actualiza Telethon: pip install --upgrade telethon"
        )
        return None
    except Exception as e:
        error_msg = str(e)
        if "forum" in error_msg.lower() or "topic" in error_msg.lower():
            logger.error(
                f"❌ Error creando tema '{title}': {error_msg[:200]}\n"
                f"💡 Verifica que el supergrupo tenga 'Temas' activados: "
                f"Configuración del grupo → Editar → activar 'Temas'"
            )
        else:
            logger.error(f"❌ Error creando tema '{title}': {error_msg[:200]}")
        return None


async def get_or_create_topic(client, group_id, source_chat_id, source_title):
    """
    Obtiene un tema existente o crea uno nuevo para un chat origen.

    Returns:
        int: topic_id del tema
    """
    session = SessionLocal()
    try:
        # Si ya existe un backup con topic_id, reutilizarlo
        backup = session.query(BackupMapping).filter_by(
            source_chat_id=source_chat_id,
            storage_mode='topic'
        ).first()

        if backup and backup.topic_id:
            logger.debug(f"📦 Tema existente para {source_chat_id}: {backup.topic_id}")
            return backup.topic_id

        # Verificar límite de temas
        topic_count = session.query(BackupMapping).filter_by(
            storage_mode='topic'
        ).count()

        if topic_count >= MAX_TOPICS_PER_GROUP:
            logger.error(f"⚠️ Límite de temas alcanzado ({MAX_TOPICS_PER_GROUP})")
            return None

        # Crear nuevo tema
        safe_title = f"📦 {source_title[:40]}" if source_title else f"📦 Backup {source_chat_id}"
        topic_id = await create_topic(client, group_id, safe_title)

        if not topic_id:
            return None

        # Actualizar o crear el BackupMapping
        if backup:
            backup.topic_id = topic_id
            backup.dest_chat_id = int(group_id)
            backup.dest_chat_title = f"📦 Topic: {safe_title}"
        else:
            new_backup = BackupMapping(
                source_chat_id=source_chat_id,
                dest_chat_id=int(group_id),
                dest_chat_title=f"📦 Topic: {safe_title}",
                topic_id=topic_id,
                storage_mode='topic',
                enabled=True
            )
            session.add(new_backup)

        session.commit()
        logger.info(f"✅ Tema guardado en DB: {source_chat_id} → topic_id={topic_id}")

        return topic_id

    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error en get_or_create_topic: {str(e)[:200]}")
        return None
    finally:
        session.close()


async def count_topics_in_group(client, group_id):
    """
    Cuenta cuántos temas hay en un supergrupo.
    """
    try:
        count = 0
        async for topic in client.iter_forum_topics(group_id):
            count += 1
        return count
    except Exception as e:
        logger.error(f"❌ Error contando temas: {str(e)[:100]}")
        return 0
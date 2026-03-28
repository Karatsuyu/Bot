import asyncio
import time

LAST_ACTION = 0.0
MIN_DELAY = 30  # segundos por defecto


async def safe_delay(min_delay: int | None = None):
    """Espera de forma segura entre acciones (anti-flood)."""
    global LAST_ACTION

    delay = float(min_delay) if min_delay is not None else MIN_DELAY

    now = time.time()
    diff = now - LAST_ACTION

    if diff < delay:
        await asyncio.sleep(delay - diff)

    LAST_ACTION = time.time()

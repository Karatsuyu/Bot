from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def pagination_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Teclado simple de paginación (solo botones de anterior/siguiente)."""
    builder = InlineKeyboardBuilder()

    if page > 1:
        builder.button(text="⬅️ Anterior", callback_data=f"dir:{page-1}")

    if page < total_pages:
        builder.button(text="➡️ Siguiente", callback_data=f"dir:{page+1}")

    # Colocar los botones de navegación en una sola fila si existen
    builder.adjust(2)

    return builder.as_markup()


def directory_keyboard(entries, page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Teclado para el directorio paginado.

    entries: lista de tuplas (found_link_id, link)
    """
    builder = InlineKeyboardBuilder()

    # Fila por enlace: [Ver] [Unirme]
    for link_id, link in entries:
        builder.row(
            InlineKeyboardButton(text="🔗 Ver", url=link),
            InlineKeyboardButton(text="➕ Unirme", callback_data=f"join:{link_id}"),
        )

    # Fila de navegación
    nav_builder = InlineKeyboardBuilder()
    if page > 1:
        nav_builder.button(text="⬅️ Anterior", callback_data=f"dir:{page-1}")

    if page < total_pages:
        nav_builder.button(text="➡️ Siguiente", callback_data=f"dir:{page+1}")

    if nav_builder.buttons:
        nav_builder.adjust(2)
        # Añadir la fila de navegación al final
        for row in nav_builder.export():
            builder.row(*row)

    return builder.as_markup()

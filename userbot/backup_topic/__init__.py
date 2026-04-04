"""
Módulo para backup en supergrupos con temas (topics)
Backup automático de multimedia usando temas en lugar de canales
"""

from .service import backup_to_topic, process_pending_topic_backups, download_historial_to_topic
from .topics import create_topic, get_or_create_topic
from .sender import send_to_topic, forward_to_topic, send_file_to_topic, extract_file_info

__all__ = [
    'backup_to_topic',
    'process_pending_topic_backups',
    'download_historial_to_topic',
    'create_topic',
    'get_or_create_topic',
    'send_to_topic',
    'forward_to_topic',
    'send_file_to_topic',
    'extract_file_info',
]

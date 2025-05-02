# utils.py
import locale
from datetime import datetime

def format_datetime_es(dt):
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # Linux/macOS
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')  # Windows
        except locale.Error:
            return dt.strftime('%d/%m/%Y %H:%M')  # fallback

    return dt.strftime('%d de %B de %Y, %H:%M')

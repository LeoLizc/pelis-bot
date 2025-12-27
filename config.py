"""
Configuración central del bot.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Discord
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Google Docs
GOOGLE_DOC_ID = os.getenv("GOOGLE_DOC_ID", "1wxsL6Qe5hbXHXqTWTHcFbwB6Rkdr6Ao2ez2mXyyjtrY")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "service_account.json")

# Delimitadores para ignorar contenido (última página)
# Añade aquí cualquier texto que marque el inicio de contenido a ignorar
PAGE_DELIMITERS = [
    "-----",
    "───",
    "---",
    "—————",
    "━━━",
    "2024/25",  # Si hay un encabezado de año, ignorar desde ahí
    "2024",
    "2025",
]

# Separador entre título y proponente
MOVIE_SEPARATOR = " - "

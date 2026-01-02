#!/usr/bin/env python3
"""
Bot de Discord para gestionar lista de películas.

Características:
- Lee películas desde un documento de Google Docs
- Detecta películas vistas (tachadas) y pendientes
- Permite elegir películas al azar
- Sistema de votación grupal
- Tacha películas en el documento cuando se marcan como vistas

Uso:
    python main.py
"""
import sys

from src.utils import setup_logging, get_logger


def main():
    """Punto de entrada principal del bot."""
    # Configurar logging antes de cualquier otra cosa
    setup_logging()
    
    logger = get_logger(__name__)
    logger.info("Iniciando Pelis Bot...")
    
    try:
        from src.bot import PelisBot
        import config
        
        # Verificar configuración
        if not config.DISCORD_TOKEN:
            logger.error("DISCORD_TOKEN no configurado. Crea un archivo .env con el token.")
            sys.exit(1)
        
        logger.info("Configuración cargada correctamente")
        logger.debug(f"Google Doc ID: {config.GOOGLE_DOC_ID}")
        
        # Iniciar bot
        bot = PelisBot()
        bot.run(config.DISCORD_TOKEN)
        
    except ImportError as e:
        logger.error(f"Error de importación: {e}", exc_info=True)
        logger.error("Asegúrate de instalar las dependencias: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Error fatal: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

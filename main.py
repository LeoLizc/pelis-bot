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
import logging
import sys

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Punto de entrada principal del bot."""
    logger.info("Iniciando Pelis Bot...")
    
    try:
        from src.bot import PelisBot
        import config
        
        # Verificar configuración
        if not config.DISCORD_TOKEN:
            logger.error("DISCORD_TOKEN no configurado. Crea un archivo .env con el token.")
            sys.exit(1)
        
        # Iniciar bot
        bot = PelisBot()
        bot.run(config.DISCORD_TOKEN)
        
    except ImportError as e:
        logger.error(f"Error de importación: {e}")
        logger.error("Asegúrate de instalar las dependencias: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

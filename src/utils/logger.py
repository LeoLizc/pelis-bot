"""
Sistema de logging centralizado y detallado.
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Directorio de logs
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Formato detallado para archivos
DETAILED_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)-25s | "
    "%(filename)s:%(lineno)-4d | %(funcName)-20s | %(message)s"
)

# Formato simple para consola
CONSOLE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"

# Formato para el log de acciones del bot
ACTION_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"


class ActionFilter(logging.Filter):
    """Filtro para el log de acciones importantes."""
    
    def filter(self, record):
        # Solo pasar mensajes marcados como acciones
        return getattr(record, 'action', False)


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configura el sistema de logging completo.
    
    Args:
        level: Nivel de logging (default: INFO)
    """
    # Crear fecha para nombre de archivo
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Obtener el logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capturar todo, filtrar en handlers
    
    # Limpiar handlers existentes
    root_logger.handlers.clear()
    
    # ========================================
    # Handler 1: Consola (INFO+)
    # ========================================
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(
        CONSOLE_FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    root_logger.addHandler(console_handler)
    
    # ========================================
    # Handler 2: Archivo general detallado (DEBUG+)
    # ========================================
    general_log_file = LOGS_DIR / f"bot_{date_str}.log"
    file_handler = RotatingFileHandler(
        general_log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        DETAILED_FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    root_logger.addHandler(file_handler)
    
    # ========================================
    # Handler 3: Archivo de errores (WARNING+)
    # ========================================
    error_log_file = LOGS_DIR / f"errors_{date_str}.log"
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(logging.Formatter(
        DETAILED_FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    root_logger.addHandler(error_handler)
    
    # ========================================
    # Handler 4: Archivo de acciones (registro de uso)
    # ========================================
    actions_log_file = LOGS_DIR / f"actions_{date_str}.log"
    actions_handler = RotatingFileHandler(
        actions_log_file,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=10,
        encoding='utf-8'
    )
    actions_handler.setLevel(logging.INFO)
    actions_handler.setFormatter(logging.Formatter(
        ACTION_FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    actions_handler.addFilter(ActionFilter())
    root_logger.addHandler(actions_handler)
    
    # Reducir ruido de librerías externas
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('discord.http').setLevel(logging.WARNING)
    logging.getLogger('discord.gateway').setLevel(logging.WARNING)
    logging.getLogger('googleapiclient').setLevel(logging.WARNING)
    logging.getLogger('google').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    # Log inicial
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Sistema de logging inicializado")
    logger.info(f"Logs guardados en: {LOGS_DIR}")
    logger.info(f"Archivo general: {general_log_file.name}")
    logger.info(f"Archivo errores: {error_log_file.name}")
    logger.info(f"Archivo acciones: {actions_log_file.name}")
    logger.info("=" * 60)


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger configurado para el módulo especificado.
    
    Args:
        name: Nombre del módulo (usar __name__)
        
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)


def log_action(
    logger: logging.Logger,
    action: str,
    user: str = None,
    guild: str = None,
    details: str = None
) -> None:
    """
    Registra una acción importante del bot.
    
    Args:
        logger: Logger a usar
        action: Tipo de acción (ej: "COMMAND", "VOTE", "STRIKE")
        user: Usuario que realizó la acción
        guild: Servidor donde ocurrió
        details: Detalles adicionales
    """
    parts = [f"[{action}]"]
    
    if guild:
        parts.append(f"[Server: {guild}]")
    if user:
        parts.append(f"[User: {user}]")
    if details:
        parts.append(details)
    
    message = " ".join(parts)
    
    # Crear un registro con el atributo 'action' para el filtro
    logger.info(message, extra={'action': True})


class BotLogger:
    """
    Clase helper para logging con contexto del bot.
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def debug(self, message: str, **kwargs):
        """Log de nivel DEBUG."""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log de nivel INFO."""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log de nivel WARNING."""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log de nivel ERROR."""
        self.logger.error(message, exc_info=exc_info, **kwargs)
    
    def critical(self, message: str, exc_info: bool = True, **kwargs):
        """Log de nivel CRITICAL."""
        self.logger.critical(message, exc_info=exc_info, **kwargs)
    
    def action(
        self,
        action_type: str,
        user: str = None,
        guild: str = None,
        details: str = None
    ):
        """
        Registra una acción del bot.
        
        Args:
            action_type: Tipo de acción (COMMAND, VOTE, STRIKE, etc.)
            user: Usuario que realizó la acción
            guild: Servidor
            details: Detalles adicionales
        """
        log_action(self.logger, action_type, user, guild, details)
    
    def command(
        self,
        command_name: str,
        user: str,
        guild: str = None,
        args: dict = None
    ):
        """
        Registra la ejecución de un comando.
        
        Args:
            command_name: Nombre del comando
            user: Usuario que ejecutó
            guild: Servidor
            args: Argumentos del comando
        """
        details = f"/{command_name}"
        if args:
            args_str = ", ".join(f"{k}={v}" for k, v in args.items() if v is not None)
            if args_str:
                details += f" ({args_str})"
        
        self.action("COMMAND", user, guild, details)
    
    def movie_strike(self, movie_title: str, user: str, guild: str = None):
        """Registra cuando se tacha una película."""
        self.action("STRIKE", user, guild, f"Película tachada: '{movie_title}'")
    
    def vote(self, movie_title: str, user: str, guild: str = None, removed: bool = False):
        """Registra un voto."""
        action = "VOTE_REMOVE" if removed else "VOTE"
        self.action(action, user, guild, f"Película: '{movie_title}'")
    
    def voting_start(self, movies_count: int, duration: int, user: str, guild: str = None):
        """Registra inicio de votación."""
        self.action(
            "VOTING_START",
            user,
            guild,
            f"{movies_count} películas, {duration} minutos"
        )
    
    def voting_end(self, winner: str, votes: int, guild: str = None):
        """Registra fin de votación."""
        self.action(
            "VOTING_END",
            None,
            guild,
            f"Ganadora: '{winner}' con {votes} votos"
        )

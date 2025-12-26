"""
Cliente principal del bot de Discord.
"""
import discord
from discord.ext import commands
import logging

import config

logger = logging.getLogger(__name__)


class PelisBot(commands.Bot):
    """Bot principal para gestión de películas."""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            description="Bot para gestionar lista de películas"
        )
    
    async def setup_hook(self):
        """Se ejecuta cuando el bot está listo para cargar extensiones."""
        # Cargar cogs
        await self.load_extension("src.bot.cogs.movies")
        await self.load_extension("src.bot.cogs.voting")
        
        # Sincronizar comandos slash
        await self.tree.sync()
        logger.info("Comandos slash sincronizados")
    
    async def on_ready(self):
        """Se ejecuta cuando el bot está completamente conectado."""
        logger.info(f"Bot conectado como {self.user} (ID: {self.user.id})")
        logger.info(f"Conectado a {len(self.guilds)} servidor(es)")
        
        # Establecer estado del bot
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="películas 🎬"
        )
        await self.change_presence(activity=activity)
    
    async def on_command_error(self, ctx, error):
        """Manejo global de errores de comandos."""
        if isinstance(error, commands.CommandNotFound):
            return
        
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ No tienes permisos para usar este comando.")
            return
        
        logger.error(f"Error en comando: {error}")
        await ctx.send(f"❌ Ocurrió un error: {str(error)}")


def run_bot():
    """Función para ejecutar el bot."""
    bot = PelisBot()
    bot.run(config.DISCORD_TOKEN)

"""
Vistas para la configuración de votaciones manuales.
"""
import discord
from discord.ui import View, Button, Modal, TextInput, Select
from typing import List, Optional, Callable, TYPE_CHECKING
import asyncio

from src.models import Movie
from src.google_docs import MovieDocReader
from src.utils.logger import BotLogger

if TYPE_CHECKING:
    from src.bot.cogs.voting import VotingCog

logger = BotLogger(__name__)

# Límites
MAX_MOVIES_IN_VOTING = 10
MIN_MOVIES_IN_VOTING = 2


class MovieSearchModal(Modal):
    """Modal para buscar películas por nombre."""
    
    def __init__(self, setup_view: "VotingSetupView"):
        super().__init__(title="Buscar Película")
        self.setup_view = setup_view
        
        self.search_input = TextInput(
            label="Nombre de la película",
            placeholder="Escribe el título o parte del título...",
            style=discord.TextStyle.short,
            required=True,
            min_length=2,
            max_length=100
        )
        self.add_item(self.search_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Procesa la búsqueda cuando se envía el modal."""
        search_term = self.search_input.value.strip()
        logger.debug(f"Búsqueda de película: '{search_term}'")
        
        # Buscar coincidencias
        matches = self.setup_view.doc_reader.find_movie_by_title(
            search_term, 
            pending_only=True
        )
        
        # Filtrar películas ya seleccionadas
        already_selected_titles = {m.titulo.lower() for m in self.setup_view.selected_movies}
        matches = [m for m in matches if m.titulo.lower() not in already_selected_titles]
        
        if not matches:
            await interaction.response.send_message(
                f"❌ No se encontró ninguna película pendiente que coincida con **{search_term}**.\n"
                "*(Nota: Las películas ya seleccionadas no aparecen)*",
                ephemeral=True
            )
            return
        
        if len(matches) == 1:
            # Una sola coincidencia - añadir directamente
            movie = matches[0]
            self.setup_view.selected_movies.append(movie)
            logger.debug(f"Película añadida directamente: '{movie.titulo}'")
            
            await interaction.response.send_message(
                f"✅ **{movie.titulo}** añadida a la votación.",
                ephemeral=True
            )
            
            # Actualizar el mensaje principal
            await self.setup_view.update_setup_message()
        else:
            # Múltiples coincidencias - mostrar selector
            logger.debug(f"Múltiples coincidencias ({len(matches)}), mostrando selector")
            
            view = MovieDisambiguationView(
                matches=matches[:25],  # Límite de Discord
                setup_view=self.setup_view
            )
            
            embed = discord.Embed(
                title="🔍 Múltiples coincidencias",
                description=f"Se encontraron **{len(matches)}** películas. Selecciona cuál añadir:",
                color=discord.Color.blue()
            )
            
            await interaction.response.send_message(
                embed=embed,
                view=view,
                ephemeral=True
            )


class MovieDisambiguationView(View):
    """Vista con selector para elegir entre múltiples películas."""
    
    def __init__(
        self,
        matches: List[Movie],
        setup_view: "VotingSetupView",
        timeout: float = 60.0
    ):
        super().__init__(timeout=timeout)
        self.matches = matches
        self.setup_view = setup_view
        
        # Crear opciones del selector
        options = [
            discord.SelectOption(
                label=movie.titulo[:100],
                description=f"Por: {movie.proponente}"[:100],
                value=str(i)
            )
            for i, movie in enumerate(matches[:25])
        ]
        
        self.select_menu = Select(
            placeholder="Selecciona una película...",
            options=options,
            min_values=1,
            max_values=1
        )
        self.select_menu.callback = self.select_callback
        self.add_item(self.select_menu)
    
    async def select_callback(self, interaction: discord.Interaction):
        """Callback cuando se selecciona una película."""
        selected_index = int(self.select_menu.values[0])
        movie = self.matches[selected_index]
        
        # Añadir a la lista
        self.setup_view.selected_movies.append(movie)
        logger.debug(f"Película añadida desde selector: '{movie.titulo}'")
        
        await interaction.response.edit_message(
            content=f"✅ **{movie.titulo}** añadida a la votación.",
            embed=None,
            view=None
        )
        
        # Actualizar el mensaje principal
        await self.setup_view.update_setup_message()
    
    async def on_timeout(self):
        """Deshabilitar cuando expira."""
        self.select_menu.disabled = True


class VotingSetupView(View):
    """Vista principal para configurar una votación manual."""
    
    def __init__(
        self,
        doc_reader: MovieDocReader,
        cog: "VotingCog",
        creator: discord.User,
        duration_minutes: int = 5,
        max_votes_per_user: int = 1,
        timeout: float = 300.0  # 5 minutos para configurar
    ):
        super().__init__(timeout=timeout)
        self.doc_reader = doc_reader
        self.cog = cog
        self.creator = creator
        self.duration_minutes = duration_minutes
        self.max_votes_per_user = max_votes_per_user
        self.selected_movies: List[Movie] = []
        self.message: Optional[discord.Message] = None
        self.channel_id: Optional[int] = None
        
        self._update_buttons()
    
    def _update_buttons(self):
        """Actualiza el estado de los botones según las películas seleccionadas."""
        self.clear_items()
        
        # Botón agregar película
        can_add = len(self.selected_movies) < MAX_MOVIES_IN_VOTING
        add_btn = Button(
            label="Agregar Película",
            style=discord.ButtonStyle.secondary,
            emoji="➕",
            disabled=not can_add,
            row=0
        )
        add_btn.callback = self.add_movie_callback
        self.add_item(add_btn)
        
        # Botón quitar última
        can_remove = len(self.selected_movies) > 0
        remove_btn = Button(
            label="Quitar Última",
            style=discord.ButtonStyle.secondary,
            emoji="↩️",
            disabled=not can_remove,
            row=0
        )
        remove_btn.callback = self.remove_last_callback
        self.add_item(remove_btn)
        
        # Botón iniciar votación
        can_start = len(self.selected_movies) >= MIN_MOVIES_IN_VOTING
        start_btn = Button(
            label="Iniciar Votación",
            style=discord.ButtonStyle.success,
            emoji="🚀",
            disabled=not can_start,
            row=1
        )
        start_btn.callback = self.start_voting_callback
        self.add_item(start_btn)
        
        # Botón cancelar
        cancel_btn = Button(
            label="Cancelar",
            style=discord.ButtonStyle.danger,
            emoji="❌",
            row=1
        )
        cancel_btn.callback = self.cancel_callback
        self.add_item(cancel_btn)
    
    def get_embed(self) -> discord.Embed:
        """Genera el embed de configuración."""
        embed = discord.Embed(
            title="🎬 Configurar Votación Manual",
            description=(
                f"**Tiempo de votación:** {self.duration_minutes} minutos\n"
                f"**Votos por persona:** {self.max_votes_per_user}\n\n"
                f"Películas seleccionadas: **{len(self.selected_movies)}/{MAX_MOVIES_IN_VOTING}**"
            ),
            color=discord.Color.blue()
        )
        
        if self.selected_movies:
            movie_list = "\n".join([
                f"`{i+1}.` {movie.titulo} *(por {movie.proponente})*"
                for i, movie in enumerate(self.selected_movies)
            ])
            embed.add_field(
                name="📋 Lista de películas",
                value=movie_list,
                inline=False
            )
        else:
            embed.add_field(
                name="📋 Lista de películas",
                value="*Aún no has agregado películas. Usa el botón ➕ para buscar y añadir.*",
                inline=False
            )
        
        # Instrucciones
        if len(self.selected_movies) < MIN_MOVIES_IN_VOTING:
            embed.set_footer(
                text=f"⚠️ Necesitas al menos {MIN_MOVIES_IN_VOTING} películas para iniciar la votación."
            )
        else:
            embed.set_footer(text="✅ Listo para iniciar la votación.")
        
        return embed
    
    async def update_setup_message(self):
        """Actualiza el mensaje de configuración."""
        if self.message:
            try:
                self._update_buttons()
                await self.message.edit(embed=self.get_embed(), view=self)
            except discord.NotFound:
                logger.warning("Mensaje de configuración no encontrado")
            except Exception as e:
                logger.error(f"Error al actualizar mensaje de configuración: {e}")
    
    async def add_movie_callback(self, interaction: discord.Interaction):
        """Callback para agregar película."""
        # Verificar que sea el creador
        if interaction.user.id != self.creator.id:
            await interaction.response.send_message(
                "❌ Solo el creador de la votación puede configurarla.",
                ephemeral=True
            )
            return
        
        # Abrir modal de búsqueda
        await interaction.response.send_modal(MovieSearchModal(self))
    
    async def remove_last_callback(self, interaction: discord.Interaction):
        """Callback para quitar la última película."""
        if interaction.user.id != self.creator.id:
            await interaction.response.send_message(
                "❌ Solo el creador de la votación puede configurarla.",
                ephemeral=True
            )
            return
        
        if self.selected_movies:
            removed = self.selected_movies.pop()
            logger.debug(f"Película removida: '{removed.titulo}'")
            
            await interaction.response.send_message(
                f"↩️ **{removed.titulo}** removida de la lista.",
                ephemeral=True
            )
            await self.update_setup_message()
        else:
            await interaction.response.send_message(
                "❌ No hay películas para quitar.",
                ephemeral=True
            )
    
    async def start_voting_callback(self, interaction: discord.Interaction):
        """Callback para iniciar la votación."""
        if interaction.user.id != self.creator.id:
            await interaction.response.send_message(
                "❌ Solo el creador de la votación puede iniciarla.",
                ephemeral=True
            )
            return
        
        if len(self.selected_movies) < MIN_MOVIES_IN_VOTING:
            await interaction.response.send_message(
                f"❌ Necesitas al menos {MIN_MOVIES_IN_VOTING} películas.",
                ephemeral=True
            )
            return
        
        logger.debug(f"Iniciando votación manual con {len(self.selected_movies)} películas")
        
        # Llamar al cog para iniciar la votación
        await self.cog.start_manual_voting(
            interaction=interaction,
            movies=self.selected_movies,
            duration_minutes=self.duration_minutes,
            max_votes_per_user=self.max_votes_per_user,
            setup_message=self.message
        )
        
        # Detener esta vista
        self.stop()
    
    async def cancel_callback(self, interaction: discord.Interaction):
        """Callback para cancelar la configuración."""
        if interaction.user.id != self.creator.id:
            await interaction.response.send_message(
                "❌ Solo el creador puede cancelar.",
                ephemeral=True
            )
            return
        
        logger.debug("Configuración de votación manual cancelada")
        
        embed = discord.Embed(
            title="❌ Configuración cancelada",
            description="La votación manual ha sido cancelada.",
            color=discord.Color.greyple()
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()
    
    async def on_timeout(self):
        """Se ejecuta cuando expira el timeout."""
        logger.debug("Timeout de configuración de votación manual")
        
        if self.message:
            try:
                embed = discord.Embed(
                    title="⏰ Tiempo agotado",
                    description="La configuración de la votación ha expirado.",
                    color=discord.Color.greyple()
                )
                await self.message.edit(embed=embed, view=None)
            except:
                pass

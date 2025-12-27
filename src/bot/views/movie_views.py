"""
Vistas relacionadas con películas (botones de tachar, selección, etc.)
"""
import discord
from discord.ui import View, Button, Select
from typing import List, Optional
import logging

from src.models import Movie
from src.google_docs import MovieDocReader

logger = logging.getLogger(__name__)


class StrikeMovieView(View):
    """Vista con botón para tachar una película."""
    
    def __init__(
        self,
        movie: Movie,
        doc_reader: MovieDocReader,
        requester: Optional[discord.User] = None,
        label: str = "Tachar Película",
        timeout: float = 300.0
    ):
        super().__init__(timeout=timeout)
        self.movie = movie
        self.doc_reader = doc_reader
        self.requester = requester
        
        # Botón de confirmar
        self.confirm_button = Button(
            label=label,
            style=discord.ButtonStyle.success,
            emoji="✅"
        )
        self.confirm_button.callback = self.confirm_callback
        self.add_item(self.confirm_button)
        
        # Botón de cancelar
        self.cancel_button = Button(
            label="Cancelar",
            style=discord.ButtonStyle.secondary,
            emoji="❌"
        )
        self.cancel_button.callback = self.cancel_callback
        self.add_item(self.cancel_button)
    
    async def confirm_callback(self, interaction: discord.Interaction):
        """Callback cuando se confirma el tachado."""
        try:
            # Tachar la película en Google Docs
            self.doc_reader.strike_movie(self.movie)
            
            embed = discord.Embed(
                title="✅ Película tachada",
                description=f"**{self.movie.titulo}** ha sido marcada como vista.",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Tachada por",
                value=interaction.user.mention,
                inline=True
            )
            
            logger.info(
                f"Película tachada: '{self.movie.titulo}' por {interaction.user.name}"
            )
            
            # Deshabilitar botones
            self.confirm_button.disabled = True
            self.cancel_button.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=self)
            
        except Exception as e:
            logger.error(f"Error al tachar película: {e}")
            await interaction.response.send_message(
                f"❌ Error al tachar la película: {str(e)}",
                ephemeral=True
            )
    
    async def cancel_callback(self, interaction: discord.Interaction):
        """Callback cuando se cancela el tachado."""
        embed = discord.Embed(
            title="❌ Cancelado",
            description="No se tachó ninguna película.",
            color=discord.Color.greyple()
        )
        
        # Deshabilitar botones
        self.confirm_button.disabled = True
        self.cancel_button.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def on_timeout(self):
        """Se ejecuta cuando expira el timeout de la vista."""
        self.confirm_button.disabled = True
        self.cancel_button.disabled = True


class MovieSelectionView(View):
    """Vista con menú desplegable para seleccionar una película de múltiples opciones."""
    
    def __init__(
        self,
        movies: List[Movie],
        doc_reader: MovieDocReader,
        requester: discord.User,
        timeout: float = 120.0
    ):
        super().__init__(timeout=timeout)
        self.movies = movies
        self.doc_reader = doc_reader
        self.requester = requester
        self.selected_movie: Optional[Movie] = None
        
        # Crear opciones del menú
        options = [
            discord.SelectOption(
                label=movie.titulo[:100],  # Límite de Discord
                description=f"Por: {movie.proponente}"[:100],
                value=str(i)
            )
            for i, movie in enumerate(movies[:25])  # Máximo 25 opciones
        ]
        
        self.select_menu = Select(
            placeholder="Selecciona una película...",
            options=options,
            min_values=1,
            max_values=1
        )
        self.select_menu.callback = self.select_callback
        self.add_item(self.select_menu)
        
        # Botón de confirmar (inicialmente deshabilitado)
        self.confirm_button = Button(
            label="Confirmar tachado",
            style=discord.ButtonStyle.success,
            emoji="✅",
            disabled=True
        )
        self.confirm_button.callback = self.confirm_callback
        self.add_item(self.confirm_button)
        
        # Botón de cancelar
        self.cancel_button = Button(
            label="Cancelar",
            style=discord.ButtonStyle.secondary,
            emoji="❌"
        )
        self.cancel_button.callback = self.cancel_callback
        self.add_item(self.cancel_button)
    
    async def select_callback(self, interaction: discord.Interaction):
        """Callback cuando se selecciona una película del menú."""
        selected_index = int(self.select_menu.values[0])
        self.selected_movie = self.movies[selected_index]
        self.confirm_button.disabled = False
        
        embed = discord.Embed(
            title="🎬 Película seleccionada",
            description=f"Has seleccionado: **{self.selected_movie.titulo}**\n"
                       f"Propuesta por: {self.selected_movie.proponente}\n\n"
                       "Haz clic en 'Confirmar tachado' para marcarla como vista.",
            color=discord.Color.blue()
        )
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def confirm_callback(self, interaction: discord.Interaction):
        """Callback cuando se confirma el tachado."""
        if not self.selected_movie:
            await interaction.response.send_message(
                "❌ Primero selecciona una película.",
                ephemeral=True
            )
            return
        
        try:
            self.doc_reader.strike_movie(self.selected_movie)
            
            embed = discord.Embed(
                title="✅ Película tachada",
                description=f"**{self.selected_movie.titulo}** ha sido marcada como vista.",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Tachada por",
                value=interaction.user.mention,
                inline=True
            )
            
            logger.info(
                f"Película tachada: '{self.selected_movie.titulo}' por {interaction.user.name}"
            )
            
            # Deshabilitar todo
            self.select_menu.disabled = True
            self.confirm_button.disabled = True
            self.cancel_button.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=self)
            
        except Exception as e:
            logger.error(f"Error al tachar película: {e}")
            await interaction.response.send_message(
                f"❌ Error al tachar la película: {str(e)}",
                ephemeral=True
            )
    
    async def cancel_callback(self, interaction: discord.Interaction):
        """Callback cuando se cancela."""
        embed = discord.Embed(
            title="❌ Cancelado",
            description="No se tachó ninguna película.",
            color=discord.Color.greyple()
        )
        
        self.select_menu.disabled = True
        self.confirm_button.disabled = True
        self.cancel_button.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def on_timeout(self):
        """Se ejecuta cuando expira el timeout."""
        self.select_menu.disabled = True
        self.confirm_button.disabled = True
        self.cancel_button.disabled = True

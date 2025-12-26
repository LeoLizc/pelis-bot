"""
Cog para comandos de gestión de películas.
"""
import random
import discord
from discord import app_commands
from discord.ext import commands
import logging

from src.google_docs import MovieDocReader
from src.bot.views.movie_views import StrikeMovieView, MovieSelectionView
from src.bot.views.pagination import PaginationView

logger = logging.getLogger(__name__)


class MoviesCog(commands.Cog):
    """Comandos para listar, elegir y tachar películas."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.doc_reader = MovieDocReader()
    
    @app_commands.command(name="listar", description="Lista las películas del documento")
    @app_commands.describe(filtro="Filtrar por: todas, pendientes o vistas")
    @app_commands.choices(filtro=[
        app_commands.Choice(name="Todas", value="todas"),
        app_commands.Choice(name="Pendientes", value="pendientes"),
        app_commands.Choice(name="Vistas", value="vistas"),
    ])
    async def listar(self, interaction: discord.Interaction, filtro: str = "pendientes"):
        """Muestra la lista de películas según el filtro seleccionado."""
        await interaction.response.defer()
        
        try:
            if filtro == "todas":
                movies = self.doc_reader.get_movies()
                title = "📽️ Todas las películas"
                color = discord.Color.blue()
            elif filtro == "vistas":
                movies = self.doc_reader.get_seen_movies()
                title = "✅ Películas vistas"
                color = discord.Color.green()
            else:
                movies = self.doc_reader.get_pending_movies()
                title = "⏳ Películas pendientes"
                color = discord.Color.orange()
            
            if not movies:
                embed = discord.Embed(
                    title=title,
                    description="No hay películas en esta categoría.",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Crear vista paginada
            view = PaginationView(
                items=movies,
                title=title,
                formatter=lambda m: m.to_display(),
                color=color
            )
            
            await interaction.followup.send(embed=view.get_embed(), view=view)
            
        except Exception as e:
            logger.error(f"Error en comando listar: {e}")
            await interaction.followup.send(f"❌ Error al obtener las películas: {str(e)}")
    
    @app_commands.command(name="elegir_azar", description="Elige una película al azar")
    @app_commands.describe(proponente="Filtrar por proponente (opcional)")
    async def elegir_azar(self, interaction: discord.Interaction, proponente: str = None):
        """Elige una película pendiente al azar, opcionalmente filtrada por proponente."""
        await interaction.response.defer()
        
        try:
            if proponente:
                # Filtrar por proponente y solo pendientes
                all_movies = self.doc_reader.get_movies_by_proponent(proponente)
                movies = [m for m in all_movies if m.is_pending]
                filter_text = f"propuestas por **{proponente}**"
            else:
                movies = self.doc_reader.get_pending_movies()
                filter_text = "pendientes"
            
            if not movies:
                embed = discord.Embed(
                    title="🎲 Sin resultados",
                    description=f"No hay películas {filter_text}.",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Elegir al azar
            movie = random.choice(movies)
            
            embed = discord.Embed(
                title="🎲 ¡Película elegida!",
                description=f"De {len(movies)} películas {filter_text}:",
                color=discord.Color.green()
            )
            embed.add_field(name="🎬 Título", value=movie.titulo, inline=False)
            embed.add_field(name="👤 Propuesta por", value=movie.proponente, inline=True)
            
            # Crear vista con botón para tachar
            view = StrikeMovieView(movie, self.doc_reader, interaction.user)
            
            await interaction.followup.send(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error en comando elegir_azar: {e}")
            await interaction.followup.send(f"❌ Error: {str(e)}")
    
    @app_commands.command(name="tachar", description="Tacha una película como vista")
    @app_commands.describe(nombre="Nombre de la película a tachar")
    async def tachar(self, interaction: discord.Interaction, nombre: str):
        """Busca y tacha una película por nombre."""
        await interaction.response.defer()
        
        try:
            matches = self.doc_reader.find_movie_by_title(nombre, pending_only=True)
            
            if not matches:
                embed = discord.Embed(
                    title="❌ No encontrada",
                    description=f"No se encontró ninguna película pendiente que coincida con **{nombre}**.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)
                return
            
            if len(matches) == 1:
                # Solo una coincidencia - mostrar confirmación
                movie = matches[0]
                embed = discord.Embed(
                    title="⚠️ Confirmar tachado",
                    description=f"¿Deseas tachar esta película?",
                    color=discord.Color.yellow()
                )
                embed.add_field(name="🎬 Título", value=movie.titulo, inline=False)
                embed.add_field(name="👤 Propuesta por", value=movie.proponente, inline=True)
                
                view = StrikeMovieView(movie, self.doc_reader, interaction.user)
                await interaction.followup.send(embed=embed, view=view)
            else:
                # Múltiples coincidencias - mostrar selección
                embed = discord.Embed(
                    title="🔍 Múltiples coincidencias",
                    description=f"Se encontraron **{len(matches)}** películas. Selecciona cuál tachar:",
                    color=discord.Color.blue()
                )
                
                for i, movie in enumerate(matches[:10], 1):
                    embed.add_field(
                        name=f"{i}. {movie.titulo}",
                        value=f"Propuesta por: {movie.proponente}",
                        inline=False
                    )
                
                view = MovieSelectionView(matches[:10], self.doc_reader, interaction.user)
                await interaction.followup.send(embed=embed, view=view)
                
        except Exception as e:
            logger.error(f"Error en comando tachar: {e}")
            await interaction.followup.send(f"❌ Error: {str(e)}")
    
    @app_commands.command(name="buscar", description="Busca películas por título o proponente")
    @app_commands.describe(
        termino="Término de búsqueda",
        tipo="Buscar por título o proponente"
    )
    @app_commands.choices(tipo=[
        app_commands.Choice(name="Título", value="titulo"),
        app_commands.Choice(name="Proponente", value="proponente"),
    ])
    async def buscar(self, interaction: discord.Interaction, termino: str, tipo: str = "titulo"):
        """Busca películas por título o proponente."""
        await interaction.response.defer()
        
        try:
            if tipo == "proponente":
                movies = self.doc_reader.get_movies_by_proponent(termino)
            else:
                movies = self.doc_reader.find_movie_by_title(termino, pending_only=False)
            
            if not movies:
                embed = discord.Embed(
                    title="🔍 Sin resultados",
                    description=f"No se encontraron películas para: **{termino}**",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Crear vista paginada
            view = PaginationView(
                items=movies,
                title=f"🔍 Resultados para: {termino}",
                formatter=lambda m: m.to_display(),
                color=discord.Color.blue()
            )
            
            await interaction.followup.send(embed=view.get_embed(), view=view)
            
        except Exception as e:
            logger.error(f"Error en comando buscar: {e}")
            await interaction.followup.send(f"❌ Error: {str(e)}")


async def setup(bot: commands.Bot):
    """Función de setup para cargar el cog."""
    await bot.add_cog(MoviesCog(bot))

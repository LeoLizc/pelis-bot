"""
Cog para el sistema de votación de películas.
"""
import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Set
import discord
from discord import app_commands
from discord.ext import commands
import logging

from src.google_docs import MovieDocReader
from src.models import Movie
from src.bot.views.voting_views import VotingView

logger = logging.getLogger(__name__)


class VotingSession:
    """Representa una sesión de votación activa."""
    
    def __init__(
        self,
        movies: List[Movie],
        max_votes_per_user: int,
        duration_minutes: int,
        channel_id: int,
        creator_id: int
    ):
        self.movies = movies
        self.max_votes_per_user = max_votes_per_user
        self.duration_minutes = duration_minutes
        self.channel_id = channel_id
        self.creator_id = creator_id
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(minutes=duration_minutes)
        
        # Votos: {movie_index: set(user_ids)}
        self.votes: Dict[int, Set[int]] = {i: set() for i in range(len(movies))}
        # Registro de votos por usuario: {user_id: [movie_indices]}
        self.user_votes: Dict[int, List[int]] = {}
        
        self.is_active = True
        self.message: discord.Message = None
    
    def add_vote(self, user_id: int, movie_index: int) -> tuple[bool, str]:
        """
        Añade un voto de un usuario a una película.
        
        Returns:
            Tuple (éxito, mensaje)
        """
        if not self.is_active:
            return False, "La votación ha terminado."
        
        if movie_index < 0 or movie_index >= len(self.movies):
            return False, "Película no válida."
        
        # Verificar si ya votó por esta película
        if user_id in self.votes[movie_index]:
            return False, "Ya votaste por esta película."
        
        # Verificar límite de votos
        user_vote_count = len(self.user_votes.get(user_id, []))
        if user_vote_count >= self.max_votes_per_user:
            return False, f"Ya usaste tus {self.max_votes_per_user} voto(s)."
        
        # Registrar voto
        self.votes[movie_index].add(user_id)
        if user_id not in self.user_votes:
            self.user_votes[user_id] = []
        self.user_votes[user_id].append(movie_index)
        
        return True, f"¡Voto registrado para **{self.movies[movie_index].titulo}**!"
    
    def remove_vote(self, user_id: int, movie_index: int) -> tuple[bool, str]:
        """Quita un voto de un usuario."""
        if not self.is_active:
            return False, "La votación ha terminado."
        
        if user_id not in self.votes[movie_index]:
            return False, "No has votado por esta película."
        
        self.votes[movie_index].remove(user_id)
        self.user_votes[user_id].remove(movie_index)
        
        return True, f"Voto removido de **{self.movies[movie_index].titulo}**."
    
    def get_results(self) -> List[tuple[Movie, int]]:
        """Obtiene los resultados ordenados por votos."""
        results = [
            (self.movies[i], len(voters))
            for i, voters in self.votes.items()
        ]
        return sorted(results, key=lambda x: x[1], reverse=True)
    
    def get_winner(self) -> tuple[Movie, int]:
        """Obtiene la película ganadora."""
        results = self.get_results()
        if not results:
            return None, 0
        return results[0]
    
    def time_remaining(self) -> timedelta:
        """Retorna el tiempo restante de la votación."""
        remaining = self.end_time - datetime.now()
        return remaining if remaining.total_seconds() > 0 else timedelta(0)


class VotingCog(commands.Cog):
    """Sistema de votación para elegir películas."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.doc_reader = MovieDocReader()
        # Sesiones activas por canal
        self.active_sessions: Dict[int, VotingSession] = {}
    
    @app_commands.command(name="votacion", description="Inicia una votación de películas")
    @app_commands.describe(
        cantidad="Cantidad de películas a elegir (2-10)",
        max_votos="Máximo de votos por usuario (1-5)",
        tiempo="Duración en minutos (1-60)"
    )
    async def votacion(
        self,
        interaction: discord.Interaction,
        cantidad: int = 3,
        max_votos: int = 1,
        tiempo: int = 5
    ):
        """Inicia una sesión de votación."""
        await interaction.response.defer()
        
        # Validaciones
        if cantidad < 2 or cantidad > 10:
            await interaction.followup.send("❌ La cantidad debe estar entre 2 y 10.")
            return
        
        if max_votos < 1 or max_votos > 5:
            await interaction.followup.send("❌ Los votos máximos deben estar entre 1 y 5.")
            return
        
        if tiempo < 1 or tiempo > 60:
            await interaction.followup.send("❌ El tiempo debe estar entre 1 y 60 minutos.")
            return
        
        # Verificar si ya hay una votación activa
        if interaction.channel_id in self.active_sessions:
            session = self.active_sessions[interaction.channel_id]
            if session.is_active:
                await interaction.followup.send(
                    "❌ Ya hay una votación activa en este canal. "
                    "Espera a que termine o usa `/cancelar_votacion`."
                )
                return
        
        try:
            # Obtener películas pendientes
            pending_movies = self.doc_reader.get_pending_movies()
            
            if len(pending_movies) < cantidad:
                await interaction.followup.send(
                    f"❌ No hay suficientes películas pendientes. "
                    f"Disponibles: {len(pending_movies)}, Solicitadas: {cantidad}"
                )
                return
            
            # Seleccionar películas al azar
            selected_movies = random.sample(pending_movies, cantidad)
            
            # Crear sesión de votación
            session = VotingSession(
                movies=selected_movies,
                max_votes_per_user=max_votos,
                duration_minutes=tiempo,
                channel_id=interaction.channel_id,
                creator_id=interaction.user.id
            )
            self.active_sessions[interaction.channel_id] = session
            
            # Crear embed de votación
            embed = self._create_voting_embed(session)
            
            # Crear vista con botones
            view = VotingView(session, self)
            
            message = await interaction.followup.send(embed=embed, view=view)
            session.message = message
            
            # Programar fin de votación
            self.bot.loop.create_task(
                self._end_voting_after(session, tiempo * 60)
            )
            
        except Exception as e:
            logger.error(f"Error al iniciar votación: {e}")
            await interaction.followup.send(f"❌ Error al iniciar votación: {str(e)}")
    
    def _create_voting_embed(self, session: VotingSession) -> discord.Embed:
        """Crea el embed de votación."""
        embed = discord.Embed(
            title="🗳️ ¡Votación de películas!",
            description=(
                f"**Votos por persona:** {session.max_votes_per_user}\n"
                f"**Tiempo restante:** {int(session.time_remaining().total_seconds() // 60)} minutos\n\n"
                "Haz clic en los botones para votar:"
            ),
            color=discord.Color.purple()
        )
        
        for i, movie in enumerate(session.movies):
            vote_count = len(session.votes[i])
            embed.add_field(
                name=f"{i + 1}. {movie.titulo}",
                value=f"👤 {movie.proponente} | 🗳️ {vote_count} voto(s)",
                inline=False
            )
        
        embed.set_footer(text="Los votos se actualizan en tiempo real")
        return embed
    
    async def update_voting_message(self, session: VotingSession):
        """Actualiza el mensaje de votación con los votos actuales."""
        if session.message:
            try:
                embed = self._create_voting_embed(session)
                view = VotingView(session, self)
                await session.message.edit(embed=embed, view=view)
            except discord.NotFound:
                pass
            except Exception as e:
                logger.error(f"Error al actualizar mensaje de votación: {e}")
    
    async def _end_voting_after(self, session: VotingSession, seconds: int):
        """Finaliza la votación después del tiempo especificado."""
        await asyncio.sleep(seconds)
        
        if not session.is_active:
            return
        
        session.is_active = False
        
        # Obtener resultados
        winner, votes = session.get_winner()
        results = session.get_results()
        
        # Crear embed de resultados
        embed = discord.Embed(
            title="🎉 ¡Votación finalizada!",
            color=discord.Color.gold()
        )
        
        if winner:
            embed.add_field(
                name="🏆 Ganadora",
                value=f"**{winner.titulo}**\nPropuesta por: {winner.proponente}\nVotos: {votes}",
                inline=False
            )
            
            # Mostrar ranking completo
            ranking = "\n".join([
                f"{'🥇' if i == 0 else '🥈' if i == 1 else '🥉' if i == 2 else f'{i+1}.'} "
                f"{movie.titulo} - {count} voto(s)"
                for i, (movie, count) in enumerate(results)
            ])
            embed.add_field(name="📊 Resultados", value=ranking, inline=False)
        else:
            embed.description = "No hubo votos en esta votación."
        
        # Crear vista con botón para tachar ganadora
        from src.bot.views.movie_views import StrikeMovieView
        view = None
        if winner:
            view = StrikeMovieView(winner, self.doc_reader, None, label="Tachar Ganadora")
        
        try:
            channel = self.bot.get_channel(session.channel_id)
            if channel:
                await channel.send(embed=embed, view=view)
                
                # Deshabilitar botones del mensaje original
                if session.message:
                    await session.message.edit(view=None)
        except Exception as e:
            logger.error(f"Error al finalizar votación: {e}")
        
        # Limpiar sesión
        if session.channel_id in self.active_sessions:
            del self.active_sessions[session.channel_id]
    
    @app_commands.command(name="cancelar_votacion", description="Cancela la votación activa")
    async def cancelar_votacion(self, interaction: discord.Interaction):
        """Cancela una votación activa."""
        if interaction.channel_id not in self.active_sessions:
            await interaction.response.send_message(
                "❌ No hay ninguna votación activa en este canal.",
                ephemeral=True
            )
            return
        
        session = self.active_sessions[interaction.channel_id]
        
        # Solo el creador o admins pueden cancelar
        if (session.creator_id != interaction.user.id and 
            not interaction.user.guild_permissions.administrator):
            await interaction.response.send_message(
                "❌ Solo el creador de la votación o un administrador puede cancelarla.",
                ephemeral=True
            )
            return
        
        session.is_active = False
        del self.active_sessions[interaction.channel_id]
        
        if session.message:
            try:
                await session.message.edit(view=None)
            except:
                pass
        
        await interaction.response.send_message("✅ Votación cancelada.")
    
    @app_commands.command(name="estado_votacion", description="Muestra el estado de la votación actual")
    async def estado_votacion(self, interaction: discord.Interaction):
        """Muestra el estado actual de la votación."""
        if interaction.channel_id not in self.active_sessions:
            await interaction.response.send_message(
                "❌ No hay ninguna votación activa en este canal.",
                ephemeral=True
            )
            return
        
        session = self.active_sessions[interaction.channel_id]
        embed = self._create_voting_embed(session)
        
        remaining = session.time_remaining()
        minutes = int(remaining.total_seconds() // 60)
        seconds = int(remaining.total_seconds() % 60)
        
        embed.set_footer(text=f"Tiempo restante: {minutes}m {seconds}s")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Función de setup para cargar el cog."""
    await bot.add_cog(VotingCog(bot))

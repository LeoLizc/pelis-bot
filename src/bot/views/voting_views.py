"""
Vistas relacionadas con el sistema de votación.
"""
import random
import discord
from discord.ui import View, Button
from typing import TYPE_CHECKING, List

from src.utils.logger import BotLogger

if TYPE_CHECKING:
    from src.bot.cogs.voting import VotingSession, VotingCog
    from src.models import Movie

logger = BotLogger(__name__)


class VotingView(View):
    """Vista con botones para votar por películas."""
    
    def __init__(self, session: "VotingSession", cog: "VotingCog"):
        super().__init__(timeout=None)  # Sin timeout, controlado por la sesión
        self.session = session
        self.cog = cog
        
        # Crear botones para cada película
        for i, movie in enumerate(session.movies):
            button = VoteButton(
                movie_index=i,
                movie_title=movie.titulo,
                session=session,
                cog=cog
            )
            self.add_item(button)


class VoteButton(Button):
    """Botón individual para votar por una película."""
    
    def __init__(
        self,
        movie_index: int,
        movie_title: str,
        session: "VotingSession",
        cog: "VotingCog"
    ):
        # Colores diferentes para cada botón
        styles = [
            discord.ButtonStyle.primary,
            discord.ButtonStyle.success,
            discord.ButtonStyle.secondary,
            discord.ButtonStyle.primary,
            discord.ButtonStyle.success,
        ]
        
        super().__init__(
            label=f"{movie_index + 1}",
            style=styles[movie_index % len(styles)],
            custom_id=f"vote_{session.channel_id}_{movie_index}"
        )
        self.movie_index = movie_index
        self.movie_title = movie_title
        self.session = session
        self.cog = cog
    
    async def callback(self, interaction: discord.Interaction):
        """Callback cuando se hace clic en el botón de voto."""
        if not self.session.is_active:
            await interaction.response.send_message(
                "❌ Esta votación ya ha terminado.",
                ephemeral=True
            )
            return
        
        user_id = interaction.user.id
        guild_name = interaction.guild.name if interaction.guild else "DM"
        
        # Verificar si ya votó por esta película (toggle)
        if user_id in self.session.votes[self.movie_index]:
            success, message = self.session.remove_vote(user_id, self.movie_index)
            if success:
                logger.vote(
                    movie_title=self.movie_title,
                    user=str(interaction.user),
                    guild=guild_name,
                    removed=True
                )
        else:
            success, message = self.session.add_vote(user_id, self.movie_index)
            if success:
                logger.vote(
                    movie_title=self.movie_title,
                    user=str(interaction.user),
                    guild=guild_name,
                    removed=False
                )
        
        # Mostrar mensaje efímero
        await interaction.response.send_message(message, ephemeral=True)
        
        # Actualizar el mensaje de votación si el voto fue exitoso
        if success:
            await self.cog.update_voting_message(self.session)


class TieBreakView(View):
    """Vista para manejar empates en votaciones."""
    
    def __init__(
        self,
        tied_movies: List["Movie"],
        cog: "VotingCog",
        original_session: "VotingSession",
        doc_reader
    ):
        super().__init__(timeout=300)  # 5 minutos para decidir
        self.tied_movies = tied_movies
        self.cog = cog
        self.original_session = original_session
        self.doc_reader = doc_reader
    
    @discord.ui.button(label="🎲 Elegir al azar", style=discord.ButtonStyle.primary)
    async def random_winner(self, interaction: discord.Interaction, button: Button):
        """Elige un ganador aleatorio entre los empatados."""
        winner = random.choice(self.tied_movies)
        
        logger.action(
            "TIE_BREAK_RANDOM",
            user=str(interaction.user),
            guild=interaction.guild.name if interaction.guild else "DM",
            details=f"Ganador aleatorio: {winner.titulo}"
        )
        
        embed = discord.Embed(
            title="🎲 ¡Ganador por sorteo!",
            description="Se eligió aleatoriamente entre los empatados:",
            color=discord.Color.gold()
        )
        embed.add_field(
            name="🏆 Ganadora",
            value=f"**{winner.titulo}**\nPropuesta por: {winner.proponente}",
            inline=False
        )
        
        # Lista de empatados
        tied_list = "\n".join([f"• {m.titulo}" for m in self.tied_movies])
        embed.add_field(
            name="🤝 Películas empatadas",
            value=tied_list,
            inline=False
        )
        
        # Botón para tachar ganadora
        from src.bot.views.movie_views import StrikeMovieView
        view = StrikeMovieView(winner, self.doc_reader, None, label="Tachar Ganadora")
        
        # Deshabilitar botones actuales
        self.disable_all_items()
        await interaction.message.edit(view=self)
        
        await interaction.response.send_message(embed=embed, view=view)
    
    @discord.ui.button(label="🗳️ Nueva votación", style=discord.ButtonStyle.success)
    async def new_voting(self, interaction: discord.Interaction, button: Button):
        """Inicia una nueva votación solo con los empatados."""
        from src.bot.cogs.voting import VotingSession
        
        logger.action(
            "TIE_BREAK_REVOTE",
            user=str(interaction.user),
            guild=interaction.guild.name if interaction.guild else "DM",
            details=f"Nueva votación con {len(self.tied_movies)} películas"
        )
        
        # Crear nueva sesión con las películas empatadas
        new_session = VotingSession(
            movies=self.tied_movies,
            max_votes_per_user=1,  # Un voto para desempatar
            duration_minutes=3,    # 3 minutos para desempatar
            channel_id=interaction.channel_id,
            creator_id=interaction.user.id
        )
        self.cog.active_sessions[interaction.channel_id] = new_session
        
        # Crear embed de votación
        embed = discord.Embed(
            title="🗳️ ¡Desempate!",
            description=(
                f"**Votos por persona:** 1\n"
                f"**Tiempo:** 3 minutos\n\n"
                "Vota para desempatar:"
            ),
            color=discord.Color.purple()
        )
        
        for i, movie in enumerate(self.tied_movies):
            embed.add_field(
                name=f"{i + 1}. {movie.titulo}",
                value=f"👤 {movie.proponente} | 🗳️ 0 voto(s)",
                inline=False
            )
        
        embed.set_footer(text="Los votos se actualizan en tiempo real")
        
        # Crear vista con botones
        view = VotingView(new_session, self.cog)
        
        # Deshabilitar botones actuales
        self.disable_all_items()
        await interaction.message.edit(view=self)
        
        message = await interaction.response.send_message(embed=embed, view=view)
        
        # Obtener el mensaje enviado
        new_session.message = await interaction.original_response()
        
        # Programar fin de votación
        import asyncio
        self.cog.bot.loop.create_task(
            self.cog._end_voting_after(new_session, 3 * 60)
        )
    
    def disable_all_items(self):
        """Deshabilita todos los botones."""
        for item in self.children:
            item.disabled = True

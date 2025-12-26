"""
Vistas relacionadas con el sistema de votación.
"""
import discord
from discord.ui import View, Button
from typing import TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from src.bot.cogs.voting import VotingSession, VotingCog

logger = logging.getLogger(__name__)


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
        
        # Verificar si ya votó por esta película (toggle)
        if user_id in self.session.votes[self.movie_index]:
            success, message = self.session.remove_vote(user_id, self.movie_index)
        else:
            success, message = self.session.add_vote(user_id, self.movie_index)
        
        # Mostrar mensaje efímero
        await interaction.response.send_message(message, ephemeral=True)
        
        # Actualizar el mensaje de votación si el voto fue exitoso
        if success:
            await self.cog.update_voting_message(self.session)

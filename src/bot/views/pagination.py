"""
Vista de paginación para listas largas.
"""
import discord
from discord.ui import View, Button
from typing import List, Callable, Any
import logging

logger = logging.getLogger(__name__)

# Películas por página
ITEMS_PER_PAGE = 10


class PaginationView(View):
    """Vista con botones de paginación para listas largas."""
    
    def __init__(
        self,
        items: List[Any],
        title: str,
        formatter: Callable[[Any], str],
        color: discord.Color = discord.Color.blue(),
        items_per_page: int = ITEMS_PER_PAGE,
        timeout: float = 180.0
    ):
        """
        Args:
            items: Lista de elementos a paginar
            title: Título del embed
            formatter: Función que convierte cada item a string para mostrar
            color: Color del embed
            items_per_page: Elementos por página
            timeout: Tiempo de expiración de los botones
        """
        super().__init__(timeout=timeout)
        self.items = items
        self.title = title
        self.formatter = formatter
        self.color = color
        self.items_per_page = items_per_page
        self.current_page = 0
        self.total_pages = max(1, (len(items) + items_per_page - 1) // items_per_page)
        
        self._update_buttons()
    
    def _update_buttons(self):
        """Actualiza el estado de los botones según la página actual."""
        self.clear_items()
        
        # Botón primera página
        first_btn = Button(
            emoji="⏮️",
            style=discord.ButtonStyle.secondary,
            disabled=self.current_page == 0
        )
        first_btn.callback = self.first_page
        self.add_item(first_btn)
        
        # Botón página anterior
        prev_btn = Button(
            emoji="◀️",
            style=discord.ButtonStyle.primary,
            disabled=self.current_page == 0
        )
        prev_btn.callback = self.prev_page
        self.add_item(prev_btn)
        
        # Indicador de página
        page_indicator = Button(
            label=f"{self.current_page + 1}/{self.total_pages}",
            style=discord.ButtonStyle.secondary,
            disabled=True
        )
        self.add_item(page_indicator)
        
        # Botón página siguiente
        next_btn = Button(
            emoji="▶️",
            style=discord.ButtonStyle.primary,
            disabled=self.current_page >= self.total_pages - 1
        )
        next_btn.callback = self.next_page
        self.add_item(next_btn)
        
        # Botón última página
        last_btn = Button(
            emoji="⏭️",
            style=discord.ButtonStyle.secondary,
            disabled=self.current_page >= self.total_pages - 1
        )
        last_btn.callback = self.last_page
        self.add_item(last_btn)
    
    def get_embed(self) -> discord.Embed:
        """Genera el embed para la página actual."""
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_items = self.items[start_idx:end_idx]
        
        embed = discord.Embed(
            title=self.title,
            description=f"Total: **{len(self.items)}** películas",
            color=self.color
        )
        
        # Formatear items con números
        formatted_items = []
        for i, item in enumerate(page_items, start=start_idx + 1):
            formatted_items.append(f"`{i}.` {self.formatter(item)}")
        
        content = "\n".join(formatted_items) if formatted_items else "No hay elementos."
        embed.add_field(name="Lista", value=content, inline=False)
        
        embed.set_footer(
            text=f"Página {self.current_page + 1} de {self.total_pages} • "
                 f"Mostrando {start_idx + 1}-{min(end_idx, len(self.items))} de {len(self.items)}"
        )
        
        return embed
    
    async def first_page(self, interaction: discord.Interaction):
        """Ir a la primera página."""
        self.current_page = 0
        self._update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)
    
    async def prev_page(self, interaction: discord.Interaction):
        """Ir a la página anterior."""
        self.current_page = max(0, self.current_page - 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)
    
    async def next_page(self, interaction: discord.Interaction):
        """Ir a la página siguiente."""
        self.current_page = min(self.total_pages - 1, self.current_page + 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)
    
    async def last_page(self, interaction: discord.Interaction):
        """Ir a la última página."""
        self.current_page = self.total_pages - 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)
    
    async def on_timeout(self):
        """Deshabilitar botones cuando expira el timeout."""
        self.clear_items()

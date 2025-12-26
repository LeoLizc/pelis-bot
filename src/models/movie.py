"""
Modelo de datos para una película.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Movie:
    """Representa una película del documento."""
    
    titulo: str
    proponente: str
    seen: bool = False
    start_index: Optional[int] = None
    end_index: Optional[int] = None
    
    @property
    def is_pending(self) -> bool:
        """Retorna True si la película está pendiente (no vista)."""
        return not self.seen
    
    def __str__(self) -> str:
        status = "✅" if self.seen else "⏳"
        return f"{status} {self.titulo} - {self.proponente}"
    
    def to_display(self, show_status: bool = True) -> str:
        """Formato para mostrar en Discord."""
        if show_status:
            status = "~~" if self.seen else ""
            return f"{status}{self.titulo}{status} - {self.proponente}"
        return f"{self.titulo} - {self.proponente}"

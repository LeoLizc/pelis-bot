"""
Lector y escritor de documentos de Google Docs.
"""
import re
from typing import List, Optional, Tuple
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.models import Movie
import config


class MovieDocReader:
    """
    Clase para leer y modificar el documento de películas en Google Docs.
    """
    
    SCOPES = ['https://www.googleapis.com/auth/documents']
    
    def __init__(self, credentials_path: str = None, document_id: str = None):
        self.credentials_path = credentials_path or config.GOOGLE_CREDENTIALS_PATH
        self.document_id = document_id or config.GOOGLE_DOC_ID
        self.service = None
        self._connect()
    
    def _connect(self):
        """Establece conexión con la API de Google Docs."""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.SCOPES
            )
            self.service = build('docs', 'v1', credentials=credentials)
        except Exception as e:
            raise ConnectionError(f"Error al conectar con Google Docs: {e}")
    
    def fetch_content(self) -> dict:
        """
        Obtiene el contenido completo del documento en formato JSON.
        """
        try:
            document = self.service.documents().get(documentId=self.document_id).execute()
            return document
        except HttpError as e:
            raise Exception(f"Error al obtener el documento: {e}")
    
    def _find_delimiter_index(self, content: List[dict]) -> Optional[int]:
        """
        Encuentra el índice donde comienza el contenido a ignorar (última página).
        Busca delimitadores como '-----' o saltos de página.
        Retorna el índice del elemento donde se debe cortar.
        """
        last_page_break_index = None
        
        for i, element in enumerate(content):
            # Detectar sectionBreak (salto de sección/página)
            if 'sectionBreak' in element:
                last_page_break_index = i
                continue
            
            if 'paragraph' in element:
                paragraph = element['paragraph']
                
                # Detectar pageBreak dentro de un párrafo
                for elem in paragraph.get('elements', []):
                    if 'pageBreak' in elem:
                        last_page_break_index = i
                        break
                
                # Buscar delimitadores de texto como '-----'
                for elem in paragraph.get('elements', []):
                    if 'textRun' in elem:
                        text = elem['textRun'].get('content', '').strip()
                        # Verificar si el texto contiene un delimitador
                        for delimiter in config.PAGE_DELIMITERS:
                            if text == delimiter or delimiter in text:
                                # Encontramos un delimitador visual
                                return i
        
        # Si hay un salto de página/sección, usar ese como punto de corte
        if last_page_break_index is not None:
            return last_page_break_index
        
        return None
    
    def _parse_movie_line(self, text: str, is_strikethrough: bool, 
                          start_index: int, end_index: int) -> Optional[Movie]:
        """
        Parsea una línea de texto para extraer información de la película.
        Formato esperado: "Título - Proponente"
        """
        text = text.strip()
        if not text or text in config.PAGE_DELIMITERS:
            return None
        
        # Intentar separar título y proponente
        separator = config.MOVIE_SEPARATOR
        if separator in text:
            parts = text.rsplit(separator, 1)
            if len(parts) == 2:
                titulo = parts[0].strip()
                proponente = parts[1].strip()
            else:
                titulo = text
                proponente = "Desconocido"
        else:
            titulo = text
            proponente = "Desconocido"
        
        if not titulo:
            return None
        
        return Movie(
            titulo=titulo,
            proponente=proponente,
            seen=is_strikethrough,
            start_index=start_index,
            end_index=end_index
        )
    
    def get_movies(self) -> List[Movie]:
        """
        Obtiene la lista de películas del documento.
        Detecta cuáles están tachadas (vistas) y cuáles no.
        """
        document = self.fetch_content()
        content = document.get('body', {}).get('content', [])
        
        # Encontrar dónde termina el contenido relevante
        delimiter_index = self._find_delimiter_index(content)
        if delimiter_index:
            content = content[:delimiter_index]
        
        movies = []
        
        for element in content:
            if 'paragraph' not in element:
                continue
            
            paragraph = element['paragraph']
            paragraph_text = ""
            is_strikethrough = False
            start_index = None
            end_index = None
            
            for elem in paragraph.get('elements', []):
                if 'textRun' not in elem:
                    continue
                
                text_run = elem['textRun']
                text = text_run.get('content', '')
                text_style = text_run.get('textStyle', {})
                
                # Verificar si tiene tachado
                if text_style.get('strikethrough', False):
                    is_strikethrough = True
                
                # Guardar índices para poder tachar después
                if start_index is None:
                    start_index = elem.get('startIndex', 0)
                end_index = elem.get('endIndex', 0)
                
                paragraph_text += text
            
            # Limpiar y parsear
            paragraph_text = paragraph_text.strip()
            if paragraph_text and paragraph_text not in ['\n', '']:
                movie = self._parse_movie_line(
                    paragraph_text, 
                    is_strikethrough, 
                    start_index, 
                    end_index
                )
                if movie:
                    movies.append(movie)
        
        return movies
    
    def get_pending_movies(self) -> List[Movie]:
        """Obtiene solo las películas pendientes (no vistas)."""
        return [m for m in self.get_movies() if m.is_pending]
    
    def get_seen_movies(self) -> List[Movie]:
        """Obtiene solo las películas vistas (tachadas)."""
        return [m for m in self.get_movies() if m.seen]
    
    def get_movies_by_proponent(self, proponent: str) -> List[Movie]:
        """
        Obtiene películas filtradas por proponente.
        Búsqueda case-insensitive.
        """
        proponent_lower = proponent.lower()
        return [
            m for m in self.get_movies() 
            if proponent_lower in m.proponente.lower()
        ]
    
    def strike_movie(self, movie: Movie) -> bool:
        """
        Aplica formato tachado a una película en el documento.
        
        Args:
            movie: Película a tachar (debe tener start_index y end_index)
            
        Returns:
            True si se tachó correctamente, False en caso contrario
        """
        if movie.start_index is None or movie.end_index is None:
            raise ValueError("La película no tiene índices de posición válidos")
        
        try:
            requests = [
                {
                    'updateTextStyle': {
                        'range': {
                            'startIndex': movie.start_index,
                            'endIndex': movie.end_index
                        },
                        'textStyle': {
                            'strikethrough': True
                        },
                        'fields': 'strikethrough'
                    }
                }
            ]
            
            self.service.documents().batchUpdate(
                documentId=self.document_id,
                body={'requests': requests}
            ).execute()
            
            return True
        except HttpError as e:
            raise Exception(f"Error al tachar la película: {e}")
    
    def find_movie_by_title(self, title: str, pending_only: bool = True) -> List[Movie]:
        """
        Busca películas por título (búsqueda difusa).
        
        Args:
            title: Título a buscar
            pending_only: Si True, solo busca en películas pendientes
            
        Returns:
            Lista de películas que coinciden
        """
        from thefuzz import fuzz
        
        movies = self.get_pending_movies() if pending_only else self.get_movies()
        title_lower = title.lower()
        
        matches = []
        for movie in movies:
            # Coincidencia exacta
            if title_lower == movie.titulo.lower():
                matches.insert(0, movie)
            # Coincidencia parcial
            elif title_lower in movie.titulo.lower():
                matches.append(movie)
            # Coincidencia difusa (fuzzy)
            elif fuzz.ratio(title_lower, movie.titulo.lower()) > 70:
                matches.append(movie)
        
        return matches

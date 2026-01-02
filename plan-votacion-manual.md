# Plan de Implementación: Votación Manual de Películas

Este plan detalla los pasos para implementar una nueva funcionalidad que permita a los usuarios seleccionar manualmente qué películas incluir en una votación, en lugar de seleccionarlas al azar.

## 1. Diseño de la Interacción (UX)

Dado que hay muchas películas (>25), no podemos mostrarlas todas en un solo menú de selección. El flujo propuesto es interactivo:

1.  **Comando Inicial:** El usuario ejecuta `/votacion_manual [tiempo] [max_votos]`.
2.  **Panel de Configuración:** El bot responde con un mensaje (Embed) que muestra:
    *   Configuración actual (Tiempo, Votos/usuario).
    *   Lista de películas seleccionadas (inicialmente vacía).
    *   **Botones:**
        *   `➕ Agregar Película`: Abre un buscador.
        *   `🚀 Iniciar Votación`: Inicia la votación (deshabilitado si hay < 2 películas).
        *   `❌ Cancelar`: Cierra el configurador.
3.  **Búsqueda y Selección:**
    *   Al hacer clic en `➕ Agregar Película`, se abre un **Modal** pidiendo el nombre.
    *   El bot busca coincidencias en el documento.
    *   Si hay ambigüedad (varias coincidencias), muestra un selector efímero para elegir la correcta.
    *   Una vez elegida, se añade a la lista del Panel de Configuración.
4.  **Inicio:** Al hacer clic en `🚀 Iniciar Votación`, se reutiliza el sistema de votación existente (`VotingSession`) con las películas elegidas.

## 2. Componentes Técnicos Necesarios

### A. Nuevas Vistas (`src/bot/views/voting_setup_view.py`)

Necesitamos crear un nuevo archivo para manejar la lógica de la interfaz de configuración.

1.  **`VotingSetupView`**:
    *   Mantiene el estado temporal (`selected_movies`, `config`).
    *   Gestiona los botones principales.
    *   Actualiza el Embed cada vez que se añade una película.

2.  **`MovieSearchModal`**:
    *   Formulario simple con un campo de texto para buscar la película.

3.  **`MovieDisambiguationView`**:
    *   Vista efímera con un `SelectMenu` para cuando la búsqueda devuelve múltiples resultados.

### B. Modificaciones en `VotingCog` (`src/bot/cogs/voting.py`)

1.  **Nuevo Comando `/votacion_manual`**:
    *   Inicializa el `VotingSetupView`.
    *   No crea la `VotingSession` inmediatamente, espera a que el usuario confirme.

2.  **Método `start_manual_voting`**:
    *   Método helper para transformar la lista de películas manuales en una `VotingSession` activa.

## 3. Plan de Trabajo Paso a Paso

### Paso 1: Crear las Vistas de Configuración
Crear el archivo `src/bot/views/voting_setup_view.py` con las clases `VotingSetupView`, `MovieSearchModal` y `MovieDisambiguationView`.

*   **Detalle:** Implementar la lógica de búsqueda usando `doc_reader.find_movie_by_title`.

### Paso 2: Implementar el Comando
En `src/bot/cogs/voting.py`, añadir el comando `/votacion_manual`.

*   **Detalle:** Debe instanciar `VotingSetupView` y enviarla.

### Paso 3: Conectar el Inicio de Votación
Hacer que el botón `🚀 Iniciar Votación` de `VotingSetupView` llame a una función en el Cog que cree la `VotingSession` real.

*   **Detalle:** Reutilizar la lógica existente de `VotingSession` y `VotingView` para que la experiencia de votación sea consistente con la automática.

## 4. Ejemplo de Código (Esqueleto)

```python
# src/bot/views/voting_setup_view.py

class VotingSetupView(discord.ui.View):
    def __init__(self, doc_reader, callback_start):
        self.selected_movies = []
        self.doc_reader = doc_reader
        self.callback_start = callback_start
        ...

    @discord.ui.button(label="Agregar Película", style=discord.ButtonStyle.secondary)
    async def add_movie(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MovieSearchModal(self))

    @discord.ui.button(label="Iniciar Votación", style=discord.ButtonStyle.primary)
    async def start_voting(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.callback_start(interaction, self.selected_movies)
```

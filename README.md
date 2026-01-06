# 🎬 Pelis Bot

Bot de Discord para gestionar una lista de películas almacenada en Google Docs.

## ✨ Características

- 📖 **Lee películas** desde un documento de Google Docs
- 👁️ **Detecta estado**: Identifica películas vistas (tachadas) y pendientes
- 🎲 **Selección aleatoria**: Elige películas al azar con filtros opcionales
- 🗳️ **Sistema de votación**: Votación grupal con tiempo límite
- ✅ **Marca como vista**: Tacha automáticamente las películas en el documento

## 📁 Estructura del Proyecto

```
pelis-bot/
├── main.py                 # Punto de entrada
├── config.py               # Configuración central
├── requirements.txt        # Dependencias
├── .env.example           # Plantilla de variables de entorno
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── movie.py       # Modelo de película
│   ├── google_docs/
│   │   ├── __init__.py
│   │   └── reader.py      # Lector/escritor de Google Docs
│   └── bot/
│       ├── __init__.py
│       ├── client.py      # Cliente principal del bot
│       ├── cogs/
│       │   ├── __init__.py
│       │   ├── movies.py  # Comandos de películas
│       │   └── voting.py  # Sistema de votación
│       └── views/
│           ├── __init__.py
│           ├── movie_views.py   # Botones de películas
│           └── voting_views.py  # Botones de votación
├── tests/
│   ├── __init__.py
│   └── test_reader.py     # Tests del lector
└── data/
    └── .gitkeep
```

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd pelis-bot
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Google Cloud

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto
3. Habilita la **Google Docs API**
4. Crea una **Cuenta de Servicio** (Service Account)
5. Descarga el archivo JSON de credenciales
6. Renómbralo a `service_account.json` y colócalo en la raíz del proyecto
7. **Importante**: Comparte el documento de Google Docs con el email de la cuenta de servicio (con permisos de editor)

### 5. Configurar Discord Bot

1. Ve al [Portal de Desarrolladores de Discord](https://discord.com/developers/applications)
2. Crea una nueva aplicación
3. En la sección "Bot", crea un bot
4. Copia el token del bot
5. En "OAuth2" > "URL Generator":
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: `Send Messages`, `Use Slash Commands`, `Embed Links`, `Read Message History`
6. Usa la URL generada para invitar el bot a tu servidor

### 6. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env` con tus valores:

```env
DISCORD_TOKEN=tu_token_de_discord
GOOGLE_DOC_ID=1wxsL6Qe5hbXHXqTWTHcFbwB6Rkdr6Ao2ez2mXyyjtrY
GOOGLE_CREDENTIALS_PATH=service_account.json
```

### 7. Ejecutar el bot

```bash
python main.py
```

## 📝 Comandos

### Gestión de Películas
| Comando | Parámetros | Descripción |
|---------|------------|-------------|
| `/listar` | `[filtro]` | Lista películas: `Todas`, `Pendientes` (por defecto) o `Vistas`. |
| `/elegir_azar` | `[proponente]` | Elige una película pendiente al azar. Opcionalmente filtra por proponente. |
| `/buscar` | `<termino> [tipo]` | Busca películas por `Título` (por defecto) o `Proponente`. |
| `/tachar` | `<nombre>` | Busca una película pendiente y la marca como vista en el documento. |

### Sistema de Votación
| Comando | Parámetros | Descripción |
|---------|------------|-------------|
| `/votacion` | `[cantidad] [max_votos] [tiempo] [proponente]` | Inicia una votación con películas elegidas al azar. Opcionalmente filtra por proponente. |
| `/votacion_manual`| `[max_votos] [tiempo]` | Inicia una votación permitiendo elegir las películas manualmente. |
| `/estado_votacion` | - | Muestra el estado actual, votos y tiempo restante. |
| `/finalizar_votacion` | - | Termina la votación inmediatamente y muestra al ganador. |
| `/cancelar_votacion` | - | Cancela la votación activa sin mostrar resultados. |

> **Nota**: Los comandos `/finalizar_votacion` y `/cancelar_votacion` solo pueden ser usados por el creador de la votación o un administrador.

## 🧪 Tests

Ejecuta el test de lectura del documento:

```bash
python -m tests.test_reader
```

## 📋 Formato del Documento

El documento de Google Docs debe seguir este formato:

```
Película 1 - NombreProponente
Película 2 - OtroProponente
~~Película Vista - Proponente~~
...
-----
Contenido a ignorar (última página)
```

- Cada línea es una película
- Formato: `Título - Proponente`
- Las películas tachadas (strikethrough) se consideran vistas
- El delimitador `-----` marca el inicio del contenido a ignorar

## 🛠️ Desarrollo

### Agregar nuevos comandos

1. Crea un nuevo archivo en `src/bot/cogs/`
2. Define un `Cog` con tus comandos
3. Añade la carga del cog en `src/bot/client.py`

### Modificar el parser

El parser de películas está en `src/google_docs/reader.py`. Puedes modificar:
- `PAGE_DELIMITERS` en `config.py` para los delimitadores
- `MOVIE_SEPARATOR` para el separador título-proponente
- `_parse_movie_line()` para lógica de parsing personalizada

## 📄 Licencia

MIT

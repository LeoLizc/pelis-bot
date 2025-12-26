"""
Script de prueba para verificar la lectura del documento de Google Docs.
Ejecutar: python -m tests.test_reader
"""
import sys
import os

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.google_docs import MovieDocReader


def test_connection():
    """Prueba la conexión con Google Docs."""
    print("=" * 50)
    print("TEST: Conexión con Google Docs")
    print("=" * 50)
    
    try:
        reader = MovieDocReader()
        print("✅ Conexión exitosa")
        return reader
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None


def test_fetch_content(reader: MovieDocReader):
    """Prueba la obtención del contenido del documento."""
    print("\n" + "=" * 50)
    print("TEST: Obtener contenido del documento")
    print("=" * 50)
    
    try:
        content = reader.fetch_content()
        title = content.get('title', 'Sin título')
        print(f"✅ Documento obtenido: {title}")
        return True
    except Exception as e:
        print(f"❌ Error al obtener contenido: {e}")
        return False


def test_get_movies(reader: MovieDocReader):
    """Prueba la obtención de películas."""
    print("\n" + "=" * 50)
    print("TEST: Obtener lista de películas")
    print("=" * 50)
    
    try:
        movies = reader.get_movies()
        print(f"✅ Total de películas encontradas: {len(movies)}")
        
        pending = [m for m in movies if m.is_pending]
        seen = [m for m in movies if m.seen]
        
        print(f"   📌 Pendientes: {len(pending)}")
        print(f"   ✅ Vistas: {len(seen)}")
        
        return movies
    except Exception as e:
        print(f"❌ Error al obtener películas: {e}")
        return []


def test_display_movies(movies, limit=10):
    """Muestra algunas películas de ejemplo."""
    print("\n" + "=" * 50)
    print(f"TEST: Mostrar primeras {limit} películas")
    print("=" * 50)
    
    if not movies:
        print("⚠️ No hay películas para mostrar")
        return
    
    for i, movie in enumerate(movies[:limit], 1):
        status = "✅" if movie.seen else "⏳"
        print(f"{i}. {status} {movie.titulo}")
        print(f"      Proponente: {movie.proponente}")
        if movie.start_index:
            print(f"      Índices: [{movie.start_index}, {movie.end_index}]")


def test_filter_by_proponent(reader: MovieDocReader, proponent: str = None):
    """Prueba el filtrado por proponente."""
    print("\n" + "=" * 50)
    print("TEST: Filtrar por proponente")
    print("=" * 50)
    
    try:
        movies = reader.get_movies()
        
        if not movies:
            print("⚠️ No hay películas")
            return
        
        # Obtener lista de proponentes únicos
        proponents = set(m.proponente for m in movies)
        print(f"Proponentes encontrados: {', '.join(proponents)}")
        
        if proponent:
            filtered = reader.get_movies_by_proponent(proponent)
            print(f"\nPelículas de '{proponent}': {len(filtered)}")
            for m in filtered[:5]:
                print(f"  - {m.titulo}")
                
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Ejecuta todos los tests."""
    print("\n🎬 TESTS DEL LECTOR DE GOOGLE DOCS 🎬\n")
    
    # Test 1: Conexión
    reader = test_connection()
    if not reader:
        print("\n❌ No se puede continuar sin conexión")
        return
    
    # Test 2: Obtener contenido
    if not test_fetch_content(reader):
        print("\n❌ No se puede continuar sin contenido")
        return
    
    # Test 3: Obtener películas
    movies = test_get_movies(reader)
    
    # Test 4: Mostrar películas
    test_display_movies(movies)
    
    # Test 5: Filtrar por proponente
    test_filter_by_proponent(reader)
    
    print("\n" + "=" * 50)
    print("✅ TESTS COMPLETADOS")
    print("=" * 50)


if __name__ == "__main__":
    main()

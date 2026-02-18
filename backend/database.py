"""
Módulo de base de datos SQLite para gestión de películas
"""

import sqlite3

DATABASE_PATH = "movies.db"


def init_db():
    """Inicializa la base de datos y crea la tabla de películas si no existe"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            year INTEGER NOT NULL,
            director TEXT NOT NULL
        )
    """
    )

    # Insertar datos de ejemplo si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM movies")
    if cursor.fetchone()[0] == 0:
        sample_movies = [
            ("El Padrino", 1972, "Francis Ford Coppola"),
            ("Pulp Fiction", 1994, "Quentin Tarantino"),
            ("El Caballero Oscuro", 2008, "Christopher Nolan"),
            ("Forrest Gump", 1994, "Robert Zemeckis"),
            ("Inception", 2010, "Christopher Nolan"),
            ("Matrix", 1999, "Lana y Lilly Wachowski"),
            ("Interstellar", 2014, "Christopher Nolan"),
            ("Gladiador", 2000, "Ridley Scott"),
        ]
        cursor.executemany(
            "INSERT INTO movies (title, year, director) VALUES (?, ?, ?)", sample_movies
        )

    conn.commit()
    conn.close()
    print(f"✓ Base de datos inicializada en {DATABASE_PATH}")


def get_connection():
    """Retorna una conexión a la base de datos"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Para acceder a columnas por nombre
    return conn


def get_all_movies():
    """Obtiene todas las películas de la base de datos"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM movies")
    movies = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return movies


def get_movie_by_id(movie_id):
    """Obtiene una película por su ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM movies WHERE id = ?", (movie_id,))
    movie = cursor.fetchone()
    conn.close()
    return dict(movie) if movie else None


def add_movie(title, year, director):
    """Agrega una nueva película a la base de datos"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO movies (title, year, director) VALUES (?, ?, ?)", (title, year, director)
    )
    movie_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return movie_id

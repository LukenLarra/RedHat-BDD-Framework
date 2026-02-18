"""
Módulo de base de datos PostgreSQL con SQLAlchemy ORM para gestión de películas
"""
import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import DeclarativeBase, Session, scoped_session, sessionmaker

# Leer DATABASE_URL de variables de entorno (configurada por el framework)
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/movies_db')

# Crear engine de SQLAlchemy
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

# Configurar session factory con scoped_session para thread-safety
session_factory = sessionmaker(bind=engine)
SessionLocal = scoped_session(session_factory)


# Definir Base para modelos ORM
class Base(DeclarativeBase):
    pass


# Modelo ORM para la tabla movies
class Movie(Base):
    __tablename__ = 'movies'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    year = Column(Integer, nullable=False)
    director = Column(String(255), nullable=False)
    
    def to_dict(self):
        """Convierte el objeto ORM a diccionario para JSON"""
        return {
            'id': self.id,
            'title': self.title,
            'year': self.year,
            'director': self.director
        }


def init_db():
    """Inicializa la base de datos y crea las tablas si no existen"""
    # Crear todas las tablas definidas en Base
    Base.metadata.create_all(engine)
    
    # Insertar datos de ejemplo si la tabla está vacía
    session = SessionLocal()
    try:
        movie_count = session.query(Movie).count()
        if movie_count == 0:
            sample_movies = [
                Movie(title='El Padrino', year=1972, director='Francis Ford Coppola'),
                Movie(title='Pulp Fiction', year=1994, director='Quentin Tarantino'),
                Movie(title='El Caballero Oscuro', year=2008, director='Christopher Nolan'),
                Movie(title='Forrest Gump', year=1994, director='Robert Zemeckis'),
                Movie(title='Inception', year=2010, director='Christopher Nolan'),
                Movie(title='Matrix', year=1999, director='Lana y Lilly Wachowski'),
                Movie(title='Interstellar', year=2014, director='Christopher Nolan'),
                Movie(title='Gladiador', year=2000, director='Ridley Scott')
            ]
            session.add_all(sample_movies)
            session.commit()
            print(f"✓ Base de datos inicializada con {len(sample_movies)} películas de ejemplo")
        else:
            print(f"✓ Base de datos ya contiene {movie_count} películas")
    except Exception as e:
        session.rollback()
        print(f"✗ Error al inicializar base de datos: {e}")
        raise
    finally:
        session.close()


def get_all_movies():
    """Obtiene todas las películas de la base de datos"""
    session = SessionLocal()
    try:
        movies = session.query(Movie).all()
        return [movie.to_dict() for movie in movies]
    finally:
        session.close()


def get_movie_by_id(movie_id):
    """Obtiene una película por su ID"""
    session = SessionLocal()
    try:
        movie = session.query(Movie).filter(Movie.id == movie_id).first()
        return movie.to_dict() if movie else None
    finally:
        session.close()


def add_movie(title, year, director):
    """Agrega una nueva película a la base de datos"""
    session = SessionLocal()
    try:
        new_movie = Movie(title=title, year=year, director=director)
        session.add(new_movie)
        session.commit()
        session.refresh(new_movie)  # Refrescar para obtener el ID generado
        movie_id = new_movie.id
        return movie_id
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()

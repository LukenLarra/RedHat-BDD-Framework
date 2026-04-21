"""
PostgreSQL database module using SQLAlchemy ORM for movie management
"""

import os

from sqlalchemy import Column, Integer, String, create_engine, text
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker

# Read DATABASE_URL from environment variables (configured by the framework)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/movies_db")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

# Configure session factory with scoped_session for thread-safety
session_factory = sessionmaker(bind=engine)
SessionLocal = scoped_session(session_factory)


# Define Base for ORM models
class Base(DeclarativeBase):
    pass


# ORM model for the movies table
class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    year = Column(Integer, nullable=False)
    director = Column(String(255), nullable=False)

    def to_dict(self):
        """Convert the ORM object to a dictionary for JSON."""
        return {"id": self.id, "title": self.title, "year": self.year, "director": self.director}


def init_db(reset: bool = False):
    """Initialize the database and create tables if they do not exist.

    Always truncates the movies table and reloads 8 sample movies.
    The reset parameter is kept for backward compatibility.
    """
    # Create all tables defined in Base
    Base.metadata.create_all(engine)

    session = SessionLocal()
    try:
        # Always truncate the movies table
        if engine.dialect.name == "postgresql":
            session.execute(text("TRUNCATE TABLE movies RESTART IDENTITY CASCADE"))
        else:
            session.query(Movie).delete()
        session.commit()

        # Always load sample movies
        sample_movies = [
            Movie(title="The Godfather", year=1972, director="Francis Ford Coppola"),
            Movie(title="Pulp Fiction", year=1994, director="Quentin Tarantino"),
            Movie(title="The Dark Knight", year=2008, director="Christopher Nolan"),
            Movie(title="Forrest Gump", year=1994, director="Robert Zemeckis"),
            Movie(title="Inception", year=2010, director="Christopher Nolan"),
            Movie(title="The Matrix", year=1999, director="Lana and Lilly Wachowski"),
            Movie(title="Interstellar", year=2014, director="Christopher Nolan"),
            Movie(title="Gladiator", year=2000, director="Ridley Scott"),
        ]
        session.add_all(sample_movies)
        session.commit()
        print(f"[OK] Database reset with {len(sample_movies)} sample movies")
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Error initializing database: {e}")
        raise
    finally:
        session.close()


def get_all_movies():
    """Retrieve all movies from the database."""
    session = SessionLocal()
    try:
        movies = session.query(Movie).all()
        return [movie.to_dict() for movie in movies]
    finally:
        session.close()


def get_movie_by_id(movie_id):
    """Retrieve a movie by its ID."""
    session = SessionLocal()
    try:
        movie = session.query(Movie).filter(Movie.id == movie_id).first()
        return movie.to_dict() if movie else None
    finally:
        session.close()


def add_movie(title, year, director):
    """Add a new movie to the database."""
    session = SessionLocal()
    try:
        new_movie = Movie(title=title, year=year, director=director)
        session.add(new_movie)
        session.commit()
        session.refresh(new_movie)  # Refresh to obtain generated ID
        movie_id = new_movie.id
        return movie_id
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

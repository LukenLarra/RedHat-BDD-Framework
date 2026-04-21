"""
FastAPI API for movie management
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from contextlib import asynccontextmanager

import database
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from schema import MovieCreate, MovieResponse, MoviesResponse


# Replace the startup event with a lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager to initialize and clean up resources."""
    # Initialize the database
    database.init_db()
    yield
    # Perform any cleanup if necessary


# Create FastAPI application
app = FastAPI(
    title="Movies API",
    description="REST API for movie management with FastAPI",
    version="1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def home():
    """Root API endpoint."""
    return {
        "message": "Movies API",
        "version": "1.0",
        "endpoints": {
            "GET /api/movies": "Retrieve all movies",
            "GET /api/movies/{id}": "Retrieve a movie by ID",
            "POST /api/movies": "Create a new movie",
        },
        "documentation": {"swagger": "/docs", "redoc": "/redoc"},
    }


@app.get("/api/movies", response_model=MoviesResponse)
async def get_movies():
    """Retrieve all movies."""
    try:
        movies = database.get_all_movies()
        return {"success": True, "count": len(movies), "data": movies}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@app.get("/api/movies/{movie_id}", response_model=MovieResponse)
async def get_movie(movie_id: int):
    """Retrieve a movie by its ID."""
    try:
        movie = database.get_movie_by_id(movie_id)
        if movie:
            return {"success": True, "data": movie}
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@app.post("/api/movies", response_model=MovieResponse, status_code=status.HTTP_201_CREATED)
async def create_movie(movie: MovieCreate):
    """Create a new movie."""
    try:
        movie_id = database.add_movie(movie.title, movie.year, movie.director)

        return {
            "success": True,
            "data": {
                "id": movie_id,
                "title": movie.title,
                "year": movie.year,
                "director": movie.director,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "movies-api"}


@app.post("/api/test/reset")
async def reset_test_database():
    """Reset the database to its initial state for tests only."""
    if os.getenv("ENABLE_TEST_API", "false").lower() != "true":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    try:
        database.init_db(reset=True)
        return {"success": True, "message": "Test database restored"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


if __name__ == "__main__":
    import uvicorn

    # Read configuration from environment variables
    host = os.environ.get("API_HOST", "0.0.0.0")
    port = int(os.environ.get("API_PORT", "8000"))
    reload = os.environ.get("API_RELOAD", "1") == "1"

    print("🚀 Starting Movies API...")
    print(f"📍 URL: http://{host}:{port}")
    print(f"📝 Swagger docs: http://localhost:{port}/docs")
    print(f"📝 ReDoc docs: http://localhost:{port}/redoc")
    print(f"🔧 Reload mode: {reload}")

    uvicorn.run("app:app", host=host, port=port, reload=reload)

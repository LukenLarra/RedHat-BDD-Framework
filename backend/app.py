"""
API Flask para gestión de películas
"""

import os
from typing import Any, Dict, List

import database
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


# Modelos Pydantic para validación de datos
class MovieCreate(BaseModel):
    """Modelo para crear una nueva película"""

    title: str = Field(..., min_length=1, description="Título de la película")
    year: int = Field(..., gt=1800, lt=2100, description="Año de lanzamiento")
    director: str = Field(..., min_length=1, description="Director de la película")


class Movie(MovieCreate):
    """Modelo de película con ID"""

    id: int


class MovieResponse(BaseModel):
    """Respuesta estándar para una película"""

    success: bool
    data: Movie


class MoviesResponse(BaseModel):
    """Respuesta estándar para lista de películas"""

    success: bool
    count: int
    data: List[Dict[str, Any]]


class ErrorResponse(BaseModel):
    """Respuesta de error"""

    success: bool
    error: str


# Crear aplicación FastAPI
app = FastAPI(
    title="API de Películas",
    description="API REST para gestión de películas con FastAPI",
    version="1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar la base de datos al arrancar
database.init_db()


@app.get("/")
async def home():
    """Endpoint raíz de la API"""
    return {
        "message": "API de Películas",
        "version": "1.0",
        "endpoints": {
            "GET /api/movies": "Obtener todas las películas",
            "GET /api/movies/{id}": "Obtener película por ID",
            "POST /api/movies": "Crear nueva película",
        },
        "documentation": {"swagger": "/docs", "redoc": "/redoc"},
    }


@app.route("/api/movies", methods=["GET"])
def get_movies():
    """Obtiene todas las películas"""
    try:
        movies = database.get_all_movies()
        return {"success": True, "count": len(movies), "data": movies}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.route("/api/movies/<int:movie_id>", methods=["GET"])
def get_movie(movie_id):
    """Obtiene una película específica por ID"""
    try:
        movie = database.get_movie_by_id(movie_id)
        if movie:
            return {"success": True, "data": movie}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Película no encontrada"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.route("/api/movies", methods=["POST"])
def create_movie(movie: MovieCreate):
    """Crea una nueva película"""
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.route("/health", methods=["GET"])
def health_check():
    """Endpoint para verificar el estado de la API"""
    return {"status": "healthy", "service": "movies-api"}


if __name__ == "__main__":
    import uvicorn

    # Leer configuración desde variables de entorno
    host = os.environ.get("API_HOST", "0.0.0.0")
    port = int(os.environ.get("API_PORT", "8000"))
    reload = os.environ.get("API_RELOAD", "1") == "1"

    print("🚀 Iniciando API de Películas...")
    print(f"📍 URL: http://{host}:{port}")
    print(f"📝 Documentación Swagger: http://localhost:{port}/docs")
    print(f"📝 Documentación ReDoc: http://localhost:{port}/redoc")
    print(f"🔧 Reload mode: {reload}")

    uvicorn.run("app:app", host=host, port=port, reload=reload)

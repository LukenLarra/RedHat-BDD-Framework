"""
API FastAPI para gestión de películas
"""
<<<<<<< pre-commit

import os

import database
from flask import Flask, jsonify, request
from flask_cors import CORS
=======
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import database
from contextlib import asynccontextmanager
from schema import MovieCreate, Movie, MovieResponse, MoviesResponse, ErrorResponse

# Replace the startup event with a lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager to initialize and clean up resources."""
    # Initialize the database
    database.init_db()
    yield
    # Perform any cleanup if necessary
>>>>>>> main

# Crear aplicación FastAPI
app = FastAPI(
    title="API de Películas",
    description="API REST para gestión de películas con FastAPI",
    version="1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

<<<<<<< pre-commit

@app.route("/")
def home():
    """Endpoint raíz de la API"""
    return jsonify(
        {
            "message": "API de Películas",
            "version": "1.0",
            "endpoints": {
                "GET /api/movies": "Obtener todas las películas",
                "GET /api/movies/<id>": "Obtener película por ID",
                "POST /api/movies": "Crear nueva película",
            },
        }
    )


@app.route("/api/movies", methods=["GET"])
def get_movies():
    """Obtiene todas las películas"""
    try:
        movies = database.get_all_movies()
        return jsonify({"success": True, "count": len(movies), "data": movies}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/movies/<int:movie_id>", methods=["GET"])
def get_movie(movie_id):
=======
@app.get("/")
async def home():
    """Endpoint raíz de la API"""
    return {
        'message': 'API de Películas',
        'version': '1.0',
        'endpoints': {
            'GET /api/movies': 'Obtener todas las películas',
            'GET /api/movies/{id}': 'Obtener película por ID',
            'POST /api/movies': 'Crear nueva película'
        },
        'documentation': {
            'swagger': '/docs',
            'redoc': '/redoc'
        }
    }

@app.get("/api/movies", response_model=MoviesResponse)
async def get_movies():
    """Obtiene todas las películas"""
    try:
        movies = database.get_all_movies()
        return {
            'success': True,
            'count': len(movies),
            'data': movies
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/api/movies/{movie_id}", response_model=MovieResponse)
async def get_movie(movie_id: int):
>>>>>>> main
    """Obtiene una película específica por ID"""
    try:
        movie = database.get_movie_by_id(movie_id)
        if movie:
<<<<<<< pre-commit
            return jsonify({"success": True, "data": movie}), 200
        else:
            return jsonify({"success": False, "error": "Película no encontrada"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/movies", methods=["POST"])
def create_movie():
    """Crea una nueva película"""
    try:
        data = request.get_json()

        # Validar datos requeridos
        if not all(key in data for key in ["title", "year", "director"]):
            return (
                jsonify(
                    {"success": False, "error": "Faltan campos requeridos: title, year, director"}
                ),
                400,
            )

        movie_id = database.add_movie(data["title"], data["year"], data["director"])

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Película creada exitosamente",
                    "data": {
                        "id": movie_id,
                        "title": data["title"],
                        "year": data["year"],
                        "director": data["director"],
                    },
                }
            ),
            201,
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """Endpoint para verificar el estado de la API"""
    return jsonify({"status": "healthy", "service": "movies-api"}), 200


if __name__ == "__main__":
    # Leer configuración desde variables de entorno
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    host = os.environ.get("FLASK_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_PORT", "5000"))

    print("🚀 Iniciando API de Películas...")
    print(f"📍 URL: http://{host}:{port}")
    print("📝 Documentación: http://localhost:5000/")
    print(f"🔧 Debug mode: {debug_mode}")

    app.run(debug=debug_mode, host=host, port=port)
=======
            return {
                'success': True,
                'data': movie
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Película no encontrada'
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/api/movies", response_model=MovieResponse, status_code=status.HTTP_201_CREATED)
async def create_movie(movie: MovieCreate):
    """Crea una nueva película"""
    try:
        movie_id = database.add_movie(movie.title, movie.year, movie.director)
        
        return {
            'success': True,
            'data': {
                'id': movie_id,
                'title': movie.title,
                'year': movie.year,
                'director': movie.director
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/health")
async def health_check():
    """Endpoint para verificar el estado de la API"""
    return {
        'status': 'healthy',
        'service': 'movies-api'
    }

if __name__ == '__main__':
    import uvicorn
    
    # Leer configuración desde variables de entorno
    host = os.environ.get('API_HOST', '0.0.0.0')
    port = int(os.environ.get('API_PORT', '8000'))
    reload = os.environ.get('API_RELOAD', '1') == '1'
    
    print("🚀 Iniciando API de Películas...")
    print(f"📍 URL: http://{host}:{port}")
    print(f"📝 Documentación Swagger: http://localhost:{port}/docs")
    print(f"📝 Documentación ReDoc: http://localhost:{port}/redoc")
    print(f"🔧 Reload mode: {reload}")
    
    uvicorn.run("app:app", host=host, port=port, reload=reload)
>>>>>>> main

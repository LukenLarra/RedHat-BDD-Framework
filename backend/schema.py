from typing import List, Dict, Any
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
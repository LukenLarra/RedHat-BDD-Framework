"""
API Flask para gestión de películas
"""

import os

import database
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Habilitar CORS para permitir peticiones desde el frontend

# Inicializar la base de datos al arrancar
database.init_db()


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
    """Obtiene una película específica por ID"""
    try:
        movie = database.get_movie_by_id(movie_id)
        if movie:
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

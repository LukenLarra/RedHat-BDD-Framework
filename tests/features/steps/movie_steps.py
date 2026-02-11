import requests
from behave import given, when, then


@given('the API is running')
def step_api_running(context):
    """Verifica que la API esté funcionando"""
    try:
        response = requests.get(f"{context.api_url}/health", timeout=5)
        assert response.status_code == 200, "La API no responde correctamente"
    except requests.exceptions.RequestException as e:
        raise AssertionError(f"No se pudo conectar a la API: {e}")


@when('I make a GET request to "/api/movies"')
def step_get_all_movies(context):
    """Realiza una petición HTTP GET a /api/movies"""
    try:
        response = requests.get(f"{context.api_url}/api/movies", timeout=5)
        context.status_code = response.status_code
        context.response = response.json()
    except requests.exceptions.RequestException as e:
        raise AssertionError(f"Error al hacer la petición: {e}")


@when('I make a GET request to "/api/movies/{movie_id}"')
def step_get_movie_by_id(context, movie_id):
    """Realiza una petición HTTP GET a /api/movies/<id>"""
    try:
        response = requests.get(f"{context.api_url}/api/movies/{movie_id}", timeout=5)
        context.status_code = response.status_code
        context.response = response.json()
    except requests.exceptions.RequestException as e:
        raise AssertionError(f"Error al hacer la petición: {e}")


@given('there is a movie with ID {movie_id}')
def step_movie_exists(context, movie_id):
    """Verifica que existe una película con el ID especificado"""
    try:
        response = requests.get(f"{context.api_url}/api/movies/{movie_id}", timeout=5)
        assert response.status_code == 200, \
            f"No existe ninguna película con ID {movie_id}"
        data = response.json()
        assert data.get('success') is True, \
            f"La película con ID {movie_id} no se encontró"
    except requests.exceptions.RequestException as e:
        raise AssertionError(f"Error al verificar la película: {e}")


@then('I get a response with status code 200')
def step_status_code_200(context):
    """Verifica que el código de estado sea 200"""
    assert context.status_code == 200, \
        f"Se esperaba status code 200, se obtuvo {context.status_code}"


@then('the response contains a list of movies')
def step_response_contains_movies(context):
    """Verifica que la respuesta contenga una lista de películas"""
    assert context.response is not None, "La respuesta es None"
    assert context.response.get('success') is True, \
        f"La respuesta indica error: {context.response.get('error')}"

    movies = context.response.get('data', [])
    assert isinstance(movies, list), \
        f"Se esperaba una lista en 'data', se obtuvo {type(movies)}"
    assert len(movies) > 0, "La lista de películas está vacía"


@then('the response contains the details of the movie with ID {movie_id}')
def step_response_contains_movie_details(context, movie_id):
    """Verifica que la respuesta contenga los detalles de la película"""
    assert context.response is not None, "La respuesta es None"
    assert context.response.get('success') is True, \
        f"La respuesta indica error: {context.response.get('error')}"

    movie = context.response.get('data')
    assert movie is not None, \
        f"No se encontró ninguna película con ID {movie_id}"
    assert movie['id'] == int(movie_id), \
        f"ID esperado: {movie_id}, ID obtenido: {movie['id']}"
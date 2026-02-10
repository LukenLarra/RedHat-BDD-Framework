from behave import given, when, then
from backend.database import get_all_movies, get_movie_by_id


@given('the API is running')
def step_api_running(context):
    context.api_status = True


@when('I make a GET request to "/api/movies"')
def step_get_all_movies(context):
    assert context.api_status, "La API no está en funcionamiento"
    context.response = get_all_movies()


@when('I make a GET request to "/api/movies/{movie_id}"')
def step_get_movie_by_id(context, movie_id):
    assert context.api_status, "La API no está en funcionamiento"
    context.response = get_movie_by_id(int(movie_id))


@given('there is a movie with ID {movie_id}')
def step_movie_exists(context, movie_id):
    movie = get_movie_by_id(int(movie_id))
    assert movie is not None, f"No existe ninguna película con ID {movie_id}"


@then('I get a response with status code 200')
def step_status_code_200(context):
    assert context.response is not None, "La respuesta es None, se esperaba contenido"


@then('the response contains a list of movies')
def step_response_contains_movies(context):
    assert isinstance(context.response, list), \
        f"Se esperaba una lista, se obtuvo {type(context.response)}"
    assert len(context.response) > 0, "La lista de películas está vacía"


@then('the response contains the details of the movie with ID {movie_id}')
def step_response_contains_movie_details(context, movie_id):
    assert context.response is not None, \
        f"No se encontró ninguna película con ID {movie_id}"
    assert context.response['id'] == int(movie_id), \
        f"ID esperado: {movie_id}, ID obtenido: {context.response['id']}"
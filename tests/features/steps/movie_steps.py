import json

import requests
from behave import given, then, when


@given("the API is running")
def step_api_running(context):
    """Verifica que la API esté funcionando"""
    try:
        response = requests.get(f"{context.api_url}/health", timeout=5)
        assert response.status_code == 200, "La API no responde correctamente"
    except requests.exceptions.RequestException as e:
        raise AssertionError(f"No se pudo conectar a la API: {e}") from e


@when('I make a GET request to "/api/movies"')
def step_get_all_movies(context):
    """Realiza una petición HTTP GET a /api/movies"""
    try:
        response = requests.get(f"{context.api_url}/api/movies", timeout=5)
        context.status_code = response.status_code
        context.response = response.json()
    except requests.exceptions.RequestException as e:
        raise AssertionError(f"Error al hacer la petición: {e}") from e


@when('I make a GET request to "/api/movies/{movie_id}"')
def step_get_movie_by_id(context, movie_id):
    """Realiza una petición HTTP GET a /api/movies/<id>"""
    try:
        response = requests.get(f"{context.api_url}/api/movies/{movie_id}", timeout=5)
        context.status_code = response.status_code
        context.response = response.json()
    except requests.exceptions.RequestException as e:
        raise AssertionError(f"Error al hacer la petición: {e}") from e


@given("there is a movie with ID {movie_id}")
def step_movie_exists(context, movie_id):
    """Verifica que existe una película con el ID especificado"""
    try:
        response = requests.get(f"{context.api_url}/api/movies/{movie_id}", timeout=5)
        assert response.status_code == 200, f"No existe ninguna película con ID {movie_id}"
        data = response.json()
        assert data.get("success") is True, f"La película con ID {movie_id} no se encontró"
    except requests.exceptions.RequestException as e:
        raise AssertionError(f"Error al verificar la película: {e}") from e


@then("I get a response with status code {expected_status:d}")
def step_status_code(context, expected_status):
    """Verifica que el código de estado coincida con el esperado"""
    assert context.status_code == expected_status, (
        f"Se esperaba status code {expected_status}, se obtuvo {context.status_code}"
    )


@then("the response contains a list of movies")
def step_response_contains_movies(context):
    """Verifica que la respuesta contenga una lista de películas"""
    assert context.response is not None, "La respuesta es None"
    assert context.response.get("success") is True, (
        f"La respuesta indica error: {context.response.get('error')}"
    )

    movies = context.response.get("data", [])
    assert isinstance(movies, list), f"Se esperaba una lista en 'data', se obtuvo {type(movies)}"
    assert len(movies) > 0, "La lista de películas está vacía"


@then("the response contains the details of the movie with ID {movie_id}")
def step_response_contains_movie_details(context, movie_id):
    """Verifica que la respuesta contenga los detalles de la película"""
    assert context.response is not None, "La respuesta es None"
    assert context.response.get("success") is True, (
        f"La respuesta indica error: {context.response.get('error')}"
    )

    movie = context.response.get("data")
    assert movie is not None, f"No se encontró ninguna película con ID {movie_id}"
    assert movie["id"] == int(movie_id), f"ID esperado: {movie_id}, ID obtenido: {movie['id']}"


@then('the LLM confirms that "{condition}"')
def step_llm_confirms_condition(context, condition):
    """Verifica una condición usando el LLM (OpenAI) sobre la respuesta de la API"""
    assert context.response is not None, "No hay respuesta para evaluar con el LLM"
    assert getattr(context, "openai_client", None) is not None, "Cliente OpenAI no inicializado"

    prompt = f"""
    Eres un evaluador de pruebas de software estricto. Tu única tarea es validar si
    el payload JSON proporcionado cumple con la siguiente condición descrita por el usuario:
    "{condition}"

    Responde ESTRICTA Y ÚNICAMENTE con la palabra "True" si se cumple la condición, o "False" si no se cumple. Sin ningún otro texto.

    Response payload JSON recibido del backend a evaluar:
    {json.dumps(context.response, indent=2)}
    """

    try:
        completion = context.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a strict evaluator that ONLY outputs 'True' or 'False'.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=5,
            temperature=0,
        )
        text_response = completion.choices[0].message.content.strip()

        assert text_response.lower() == "true", (
            f"LLM Assertion fallida. El modelo evaluó la condición como: {text_response}"
        )
    except Exception as e:
        raise AssertionError(f"Error en la aserción con LLM: {e}") from e

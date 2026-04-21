import json

import requests
from behave import given, then, when


@given("the API is running")
def step_api_running(context):
    """Verifies the API is running"""
    try:
        response = requests.get(f"{context.api_url}/health", timeout=5)
        assert response.status_code == 200, "API is not responding correctly"
    except requests.exceptions.RequestException as e:
        raise AssertionError(f"Could not connect to the API: {e}") from e


@when('I make a GET request to "/api/movies"')
def step_get_all_movies(context):
    """Makes an HTTP GET request to /api/movies"""
    try:
        response = requests.get(f"{context.api_url}/api/movies", timeout=5)
        context.status_code = response.status_code
        context.response = response.json()
    except requests.exceptions.RequestException as e:
        raise AssertionError(f"Error making request: {e}") from e


@when('I make a GET request to "/api/movies/{movie_id}"')
def step_get_movie_by_id(context, movie_id):
    """Makes an HTTP GET request to /api/movies/<id>"""
    try:
        response = requests.get(f"{context.api_url}/api/movies/{movie_id}", timeout=5)
        context.status_code = response.status_code
        context.response = response.json()
    except requests.exceptions.RequestException as e:
        raise AssertionError(f"Error making request: {e}") from e


@given("there is a movie with ID {movie_id}")
def step_movie_exists(context, movie_id):
    """Verifies a movie with the given ID exists"""
    try:
        response = requests.get(f"{context.api_url}/api/movies/{movie_id}", timeout=5)
        assert response.status_code == 200, f"No movie found with ID {movie_id}"
        data = response.json()
        assert data.get("success") is True, f"Movie with ID {movie_id} not found"
    except requests.exceptions.RequestException as e:
        raise AssertionError(f"Error verifying movie: {e}") from e


@then("I get a response with status code {expected_status:d}")
def step_status_code(context, expected_status):
    """Verifies the status code matches the expected one"""
    assert context.status_code == expected_status, (
        f"Expected status code {expected_status}, got {context.status_code}"
    )


@then("the response contains a list of movies")
def step_response_contains_movies(context):
    """Verifies the response contains a list of movies"""
    assert context.response is not None, "Response is None"
    assert context.response.get("success") is True, (
        f"Response indicates error: {context.response.get('error')}"
    )

    movies = context.response.get("data", [])
    assert isinstance(movies, list), f"Expected a list in 'data', got {type(movies)}"
    assert len(movies) > 0, "Movie list is empty"


@then("the response contains the details of the movie with ID {movie_id}")
def step_response_contains_movie_details(context, movie_id):
    """Verifies the response contains the movie details"""
    assert context.response is not None, "Response is None"
    assert context.response.get("success") is True, (
        f"Response indicates error: {context.response.get('error')}"
    )

    movie = context.response.get("data")
    assert movie is not None, f"No movie found with ID {movie_id}"
    assert movie["id"] == int(movie_id), f"Expected ID: {movie_id}, got: {movie['id']}"


@then('the LLM confirms that "{condition}"')
def step_llm_confirms_condition(context, condition):
    """Verifies a condition using the LLM (OpenAI) against the API response"""
    assert context.response is not None, "No response to evaluate with the LLM"
    assert getattr(context, "openai_client", None) is not None, "OpenAI client not initialized"

    prompt = f"""
    You are a strict software test evaluator. Your task is to validate whether
    the provided JSON payload satisfies the following condition:
    "{condition}"

    Return ONLY a valid JSON object in this format, without markdown code blocks:
    {{
        "result": true or false,
        "reason": "Detailed explanation of why the condition is met or not based on the data"
    }}

    JSON response payload received from the backend to evaluate:
    {json.dumps(context.response, indent=2)}
    """

    try:
        completion = context.openai_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are a strict evaluator. Output ONLY valid JSON. No markdown markup.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
            temperature=0,
            response_format={"type": "json_object"},
        )
        text_response = completion.choices[0].message.content.strip()

        try:
            result_data = json.loads(text_response)
            is_valid = result_data.get("result", False)
            reason = result_data.get("reason", "No reason provided by the LLM")
        except json.JSONDecodeError:
            is_valid = False
            reason = f"Unexpected LLM response (not valid JSON): {text_response}"

        assert is_valid is True, f"LLM Assertion failed.\n  AI evaluation: {reason}"
    except Exception as e:
        import openai

        if isinstance(e, openai.RateLimitError):
            print(f"\n[AI SKIP] Skipping LLM assertion due to Groq rate limit: {e}")
            context.scenario.skip("Skipped: Groq rate limit reached")
            return
        raise AssertionError(f"Error in LLM assertion: {e}") from e

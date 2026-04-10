import requests
from behave import given, then, when
from bs4 import BeautifulSoup


def get_sanitized_dom(page):
    """Limpia el HTML para mantener solo la estructura importante de cara al LLM
    y minimizar tokens consumidos."""
    html_content = page.content()
    soup = BeautifulSoup(html_content, "html.parser")

    # Remover scripts, estilos y SVGs largos
    for tag in soup(["script", "style", "svg", "noscript", "meta", "link"]):
        tag.decompose()

    return str(soup)


@given("the frontend is running")
def step_impl_frontend_running(context):
    """Comprueba que el frontend responda."""
    try:
        response = requests.get(context.frontend_url, timeout=5)
        response.raise_for_status()
    except Exception as e:
        raise AssertionError(
            f"El frontend no está disponible en {context.frontend_url}: {e}"
        ) from e


@when("I open the frontend homepage")
def step_impl_open_frontend_homepage(context):
    print(f"Navegando a frontend: {context.frontend_url}")
    context.page.goto(context.frontend_url)
    context.page.wait_for_load_state("networkidle")


@then('the AI visually confirms that "{condition}"')
def step_impl_ai_visually_confirms(context, condition):
    """
    Envía el DOM limpio al LLM (Groq) para verificar si se cumple la condición semántica.
    """
    if not hasattr(context, "openai_client") or context.openai_client is None:
        raise ValueError("Cliente OpenAI/Groq no configurado (falta API KEY)")

    clean_html = get_sanitized_dom(context.page)

    prompt = f"""
Eres un analista de QA automatizado. A continuación, te proporciono el HTML simplificado del DOM de una página web actual:
```html
{clean_html}
```

El usuario quiere comprobar lo siguiente: "{condition}"

Responde ÚNICAMENTE en JSON con este formato exacto:
{{
  "confirmed": true|false,
  "reason": "Explicación breve de por qué se cumple o no en base al HTML provisto"
}}
    """

    response = context.openai_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    import json

    result_text = response.choices[0].message.content
    try:
        result = json.loads(result_text)
    except Exception as e:
        raise Exception(f"La respuesta de la IA no fue un JSON válido: {result_text}") from e

    assert result.get("confirmed") is True, (
        f"Verificación de IA falló. Razón: {result.get('reason')} - HTML truncado comprobado: {clean_html[:200]}"
    )
    print(f"✓ Confirmado por LLM: {result.get('reason')}")

import json
import time

import requests
from behave import given, then, when
from bs4 import BeautifulSoup


def get_sanitized_dom(page):
    """Limpia el HTML para mantener solo la estructura importante de cara al LLM
    y minimizar tokens consumidos."""
    html_content = page.content()
    soup = BeautifulSoup(html_content, "html.parser")

    for tag in soup(["script", "style", "svg", "noscript", "meta", "link"]):
        tag.decompose()

    return str(soup)


def get_interactive_dom_markdown(page):
    """Convierte el DOM de la página a un pseudo-markdown inyectando atributos ai-id
    para identificar inequívocamente con qué elementos interactuar."""
    html_content = page.content()
    soup = BeautifulSoup(html_content, "html.parser")

    # Remover ruido que no aporta UI interactiva
    for tag in soup(["script", "style", "svg", "noscript", "meta", "link", "head"]):
        tag.decompose()

    # Identificar elementos interactivos e inyectar in memory ai-id
    interactive_elements = soup.find_all(["input", "button", "a", "select", "textarea"])

    # Evaluar los selectores inyectando ai-id en el DOM de Playwright
    # Hacemos esto inyectando el ID directamente en el navegador real para que luego coincida.
    page.evaluate("""() => {
        let elements = document.querySelectorAll('input, button, a, select, textarea');
        elements.forEach((el, index) => {
            el.setAttribute('ai-id', String(index + 1));
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.tagName === 'SELECT') {
                el.setAttribute('dynamic-value', el.value || '');
            }
        });
    }""")

    # Volvemos a obtener el HTML tras inyectar ai-id y values localmente
    soup = BeautifulSoup(page.content(), "html.parser")
    interactive_elements = soup.find_all(["input", "button", "a", "select", "textarea"])

    markdown_lines = ["## Elementos Interactivos:\n"]
    for element in interactive_elements:
        ai_id = element.get("ai-id")
        if not ai_id:
            continue

        el_type = element.name.upper()
        el_text = element.get_text(strip=True)[:100]
        el_placeholder = element.get("placeholder", "")
        el_value = element.get("dynamic-value", "")

        info = f"[{el_type}]"
        if el_text and el_type not in ["INPUT", "TEXTAREA", "SELECT"]:
            info = f"[{el_type}: {el_text}]"
        else:
            parts = []
            if el_placeholder:
                parts.append(f"placeholder='{el_placeholder}'")
            if el_value:
                parts.append(f"current_value='{el_value}'")
            elif el_text and el_type in ["SELECT", "TEXTAREA"]:
                parts.append(f"current_value='{el_text}'")

            if parts:
                info = f"[{el_type}: {', '.join(parts)}]"

        markdown_lines.append(f'- {info} (ai-id="{ai_id}")')

    # Add error/success messages tracking to markdown to provide feedback to LLM
    alert_elements = soup.find_all(
        class_=lambda c: (
            c and ("error" in c.lower() or "success" in c.lower() or "alert" in c.lower())
        )
    )
    if alert_elements:
        markdown_lines.append("\n## Mensajes del Sistema:\n")
        for alert in alert_elements:
            markdown_lines.append(alert.get_text(strip=True))

    markdown_lines.append("\n## Contenido de la página (texto):\n")
    visible_text = soup.get_text(separator="\n", strip=True)[:1500]
    markdown_lines.append(visible_text)

    return "\n".join(markdown_lines)


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


@when('the AI acts on the page to "{goal}"')
def step_impl_ai_acts_on_page(context, goal):
    """
    Bucle ReAct (Razón + Acción) donde Llama-4 Scout decide qué clicks o fills hacer
    para cumplir el objetivo semántico propuesto.
    """
    if not hasattr(context, "openai_client") or context.openai_client is None:
        raise ValueError("Cliente OpenAI no configurado (falta API KEY)")

    step_num = 1
    while True:
        print(f"\n🔄 Step {step_num}: AI analyzing page for goal: '{goal}'")

        # 1. Obtener DOM en pseudo-markdown con IDs inyectados
        dom_markdown = get_interactive_dom_markdown(context.page)

        # 2. Prompt Llama-4 Scout
        prompt = f"""You are an intelligent web automation agent. Your goal is: "{goal}"

Current page format:
```markdown
{dom_markdown}
```

Decide your next action based on the interactive elements available. Return ONLY a JSON object with this structure:
{{
  "action": "click" | "fill" | "done",
  "ai_id": "the numerical ai-id string of the target element",
  "value": "string to fill (only if action is fill)",
  "reasoning": "brief explanation"
}}
IMPORTANT: After submitting a form with the filled steps, do not immediately assume you are done. Analyze the page again in the next step to see if the new element has appeared or if a success message is shown. Only respond with "action": "done" when you have visually confirmed the element or success message is present, or if there are no further actions needed."""

        try:
            response = context.openai_client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            result_text = response.choices[0].message.content
            action_data = json.loads(result_text)
        except Exception as e:
            print(f"❌ Error de LLM: {e}")
            raise

        print(f"  📋 Reasoning: {action_data.get('reasoning', 'N/A')}")

        action = action_data.get("action", "").lower()
        if action == "done":
            print("✅ Goal achieved!")
            return

        ai_id = action_data.get("ai_id")
        if not ai_id:
            raise ValueError(f"Action '{action}' requires 'ai_id'.")

        selector = f'[ai-id="{ai_id}"]'

        if action == "click":
            print(f"  🎯 Action: Clicking ai-id={ai_id}")
            context.page.locator(selector).click()
            context.page.wait_for_load_state("networkidle")
            time.sleep(0.5)

        elif action == "fill":
            value = action_data.get("value", "")
            print(f"  🎯 Action: Filling ai-id={ai_id} with '{value}'")
            context.page.locator(selector).fill(value)
            context.page.wait_for_load_state("networkidle")
            time.sleep(0.5)

        step_num += 1


@then('the AI visually confirms that "{condition}"')
def step_impl_ai_visually_confirms(context, condition):
    """
    Envía el DOM limpio al LLM (Groq) para verificar si se cumple la condición semántica.
    """
    if not hasattr(context, "openai_client") or context.openai_client is None:
        raise ValueError("Cliente OpenAI/Groq no configurado (falta API KEY)")

    clean_html = get_interactive_dom_markdown(context.page)

    prompt = f"""
Eres un analista de QA automatizado. Tienes el estatus pseudo-markdown actual:
```markdown
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
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        response_format={"type": "json_object"},
    )

    result_text = response.choices[0].message.content
    try:
        result = json.loads(result_text)
    except Exception as e:
        raise Exception(f"La respuesta de la IA no fue un JSON válido: {result_text}") from e

    assert result.get("confirmed") is True, (
        f"Verificación de IA falló.\nRazón: {result.get('reason')}\nDOM: {clean_html[:200]}"
    )
    print(f"✓ Confirmado por LLM: {result.get('reason')}")

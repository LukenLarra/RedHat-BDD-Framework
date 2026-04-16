import json

import requests
from behave import given, then, when
from bs4 import BeautifulSoup


def get_interactive_dom_markdown(page):
    """Convert the page DOM to pseudo-markdown by injecting ai-id attributes
    to uniquely identify interactive elements."""
    html_content = page.content()
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove noise that does not contribute to interactive UI
    for tag in soup(["script", "style", "svg", "noscript", "meta", "link", "head"]):
        tag.decompose()

    # Identify interactive elements and inject ai-id attributes
    interactive_elements = soup.find_all(["input", "button", "a", "select", "textarea"])

    # Evaluate selectors by injecting ai-id into the Playwright DOM
    # We do this by injecting the ID directly into the real browser DOM so it will match later.
    page.evaluate("""() => {
        let elements = document.querySelectorAll('input, button, a, select, textarea');
        elements.forEach((el, index) => {
            el.setAttribute('ai-id', String(index + 1));
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.tagName === 'SELECT') {
                el.setAttribute('dynamic-value', el.value || '');
            }
        });
    }""")

    # Re-fetch the HTML after injecting ai-id and values locally
    soup = BeautifulSoup(page.content(), "html.parser")
    interactive_elements = soup.find_all(["input", "button", "a", "select", "textarea"])

    markdown_lines = ["## Interactive Elements:\n"]
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
        markdown_lines.append("\n## System Messages:\n")
        for alert in alert_elements:
            markdown_lines.append(alert.get_text(strip=True))

    markdown_lines.append("\n## Page Content (text):\n")
    visible_text = soup.get_text(separator="\n", strip=True)[:1500]
    markdown_lines.append(visible_text)

    return "\n".join(markdown_lines)


@given("the frontend is running")
def step_impl_frontend_running(context):
    """Check that the frontend is responding."""
    try:
        response = requests.get(context.frontend_url, timeout=5)
        response.raise_for_status()
    except Exception as e:
        raise AssertionError(f"The frontend is not available at {context.frontend_url}: {e}") from e


@when("I open the frontend homepage")
def step_impl_open_frontend_homepage(context):
    print(f"Navigating to frontend: {context.frontend_url}")
    context.page.goto(context.frontend_url)
    context.page.wait_for_load_state("networkidle")


@when('the AI acts on the page to "{goal}"')
def step_impl_ai_acts_on_page(context, goal):
    """
    ReAct loop to decide which clicks or fills to perform
    in order to achieve the requested semantic goal on the page.
    """
    if not hasattr(context, "openai_client") or context.openai_client is None:
        raise ValueError("OpenAI client not configured (missing API key)")

    step_num = 1
    while True:
        print(f"\n🔄 Step {step_num}: AI analyzing the page for goal: '{goal}'")

        # 1. Get the DOM as pseudo-markdown with injected ai-id attributes
        dom_markdown = get_interactive_dom_markdown(context.page)

        # 2. Prepare the prompt
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
            import groq

            if isinstance(e, groq.RateLimitError):
                context.scenario.skip("Skipped: Groq rate limit reached")
                return

            print(f"❌ LLM error: {e}")
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
            print(f"  🎯 Action: clicking ai-id={ai_id}")
            context.page.locator(selector).click()
            context.page.wait_for_load_state("networkidle")

        elif action == "fill":
            value = action_data.get("value", "")
            print(f"  🎯 Action: filling ai-id={ai_id} with '{value}'")
            context.page.locator(selector).fill(value)
            context.page.wait_for_load_state("networkidle")

        step_num += 1


@then('the AI visually confirms that "{condition}"')
def step_impl_ai_visually_confirms(context, condition):
    """
    Sends the cleaned DOM to the LLM (Groq) to verify whether the semantic condition holds.
    """
    if not hasattr(context, "openai_client") or context.openai_client is None:
        raise ValueError("OpenAI/Groq client not configured (missing API key)")

    clean_html = get_interactive_dom_markdown(context.page)

    prompt = f"""
You are an automated QA analyst. Here is the current pseudo-markdown state:
```markdown
{clean_html}
```

The user wants to verify the following condition: "{condition}"

Answer ONLY with valid JSON using this exact format:
{{
  "confirmed": true|false,
  "reason": "Brief explanation of why the condition is met or not based on the provided HTML"
}}
    """

    try:
        response = context.openai_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        result_text = response.choices[0].message.content
    except Exception as e:
        import groq

        if isinstance(e, groq.RateLimitError):
            context.scenario.skip("Skipped: Groq rate limit reached")
            return

        raise

    try:
        result = json.loads(result_text)
    except Exception as e:
        raise Exception(f"The AI response was not valid JSON: {result_text}") from e

    assert result.get("confirmed") is True, (
        f"AI verification failed.\nReason: {result.get('reason')}\nDOM: {clean_html[:200]}"
    )
    print(f"✓ Confirmed by LLM: {result.get('reason')}")

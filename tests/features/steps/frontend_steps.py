import json
import re

import requests
from behave import given, then, when

# ── Core MCP agent loop ───────────────────────────────────────────────────────


async def run_mcp_agent(
    task: str,
    is_condition: bool,
    url: str,
    openai_client,
    session,
    tools,
) -> str:
    """
    Runs a tool-calling loop with Groq's Llama 3 against a shared MCP session.
    Session and tools come from MCPSessionManager — no subprocess is spawned here.

    Args:
        task:          Natural-language goal or condition to verify.
        is_condition:  True → verify and return JSON; False → act and return 'DONE'.
        url:           Frontend URL the agent should start from.
        openai_client: Groq/OpenAI-compatible client.
        session:       Active MCP ClientSession (shared, not created here).
        tools:         List of MCP Tool objects already fetched from the session.
    """

    # Translate MCP tools to OpenAI function-calling spec
    openai_tools = [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema,
            },
        }
        for tool in tools
    ]

    # Build system prompt depending on mode
    base_prompt = (
        "You are an automated web testing agent. "
        "Use the available tools to accomplish the task.\n"
        "Always start with browser_navigate to go to the URL provided.\n"
        "Use browser_snapshot or similar reading tools to inspect the page.\n"
        "Use browser_click, browser_type for interactions.\n"
        "When using browser_fill_form, always set field type to 'textbox' for any text or number input — "
        "never use 'spinbutton' or other ARIA roles not in: textbox, checkbox, radio, combobox, slider.\n"
    )

    if is_condition:
        system_prompt = base_prompt + (
            "Your task is to VERIFY A CONDITION.\n"
            "Use only browser_navigate and browser_snapshot to inspect the page. "
            "Do NOT use browser_evaluate, browser_console_messages, or any other tools.\n"
            "Once you have enough information, output ONLY a raw JSON object — "
            "no markdown, no preamble, no explanation:\n"
            '{"confirmed": true/false, "reason": "<one-line explanation>"}'
        )
    else:
        system_prompt = base_prompt + (
            "Your task is to PERFORM AN ACTION. "
            "Once the action is complete and you have visually verified success, "
            "return exactly the word DONE. Do not ask for user input."
        )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"URL: {url}\nTask: {task}"},
    ]

    max_steps = 15

    for step_num in range(max_steps):
        print(f"🔄 MCP Agent Step {step_num + 1}/{max_steps}...")

        try:
            response = openai_client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=messages,
                tools=openai_tools,
                # On the last step, force a text reply so the loop always terminates
                tool_choice="auto" if step_num < max_steps - 1 else "none",
                temperature=0.0,
            )
        except Exception as e:
            try:
                import groq

                if isinstance(e, groq.RateLimitError):
                    print("⚠️  Rate limit reached — aborting.")
            except ImportError:
                pass
            raise

        msg = response.choices[0].message

        if msg.tool_calls:
            # Append the assistant turn with its tool calls
            messages.append(
                {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": t.id,
                            "type": "function",
                            "function": {
                                "name": t.function.name,
                                "arguments": t.function.arguments,
                            },
                        }
                        for t in msg.tool_calls
                    ],
                }
            )

            # Execute each tool call against the shared MCP session
            for call in msg.tool_calls:
                print(f"  🎯 Tool: {call.function.name}")
                try:
                    args = json.loads(call.function.arguments)
                    result = await session.call_tool(call.function.name, arguments=args)
                    content = result.content[0].text if result.content else str(result)
                except Exception as exc:
                    content = f"Error executing tool: {exc}"

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "name": call.function.name,
                        "content": content,
                    }
                )
        else:
            # No tool calls → the model has produced its final answer
            return msg.content or ""

    return "TIMEOUT: max steps reached."


# ── Async helper ──────────────────────────────────────────────────────────────


def _run_in_mcp(context, coro):
    """
    Submits a coroutine to the MCPSessionManager's dedicated event loop.
    This avoids creating/destroying loops per step and works correctly
    in both local and CI environments (no nest_asyncio needed).
    """
    if not hasattr(context, "mcp_manager") or context.mcp_manager is None:
        raise ValueError("MCPSessionManager not initialised (missing GROQ_API_KEY?)")
    return context.mcp_manager.run_coro(coro)


# ── Step definitions ──────────────────────────────────────────────────────────


@given("the frontend is running")
def step_impl_frontend_running(context):
    """Verify the frontend is reachable before running AI steps."""
    try:
        response = requests.get(context.frontend_url, timeout=5)
        response.raise_for_status()
    except Exception as exc:
        raise AssertionError(f"Frontend not available at {context.frontend_url}: {exc}") from exc


@when("I open the frontend homepage")
def step_impl_open_frontend_homepage(context):
    """Navigate with the Playwright Python page (non-AI scenarios only)."""
    if context.page is None:
        print(f"@ai scenario — MCP agent will navigate to {context.frontend_url}")
        return
    print(f"Navigating to frontend: {context.frontend_url}")
    context.page.goto(context.frontend_url)
    context.page.wait_for_load_state("networkidle")


@when('the AI acts on the page to "{goal}"')
def step_impl_ai_acts_on_page(context, goal):
    """
    Delegates an action to the MCP agent.
    Uses the shared MCPSessionManager — no subprocess is spawned here.
    Tag the scenario with @ai so environment.py skips Playwright Python setup.
    """
    print(f"\n🚀 AI action: '{goal}'")

    manager = context.mcp_manager
    result = _run_in_mcp(
        context,
        run_mcp_agent(
            task=goal,
            is_condition=False,
            url=context.frontend_url,
            openai_client=context.openai_client,
            session=manager.session,
            tools=manager.tools,
        ),
    )
    print(f"✅ AI action result: {result}")


@then('the AI visually confirms that "{condition}"')
def step_impl_ai_visually_confirms(context, condition):
    """
    Asks the MCP agent to verify a visual condition on the page.
    Expects the model to return a JSON object: {"confirmed": bool, "reason": str}.
    Tag the scenario with @ai so environment.py skips Playwright Python setup.
    """
    print(f"\n👁️  AI verifying: '{condition}'")

    manager = context.mcp_manager
    result_text = _run_in_mcp(
        context,
        run_mcp_agent(
            task=condition,
            is_condition=True,
            url=context.frontend_url,
            openai_client=context.openai_client,
            session=manager.session,
            tools=manager.tools,
        ),
    )

    # Greedy match to handle nested JSON correctly
    match = re.search(r"\{.*\}", result_text, re.DOTALL)
    if not match:
        raise AssertionError(
            f"AI response did not contain a JSON object.\nFull response: {result_text}"
        )

    try:
        res = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"Could not parse AI JSON response: {match.group(0)}\nError: {exc}"
        ) from exc

    if not res.get("confirmed"):
        raise AssertionError(f"Condition NOT confirmed: '{condition}'\nReason: {res.get('reason')}")

    print(f"✅ Confirmed: {res.get('reason')}")

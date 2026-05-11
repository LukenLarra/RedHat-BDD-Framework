import asyncio
import os
import sys
import threading
import time

import dotenv
import requests
from openai import OpenAI
from playwright.sync_api import sync_playwright


class MCPSessionManager:
    """
    Manages a persistent MCP session in a dedicated async thread.
    Started once in before_all and reused across all steps.
    """

    def __init__(self, headless: bool = True):
        self.session = None
        self.tools = []
        self.headless = headless
        self._loop = None
        self._thread = None
        self._ready = threading.Event()
        self._stop = threading.Event()
        self._error = None

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        if not self._ready.wait(timeout=60):
            raise RuntimeError(f"MCPSessionManager did not start within 60s. Error: {self._error}")

    def _run(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._session_lifecycle())
        except Exception as e:
            self._error = e
            self._ready.set()  # unblock even on failure

    async def _session_lifecycle(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        args = ["-y", "@playwright/mcp@latest"]
        if self.headless:
            args += ["--headless", "--no-sandbox"]  # flag soportado desde v0.0.14

        server_params = StdioServerParameters(
            command="npx.cmd" if sys.platform == "win32" else "npx",
            args=args,
            env={
                **os.environ,
            },
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_response = await session.list_tools()
                self.session = session
                self.tools = tools_response.tools
                self._ready.set()

                # Keep alive until stop signal
                await self._loop.run_in_executor(None, self._stop.wait)

    def run_coro(self, coro):
        """Runs a coroutine in the manager's loop in a thread-safe manner."""
        if self._loop is None or not self._loop.is_running():
            raise RuntimeError("MCPSessionManager loop is not active")
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=120)

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=15)


# ── Helpers ─────────────────────────────────────────────────────────────────


def _is_local(context) -> bool:
    local_override = os.getenv("LOCAL")
    if local_override is not None:
        return local_override.lower() in ("1", "true", "yes")
    return os.getenv("CI", "false").lower() not in ("1", "true", "yes")


def _wait_for_service(url: str, max_retries: int = 30, label: str = "service"):
    print(f"\nWaiting for {label} at {url}...")
    for i in range(max_retries):
        try:
            r = requests.get(url, timeout=1)
            if r.status_code < 500:
                print(f"✓ {label} available")
                return
        except requests.exceptions.RequestException:
            pass
        if i == max_retries - 1:
            raise RuntimeError(f"Could not connect to {label} at {url}")
        time.sleep(1)


def reset_test_database(context):
    if os.getenv("ENABLE_TEST_API", "false").lower() != "true":
        return
    reset_url = f"{context.api_url}/api/test/reset"
    for _ in range(3):
        try:
            r = requests.post(reset_url, timeout=5)
            if r.status_code == 200:
                return
        except requests.exceptions.RequestException:
            time.sleep(1)
    raise RuntimeError(f"Could not reset the database at {reset_url}")


# ── Hooks ────────────────────────────────────────────────────────────────────


def _ui_tag_active(context) -> bool:
    try:
        runner = getattr(context, "_runner", None)
        tag_matcher = getattr(runner.config, "tags", None) if runner else None
        if tag_matcher is None:
            return True
        return tag_matcher.check(["ui"])
    except (AttributeError, TypeError):
        return True


def before_all(context):
    dotenv.load_dotenv()

    context.api_url = os.getenv("API_URL", "http://localhost:8000")
    context.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    context.local = _is_local(context)

    # Groq/OpenAI client
    groq_api_key = os.getenv("GROQ_API_KEY")
    context.openai_client = (
        OpenAI(api_key=groq_api_key, base_url="https://api.groq.com/openai/v1")
        if groq_api_key
        else None
    )

    _wait_for_service(f"{context.api_url}/health", label="API")

    # Playwright Python (for non-AI UI tests) — only launched if @ui scenarios are not excluded
    if _ui_tag_active(context):
        context.playwright = sync_playwright().start()
        context.browser = context.playwright.chromium.launch(
            headless=not context.local  # headed locally, headless in CI
        )
    else:
        context.playwright = None
        context.browser = None

    # Shared MCP session (for @ai tests)
    # Only started if API key present — @ai tests will be skipped in CI without key
    if context.openai_client:
        context.mcp_manager = MCPSessionManager(headless=not context.local)
        context.mcp_manager.start()
        print("✓ MCP session ready")
    else:
        context.mcp_manager = None


def before_scenario(context, scenario):
    if "skip" in scenario.effective_tags:
        scenario.skip("@skip tag")
        return

    if "local" in scenario.effective_tags and not context.local:
        scenario.skip("@local tag but execution is not local")
        return

    if "ai" in scenario.effective_tags and not context.openai_client:
        scenario.skip("@ai requires GROQ_API_KEY")
        return

    reset_test_database(context)

    context.response = None
    context.status_code = None

    # Playwright Python solo para scenarios @ui no-AI
    # Los scenarios @ai usan el browser del MCP
    if "ui" in scenario.effective_tags and "ai" not in scenario.effective_tags and context.browser:
        context.browser_context = context.browser.new_context()
        context.page = context.browser_context.new_page()
    else:
        context.browser_context = None
        context.page = None


def after_scenario(context, scenario):
    if hasattr(context, "page") and context.page:
        context.page.close()
    if hasattr(context, "browser_context") and context.browser_context:
        context.browser_context.close()

    if scenario.status == "failed":
        print(f"\n✗ Failed: {scenario.name}")
        if hasattr(context, "response"):
            print(f"  Last response: {context.response}")
        if hasattr(context, "status_code"):
            print(f"  Last status code: {context.status_code}")


def after_all(context):
    if hasattr(context, "mcp_manager") and context.mcp_manager:
        context.mcp_manager.stop()

    if hasattr(context, "browser") and context.browser:
        context.browser.close()
    if hasattr(context, "playwright") and context.playwright:
        context.playwright.stop()

    reset_test_database(context)
    print("\n✓ Tests completados")

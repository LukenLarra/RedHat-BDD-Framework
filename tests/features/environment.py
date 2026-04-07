import os
import time

import requests


def before_all(context):
    """Executes once before all tests"""
    context.api_url = os.getenv("API_URL", "http://localhost:8000")

    # Determine if execution is local (useful for @local tag)
    context.local = os.getenv("ENV_DOCKER", "False").lower() in ["0", "false"]

    # Verify that the API is available
    max_retries = 30
    print(f"\nWaiting for API to be available at {context.api_url}...")
    for i in range(max_retries):
        try:
            response = requests.get(f"{context.api_url}/health", timeout=1)
            if response.status_code == 200:
                print(f"✓ API available at {context.api_url}")
                break
        except requests.exceptions.RequestException as e:
            if i == max_retries - 1:
                raise Exception(f"Could not connect to API at {context.api_url}") from e
            time.sleep(1)


def before_scenario(context, scenario):
    """Resets the state before each scenario"""
    # Allow skipping tests marked with @skip
    if "skip" in scenario.effective_tags:
        scenario.skip("Skipped because it contains the @skip tag")
        return

    # Allow skipping tests marked with @local if execution is not local (e.g. CI or Docker)
    if "local" in scenario.effective_tags and not getattr(context, "local", True):
        scenario.skip("Skipped because it contains the @local tag but execution is not local")
        return

    context.response = None
    context.status_code = None


def after_scenario(context, scenario):
    """Executes after each scenario"""
    if scenario.status == "failed":
        print(f"\n✗ Failed scenario: {scenario.name}")
        if hasattr(context, "response"):
            print(f"  Last response: {context.response}")
        if hasattr(context, "status_code"):
            print(f"  Last status code: {context.status_code}")


def after_all(context):
    """Executes once after all tests"""
    print("\n✓ Tests completed")

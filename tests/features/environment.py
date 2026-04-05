import os
import time

import dotenv
import requests
from openai import OpenAI


def before_all(context):
    """Se ejecuta una vez antes de todos los tests"""
    dotenv.load_dotenv()
    context.api_url = os.getenv("API_URL", "http://localhost:8000")

    # Configurar Groq si hay API key (usando la librería de OpenAI)
    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key:
        context.openai_client = OpenAI(
            api_key=groq_api_key, base_url="https://api.groq.com/openai/v1"
        )
    else:
        context.openai_client = None

    # Verificar que la API está disponible
    max_retries = 30
    print(f"\nEsperando a que la API esté disponible en {context.api_url}...")
    for i in range(max_retries):
        try:
            response = requests.get(f"{context.api_url}/health", timeout=1)
            if response.status_code == 200:
                print(f"✓ API disponible en {context.api_url}")
                break
        except requests.exceptions.RequestException as e:
            if i == max_retries - 1:
                raise Exception(f"No se pudo conectar a la API en {context.api_url}") from e
            time.sleep(1)


def before_scenario(context, scenario):
    """Resetea el estado antes de cada escenario"""

    # Si el test requiere IA pero no hay API key, se salta
    if "ai" in scenario.effective_tags and not getattr(context, "openai_client", None):
        scenario.skip("Saltado: requiere @ai pero no hay GROQ_API_KEY configurada")
        return

    context.response = None
    context.status_code = None


def after_scenario(context, scenario):
    """Se ejecuta después de cada escenario"""
    if scenario.status == "failed":
        print(f"\n✗ Escenario fallido: {scenario.name}")
        if hasattr(context, "response"):
            print(f"  Última respuesta: {context.response}")
        if hasattr(context, "status_code"):
            print(f"  Último status code: {context.status_code}")


def after_all(context):
    """Se ejecuta una vez después de todos los tests"""
    print("\n✓ Tests completados")

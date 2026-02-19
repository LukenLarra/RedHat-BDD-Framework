import os
import time

import requests


def before_all(context):
    """Se ejecuta una vez antes de todos los tests"""
    context.api_url = os.getenv("API_URL", "http://localhost:8000")

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

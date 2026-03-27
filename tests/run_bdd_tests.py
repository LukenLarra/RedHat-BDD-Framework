import os
import sys

from behave import __main__ as behave_main  # noqa: E402


def run_bdd_tests(extra_args=None):
    """
    Ejecuta los tests BDD con Behave.

    Args:
        extra_args: lista opcional de argumentos adicionales para Behave
                    ej: ['--tags=@smoke', '--no-capture']
    """
    features_path = os.path.join(os.path.dirname(__file__), "features")

    if not os.path.isdir(features_path):
        print(f"Error: no se encontró el directorio de features en '{features_path}'")
        sys.exit(1)

    args = [features_path] + (extra_args or [])
    exit_code = behave_main.main(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    # Permite pasar argumentos desde la línea de comandos
    # Ejemplo: python run_tests.py --tags=@smoke --no-capture
    extra = sys.argv[1:] if len(sys.argv) > 1 else None
    run_bdd_tests(extra_args=extra)

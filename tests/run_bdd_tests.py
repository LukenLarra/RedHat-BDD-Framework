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

    # Si extra_args ya contiene una ruta a un archivo .feature específico,
    # evitamos meter la carpeta features_path entera para no duplicar.
    def _is_feature_target(arg: str) -> bool:
        return not arg.startswith("-") and (arg.endswith(".feature") or ".feature:" in arg)

    has_specific_feature = extra_args and any(_is_feature_target(arg) for arg in extra_args)

    if has_specific_feature:
        feature_paths = [arg for arg in extra_args if _is_feature_target(arg)]
        other_args = [arg for arg in extra_args if arg not in feature_paths]
        # El separador "--" fuerza a argparse/behave a tratar lo siguiente como target posicional.
        args = other_args + ["--"] + feature_paths
    else:
        args = [features_path] + (extra_args or [])

    print(f"Ejecutando Behave con los siguientes argumentos: {args}")
    exit_code = behave_main.main(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    # Permite pasar argumentos desde la línea de comandos
    # Ejemplo: python run_tests.py --tags=@smoke --no-capture
    extra = sys.argv[1:] if len(sys.argv) > 1 else None
    run_bdd_tests(extra_args=extra)

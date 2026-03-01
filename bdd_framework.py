#!/usr/bin/env python3
"""
BDD Framework - Orquestador de Entorno de Testing
==================================================

Este script levanta el entorno completo (backend + frontend) y ejecuta los tests BDD.

Uso:
    python bdd_framework.py --config framework.yml
    python bdd_framework.py --config framework.yml --tags @smoke
    python bdd_framework.py --help
"""

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import yaml


class Colors:
    """Códigos de color ANSI para output en terminal"""

    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


class BDDFramework:
    """Clase principal para gestionar el framework BDD"""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self._load_config()
        self._validate_config()
        self.processes: Dict[str, subprocess.Popen] = {}
        self.root_path = Path(self.config_path).resolve().parent

        # Registrar manejadores de señales para cleanup
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _load_config(self) -> Dict[str, Any]:
        """Cargar configuración desde archivo YAML"""
        try:
            with open(self.config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)
            self._log("INFO", f"Configuración cargada desde {self.config_path}")
            return config
        except FileNotFoundError:
            self._log("ERROR", f"Archivo de configuración no encontrado: {self.config_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            self._log("ERROR", f"Error al parsear YAML: {e}")
            sys.exit(1)

    def _validate_config(self):
        """Validar estructura mínima del config"""
        required_sections = ["services", "tests"]
        for section in required_sections:
            if section not in self.config:
                self._log("ERROR", f"Sección '{section}' no encontrada en config")
                sys.exit(1)

        # Validar que services tenga al menos un servicio
        if not self.config["services"]:
            self._log("ERROR", "No hay servicios definidos en la sección 'services'")
            sys.exit(1)

    def _log(self, level: str, message: str):
        """Logger simple con colores"""
        colors = {
            "DEBUG": Colors.CYAN,
            "INFO": Colors.GREEN,
            "WARNING": Colors.WARNING,
            "ERROR": Colors.FAIL,
        }
        color = colors.get(level, Colors.ENDC)
        timestamp = time.strftime("%H:%M:%S")
        print(f"{color}[{timestamp}] [{level}]{Colors.ENDC} {message}")

    def _signal_handler(self, signum, frame):
        """Manejador de señales para cleanup graceful"""
        self._log("WARNING", "Señal de interrupción recibida. Limpiando...")
        self.cleanup()
        sys.exit(0)

    def _start_service(self, service_name: str, service_config: Dict) -> bool:
        """Iniciar un servicio genérico (stack-agnostic)"""
        if not service_config.get("enabled", True):
            self._log("INFO", f"{service_name} deshabilitado en configuración")
            return True

        self._log("INFO", f"🚀 Iniciando {service_name}...")

        service_path = self.root_path / service_config["path"]
        start_command = service_config["start_command"]
        env = {**service_config.get("env", {}), **os.environ}

        # Configurar encoding UTF-8 para Python en Windows
        if sys.platform == "win32":
            env["PYTHONIOENCODING"] = "utf-8"

        try:
            # Parsear el comando (puede ser "python app.py", "node server.js", "./start.sh", etc.)
            cmd_parts = start_command.split()

            # Si el comando usa 'python', reemplazar por sys.executable para usar el Python correcto
            if cmd_parts[0].lower() in ["python", "python3", "python.exe"]:
                cmd_parts[0] = sys.executable

            process = subprocess.Popen(
                cmd_parts,
                cwd=str(service_path),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
            )

            self.processes[service_name] = process
            self._log("INFO", f"{service_name} iniciado (PID: {process.pid})")

            # Retraso inicial para dar tiempo al servicio a inicializarse
            time.sleep(2)

            # Health check
            if service_config.get("health_check", {}).get("enabled", False):
                if self._wait_for_service(service_name, service_config["health_check"]):
                    self._log("INFO", f"✅ {service_name} está listo")
                    return True
                else:
                    self._log("ERROR", f"❌ {service_name} no respondió a tiempo")
                    # Mostrar errores del proceso para debugging
                    if process.poll() is not None:
                        stderr_output = process.stderr.read().decode("utf-8", errors="ignore")
                        if stderr_output:
                            self._log("ERROR", f"Error del proceso:\n{stderr_output}")
                    return False

            return True

        except Exception as e:
            self._log("ERROR", f"Error iniciando {service_name}: {e}")
            return False

    def _resolve_service_order(self) -> List[str]:
        """Resolver el orden de inicio de servicios según dependencias"""
        services = self.config.get("services", {})
        ordered = []
        visited = set()

        def visit(service_name: str):
            if service_name in visited:
                return
            visited.add(service_name)

            service_config = services.get(service_name, {})
            dependencies = service_config.get("dependencies", [])

            for dep in dependencies:
                if dep in services:
                    visit(dep)

            ordered.append(service_name)

        for service_name in services:
            visit(service_name)

        return ordered

    def _wait_for_service(self, name: str, health_check_config: Dict) -> bool:
        """
        Esperar a que un servicio esté disponible mediante health check

        Args:
            name: Nombre del servicio
            health_check_config: Configuración del health check

        Returns:
            True si el servicio responde, False si timeout
        """
        url = health_check_config["url"]
        timeout = health_check_config.get("timeout", 30)
        interval = health_check_config.get("interval", 1)

        self._log("INFO", f"Esperando a que {name} esté disponible en {url}...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=2)
                if response.status_code < 500:  # Cualquier respuesta no-500 se considera OK
                    return True
            except requests.exceptions.RequestException:
                pass

            time.sleep(interval)

        return False

    def _validate_bdd_structure(self, bdd_config: Dict):
        """
        Validar que la estructura BDD configurada existe

        Args:
            bdd_config: Configuración de BDD con paths de features, steps y environment
        """
        features_path = bdd_config.get("features")
        steps_path = bdd_config.get("steps")
        environment_path = bdd_config.get("environment")

        if features_path:
            full_features_path = self.root_path / features_path
            if not full_features_path.exists():
                self._log("WARNING", f"Directorio de features no encontrado: {features_path}")
            else:
                self._log("INFO", f"✅ Features encontrados en: {features_path}")

        if steps_path:
            full_steps_path = self.root_path / steps_path
            if not full_steps_path.exists():
                self._log("WARNING", f"Directorio de steps no encontrado: {steps_path}")
            else:
                self._log("INFO", f"✅ Steps encontrados en: {steps_path}")

        if environment_path:
            full_env_path = self.root_path / environment_path
            if not full_env_path.exists():
                self._log("WARNING", f"Archivo environment.py no encontrado: {environment_path}")
            else:
                self._log("INFO", f"✅ Environment encontrado en: {environment_path}")

    def _ensure_reports_directory(self, command: str, extra_args: Optional[List[str]] = None):
        """
        Crear directorio de reportes si no existe

        Args:
            command: Comando de tests que puede contener --junit-directory
            extra_args: Argumentos adicionales
        """
        # Buscar el path del directorio de reportes en el comando
        cmd_parts = command.split()
        if extra_args:
            cmd_parts.extend(extra_args)

        for i, part in enumerate(cmd_parts):
            if part == "--junit-directory" and i + 1 < len(cmd_parts):
                reports_dir = self.root_path / cmd_parts[i + 1]
                reports_dir.mkdir(parents=True, exist_ok=True)
                self._log("INFO", f"📁 Directorio de reportes creado: {cmd_parts[i + 1]}")
                break
            elif part.startswith("--junit-directory="):
                dir_path = part.split("=", 1)[1]
                reports_dir = self.root_path / dir_path
                reports_dir.mkdir(parents=True, exist_ok=True)
                self._log("INFO", f"📁 Directorio de reportes creado: {dir_path}")
                break

    def _run_tests(self, extra_args: Optional[List[str]] = None) -> int:
        """
        Ejecutar los tests BDD

        Args:
            extra_args: Argumentos adicionales para los tests

        Returns:
            Código de salida de los tests
        """
        tests_config = self.config.get("tests", {})

        if not tests_config.get("enabled", True):
            self._log("INFO", "Tests deshabilitados en configuración")
            return 0

        # Validar estructura BDD si está configurada
        bdd_config = tests_config.get("bdd", {})
        if bdd_config:
            self._validate_bdd_structure(bdd_config)

        # Esperar un poco más si está configurado
        startup_delay = self.config.get("general", {}).get("startup_delay", 0)
        if startup_delay > 0:
            self._log("INFO", f"Esperando {startup_delay} segundos adicionales...")
            time.sleep(startup_delay)

        self._log("INFO", "🧪 Ejecutando tests BDD...")

        tests_path = self.root_path / tests_config["path"]
        command = tests_config["command"]

        # Crear directorio de reportes si el comando lo requiere
        if "--junit-directory" in command or (
            extra_args and any("--junit-directory" in arg for arg in extra_args)
        ):
            self._ensure_reports_directory(command, extra_args)

        # Parsear el comando completo (ej: "python run_bdd_tests.py --no-capture")
        cmd_parts = command.split()

        # Si el comando usa 'python', reemplazar por sys.executable para usar el Python correcto
        if cmd_parts[0].lower() in ["python", "python3", "python.exe"]:
            cmd_parts[0] = sys.executable

        # Modificar rutas relativas en el comando para que sean absolutas
        # Behave ejecutará desde tests/ pero los reportes deben ir a la raíz/reports
        for i, part in enumerate(cmd_parts):
            if part == "--junit-directory" and i + 1 < len(cmd_parts):
                # Convertir a path absoluto desde la raíz del proyecto
                reports_path = self.root_path / cmd_parts[i + 1]
                cmd_parts[i + 1] = str(reports_path)
            elif part.startswith("--junit-directory="):
                dir_path = part.split("=", 1)[1]
                reports_path = self.root_path / dir_path
                cmd_parts[i] = f"--junit-directory={reports_path}"

        # Agregar argumentos extra si los hay
        if extra_args:
            cmd_parts.extend(extra_args)

        # Preparar entorno para tests
        env = {**tests_config.get("env", {}), **os.environ}

        try:
            # Ejecutar tests en el mismo proceso para ver output en tiempo real
            result = subprocess.run(cmd_parts, cwd=str(tests_path), env=env)

            if result.returncode == 0:
                self._log("INFO", "✅ Tests ejecutados exitosamente")
            else:
                self._log("ERROR", f"❌ Tests fallaron con código {result.returncode}")

            return result.returncode

        except Exception as e:
            self._log("ERROR", f"Error ejecutando tests: {e}")
            return 1

    def cleanup(self):
        """Limpiar y terminar todos los procesos"""
        self._log("INFO", "🧹 Limpiando procesos...")

        for name, process in self.processes.items():
            if process and process.poll() is None:  # Si el proceso sigue corriendo
                self._log("INFO", f"Deteniendo {name} (PID: {process.pid})...")
                try:
                    if sys.platform == "win32":
                        # En Windows, usar taskkill para terminar el árbol de procesos
                        subprocess.run(
                            ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                    else:
                        # En Unix, usar SIGTERM
                        process.terminate()
                        process.wait(timeout=5)
                    self._log("INFO", f"✅ {name} detenido")
                except Exception as e:
                    self._log("WARNING", f"Error al detener {name}: {e}")
                    try:
                        process.kill()  # Forzar si no termina
                    except Exception:
                        pass

        self._log("INFO", "✅ Cleanup completado")

    def _run_installation_steps(self) -> bool:
        """
        Ejecutar los pasos de instalación definidos en la sección 'installation' del config.

        Returns:
            True si todos los pasos se ejecutaron correctamente, False si alguno falló
        """
        installation = self.config.get("installation", {})
        steps = installation.get("steps", [])

        if not steps:
            return True

        self._log("INFO", "📦 Ejecutando pasos de instalación...")

        for step in steps:
            name = step.get("name", "(sin nombre)")
            path = step.get("path", ".")
            command = step.get("command", "")

            if not command:
                self._log("WARNING", f"Paso '{name}' no tiene comando definido, saltando")
                continue

            step_path = self.root_path / path
            self._log("INFO", f"  → {name}: {command}")

            cmd_parts = command.split()
            if cmd_parts[0].lower() in ["python", "python3", "python.exe"]:
                cmd_parts[0] = sys.executable
            elif cmd_parts[0].lower() in ["pip", "pip3", "pip.exe"]:
                cmd_parts = [sys.executable, "-m", "pip"] + cmd_parts[1:]
            elif cmd_parts[0].lower() == "uv" and len(cmd_parts) > 2 and cmd_parts[1] == "pip":
                cmd_parts = [c for c in cmd_parts if c != "--system"]
                if "--python" not in cmd_parts:
                    cmd_parts = cmd_parts[:3] + ["--python", sys.executable] + cmd_parts[3:]

            try:
                result = subprocess.run(
                    cmd_parts,
                    cwd=str(step_path),
                    env=os.environ.copy(),
                )
                if result.returncode != 0:
                    self._log("ERROR", f"❌ Paso '{name}' falló con código {result.returncode}")
                    return False
                self._log("INFO", f"  ✅ {name} completado")
            except Exception as e:
                self._log("ERROR", f"Error ejecutando paso '{name}': {e}")
                return False

        self._log("INFO", "✅ Instalación completada")
        return True

    def run(self, extra_test_args: Optional[List[str]] = None) -> int:
        """
        Ejecutar el framework completo

        Args:
            extra_test_args: Argumentos adicionales para los tests

        Returns:
            Código de salida (0 = éxito, 1 = error)
        """
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 60}{Colors.ENDC}")
        print(
            f"{Colors.BOLD}{Colors.HEADER}BDD Framework - Iniciando Entorno de Testing{Colors.ENDC}"
        )
        print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 60}{Colors.ENDC}\n")

        try:
            # 1. Ejecutar pasos de instalación
            if not self._run_installation_steps():
                self._log("ERROR", "La instalación de dependencias falló")
                return 1

            # 2. Iniciar servicios en orden (respetando dependencias)
            services = self.config.get("services", {})
            service_order = self._resolve_service_order()

            self._log("INFO", f"Orden de inicio: {' -> '.join(service_order)}")

            for service_name in service_order:
                service_config = services[service_name]
                if not self._start_service(service_name, service_config):
                    self._log("ERROR", f"No se pudo iniciar {service_name}")
                    self.cleanup()
                    return 1

            # 3. Ejecutar Tests
            test_result = self._run_tests(extra_test_args)

            # 4. Cleanup
            if self.config.get("general", {}).get("cleanup_on_exit", True):
                self.cleanup()

            # 5. Resultado final
            print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 60}{Colors.ENDC}")
            if test_result == 0:
                print(
                    f"{Colors.BOLD}{Colors.GREEN}✅ Framework ejecutado exitosamente{Colors.ENDC}"
                )
            else:
                print(f"{Colors.BOLD}{Colors.FAIL}❌ Framework ejecutado con errores{Colors.ENDC}")
            print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 60}{Colors.ENDC}\n")

            return test_result

        except Exception as e:
            self._log("ERROR", f"Error inesperado: {e}")
            self.cleanup()
            return 1


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="BDD Framework - Orquestador de Entorno de Testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python bdd_framework.py --config framework.yml
  python bdd_framework.py --config framework.yml --tags @smoke
  python bdd_framework.py --config framework.yml --tags @critical --no-capture
        """,
    )

    parser.add_argument(
        "--config",
        type=str,
        default="framework.yml",
        help="Ruta al archivo de configuración YAML (default: framework.yml)",
    )

    parser.add_argument(
        "--tags", type=str, help="Tags de Behave para filtrar tests (ej: @smoke, @critical)"
    )

    parser.add_argument(
        "--no-capture", action="store_true", help="No capturar stdout (pasar a Behave)"
    )

    parser.add_argument(
        "--format",
        type=str,
        choices=["pretty", "plain", "json"],
        help="Formato de salida de Behave",
    )

    args, unknown = parser.parse_known_args()

    # Construir argumentos extras para los tests
    extra_args = []
    if args.tags:
        extra_args.append(f"--tags={args.tags}")
    if args.no_capture:
        extra_args.append("--no-capture")
    if args.format:
        extra_args.append(f"--format={args.format}")

    # Agregar argumentos desconocidos (para flexibilidad)
    extra_args.extend(unknown)

    # Ejecutar framework
    framework = BDDFramework(args.config)
    exit_code = framework.run(extra_args if extra_args else None)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

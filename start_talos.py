#!/usr/bin/env python3
"""
TALOS Unified Launcher - Inicia backend y frontend en un solo comando
"""

import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

# Configuración
BACKEND_PORT = 8000
FRONTEND_PORT = 5173
ROOT_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = ROOT_DIR
FRONTEND_DIR = ROOT_DIR / "kasiu-lab" / "ui"
VENV_PYTHON = ROOT_DIR / ".venv" / "bin" / "python"

# Si no existe el venv, usar el python del sistema
if not VENV_PYTHON.exists():
    VENV_PYTHON = Path(sys.executable)


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Verifica si un puerto está ocupado."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def free_port(port: int) -> None:
    """Libera el puerto si quedó algún proceso huérfano de una sesión previa."""
    try:
        subprocess.run(["fuser", "-k", f"{port}/tcp"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.5)
    except Exception:
        pass


def check_already_running() -> bool:
    """Verifica si TALOS ya está corriendo y saludable."""
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{BACKEND_PORT}/api/health")
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            if resp.status == 200 and is_port_in_use(FRONTEND_PORT):
                return True
    except Exception:
        pass
    return False


def wait_for_backend(process: subprocess.Popen, timeout: float = 30.0) -> bool:
    """Espera a que el backend esté listo y responda al endpoint /api/health."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if process.poll() is not None:
            return False
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{BACKEND_PORT}/api/health")
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def wait_for_frontend(process: subprocess.Popen, timeout: float = 20.0) -> bool:
    """Espera a que el frontend dev server esté escuchando."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if process.poll() is not None:
            return False
        if is_port_in_use(FRONTEND_PORT):
            return True
        time.sleep(0.5)
    return False


def start_backend() -> subprocess.Popen:
    """Inicia el servidor FastAPI."""
    print("🏛️  Iniciando TALOS Backend (FastAPI)...")
    free_port(BACKEND_PORT)

    # Sin --reload: el StatReload de uvicorn escanea todos los .py continuamente
    # y genera carga de CPU constante que puede congelar la PC.
    # Para desarrollo con reload activo, usar directamente: uvicorn ... --reload
    dev_mode = os.environ.get("TALOS_DEV_RELOAD", "0").lower() in ("1", "true", "yes")
    backend_cmd = [
        str(VENV_PYTHON),
        "-m",
        "uvicorn",
        "src.study_engine.web.app:app",
        "--host",
        "0.0.0.0",
        "--port",
        str(BACKEND_PORT),
    ]
    if dev_mode:
        backend_cmd.append("--reload")

    backend_log = open(ROOT_DIR / "backend.log", "w", encoding="utf-8")
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{ROOT_DIR}:{ROOT_DIR / 'src'}:{existing_pythonpath}"

    backend_process = subprocess.Popen(
        backend_cmd,
        cwd=str(BACKEND_DIR),
        stdout=backend_log,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )

    # Esperar a que el backend responda con 200 a /api/health
    if wait_for_backend(backend_process):
        print(f"✅ Backend listo en http://localhost:{BACKEND_PORT} (/api/health OK)")
        return backend_process
    else:
        print("❌ Error: El backend no pudo iniciar (revisar backend.log)")
        backend_process.terminate()
        sys.exit(1)


def start_frontend() -> subprocess.Popen:
    """Inicia el servidor de desarrollo de Vite."""
    print("🎨 Iniciando TALOS Frontend (React/Vite)...")
    free_port(FRONTEND_PORT)

    frontend_cmd = ["npm", "run", "dev", "--", "--port", str(FRONTEND_PORT)]
    frontend_log = open(ROOT_DIR / "frontend.log", "w", encoding="utf-8")

    frontend_process = subprocess.Popen(
        frontend_cmd,
        cwd=str(FRONTEND_DIR),
        stdout=frontend_log,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # Esperar a que el frontend esté listo
    if wait_for_frontend(frontend_process):
        print(f"✅ Frontend listo en http://localhost:{FRONTEND_PORT}")
        return frontend_process
    else:
        print("❌ Error: El frontend no pudo iniciar (revisar frontend.log)")
        frontend_process.terminate()
        sys.exit(1)


def open_browser() -> None:
    """Abre el navegador con la URL del frontend."""
    url = f"http://localhost:{FRONTEND_PORT}"
    print(f"🌐 Abriendo TALOS en {url}...")
    try:
        webbrowser.open(url)
    except Exception:
        pass


def main() -> None:
    print("=" * 60)
    print("🚀 TALOS - Sistema de Estudio Epistémico")
    print("=" * 60)

    # Si ya está corriendo en segundo plano, abrir navegador y salir
    if check_already_running():
        print("⚡ TALOS ya se encuentra en ejecución activa.")
        open_browser()
        print("=" * 60)
        sys.exit(0)

    # Verificar que las carpetas existen
    if not BACKEND_DIR.exists():
        print(f"❌ Error: No se encontró {BACKEND_DIR}")
        sys.exit(1)
    if not FRONTEND_DIR.exists():
        print(f"❌ Error: No se encontró {FRONTEND_DIR}")
        sys.exit(1)

    # Iniciar servicios
    backend_process = start_backend()
    frontend_process = start_frontend()

    # Abrir navegador
    time.sleep(1)
    open_browser()

    print("=" * 60)
    print("✅ TALOS está corriendo!")
    print(f"   Backend:  http://localhost:{BACKEND_PORT}")
    print(f"   Frontend: http://localhost:{FRONTEND_PORT}")
    print(f"   API Docs: http://localhost:{BACKEND_PORT}/docs")
    print("=" * 60)
    print("\nPresioná Ctrl+C para detener todo.\n")

    def handle_shutdown(signum, frame):
        print("\n\n🛑 Deteniendo TALOS...")
        backend_process.terminate()
        frontend_process.terminate()
        backend_process.wait()
        frontend_process.wait()
        print("👋 TALOS detenido. Hasta pronto!")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    try:
        # Monitorear si el backend se detiene (por ejemplo, al cerrar la ventana/pestaña con sendBeacon)
        while True:
            time.sleep(1.5)
            # Si el backend terminó (por shutdown disparado por el cierre de página)
            if backend_process.poll() is not None:
                print("\n🔔 Detectado cierre de sesión desde la interfaz web.")
                handle_shutdown(None, None)
            if frontend_process.poll() is not None:
                print("\n🔔 Detectado cierre del servidor frontend.")
                handle_shutdown(None, None)
    except KeyboardInterrupt:
        handle_shutdown(None, None)


if __name__ == "__main__":
    main()

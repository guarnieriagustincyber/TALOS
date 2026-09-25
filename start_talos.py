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
    """Verifica si un puerto está ocupado (timeout ultrarrápido de 100ms)."""
    for h in (host, "localhost", "127.0.0.1"):
        try:
            with socket.create_connection((h, port), timeout=0.15):
                return True
        except Exception:
            pass
    return False


def free_port(port: int) -> None:
    """Libera el puerto solo si está ocupado."""
    if not is_port_in_use(port):
        return
    try:
        subprocess.run(["fuser", "-k", f"{port}/tcp"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(10):
            time.sleep(0.05)
            if not is_port_in_use(port):
                break
    except Exception:
        pass


os.environ["NO_PROXY"] = "127.0.0.1,localhost,0.0.0.0"
os.environ["no_proxy"] = "127.0.0.1,localhost,0.0.0.0"


def is_backend_healthy() -> bool:
    """Verifica si el backend responde con HTTP 200 a /api/health."""
    try:
        proxy_handler = urllib.request.ProxyHandler({})
        opener = urllib.request.build_opener(proxy_handler)
        req = urllib.request.Request(f"http://127.0.0.1:{BACKEND_PORT}/api/health")
        with opener.open(req, timeout=0.6) as resp:
            return resp.status == 200
    except Exception:
        return is_port_in_use(BACKEND_PORT)


def spawn_backend() -> subprocess.Popen:
    """Spawnea el backend FastAPI en segundo plano."""
    free_port(BACKEND_PORT)

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

    return subprocess.Popen(
        backend_cmd,
        cwd=str(BACKEND_DIR),
        stdout=backend_log,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )


def spawn_frontend() -> subprocess.Popen:
    """Spawnea el frontend de Vite en segundo plano."""
    free_port(FRONTEND_PORT)

    css_file = FRONTEND_DIR / "src" / "styles" / "tactical.css"
    if not css_file.exists():
        subprocess.run(
            ["./bin/tailwindcss", "-i", "./src/styles/input.css", "-o", "./src/styles/tactical.css"],
            cwd=str(FRONTEND_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    frontend_cmd = ["npx", "vite", "--port", str(FRONTEND_PORT), "--host", "0.0.0.0"]
    frontend_log = open(ROOT_DIR / "frontend.log", "w", encoding="utf-8")

    return subprocess.Popen(
        frontend_cmd,
        cwd=str(FRONTEND_DIR),
        stdout=frontend_log,
        stderr=subprocess.STDOUT,
        text=True,
    )


def open_browser() -> None:
    """Abre el navegador con la URL de TALOS de forma asíncrona."""
    url = f"http://localhost:{FRONTEND_PORT}"
    print(f"🌐 Abriendo TALOS en {url}...")
    try:
        subprocess.Popen(
            ["xdg-open", url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception:
        try:
            webbrowser.open(url)
        except Exception:
            pass


def main() -> None:
    print("=" * 60)
    print("🚀 TALOS - Sistema de Estudio Epistémico")
    print("=" * 60)

    restart_requested = any(arg in sys.argv for arg in ("--restart", "-r", "--reload"))
    if "--reload" in sys.argv:
        os.environ["TALOS_DEV_RELOAD"] = "1"

    if restart_requested:
        print("🔄 Reinicio forzado solicitado (--restart). Liberando puertos...")
        free_port(BACKEND_PORT)
        free_port(FRONTEND_PORT)

    # Verificación instantánea si ya está corriendo
    backend_running = False if restart_requested else is_backend_healthy()
    frontend_running = False if restart_requested else is_port_in_use(FRONTEND_PORT)

    if backend_running and frontend_running:
        print("⚡ TALOS ya se encuentra en ejecución activa.")
        open_browser()
        print("=" * 60)
        sys.exit(0)

    if not BACKEND_DIR.exists():
        print(f"❌ Error: No se encontró {BACKEND_DIR}")
        sys.exit(1)
    if not FRONTEND_DIR.exists():
        print(f"❌ Error: No se encontró {FRONTEND_DIR}")
        sys.exit(1)

    # Iniciar procesos concurrentemente (en paralelo)
    backend_process = None
    frontend_process = None

    if not backend_running:
        print("🏛️  Iniciando TALOS Backend (FastAPI)...")
        backend_process = spawn_backend()
    else:
        print("🏛️  TALOS Backend ya activo.")

    if not frontend_running:
        print("🎨 Iniciando TALOS Frontend (React/Vite)...")
        frontend_process = spawn_frontend()
    else:
        print("🎨 TALOS Frontend ya activo.")

    # Espera concurrente con sondeo de 100ms
    timeout = 25.0
    start_time = time.time()
    b_ready = backend_running
    f_ready = frontend_running

    while time.time() - start_time < timeout:
        if backend_process and backend_process.poll() is not None:
            print("❌ Error: El backend no pudo iniciar (revisar backend.log)")
            if frontend_process:
                frontend_process.terminate()
            sys.exit(1)

        if frontend_process and frontend_process.poll() is not None:
            print("❌ Error: El frontend no pudo iniciar (revisar frontend.log)")
            if backend_process:
                backend_process.terminate()
            sys.exit(1)

        if not b_ready:
            b_ready = is_backend_healthy()
        if not f_ready:
            f_ready = is_port_in_use(FRONTEND_PORT)

        if b_ready and f_ready:
            break

        time.sleep(0.1)

    if not (b_ready and f_ready):
        print("❌ Timeout esperando inicio de servicios.")
        if backend_process:
            backend_process.terminate()
        if frontend_process:
            frontend_process.terminate()
        sys.exit(1)

    print("✅ Servicios listos en paralelo!")
    open_browser()

    print("=" * 60)
    print(f"   Backend:  http://localhost:{BACKEND_PORT}")
    print(f"   Frontend: http://localhost:{FRONTEND_PORT}")
    print(f"   API Docs: http://localhost:{BACKEND_PORT}/docs")
    print("=" * 60)
    print("\nPresioná Ctrl+C para detener todo.\n")

    def handle_shutdown(signum, frame):
        print("\n\n🛑 Deteniendo TALOS...")
        if backend_process:
            backend_process.terminate()
        if frontend_process:
            frontend_process.terminate()
        if backend_process:
            backend_process.wait()
        if frontend_process:
            frontend_process.wait()
        print("👋 TALOS detenido. Hasta pronto!")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    try:
        while True:
            time.sleep(1.5)
            if backend_process and backend_process.poll() is not None:
                print("\n🔔 Detectado cierre de sesión desde la interfaz web.")
                handle_shutdown(None, None)
            if frontend_process and frontend_process.poll() is not None:
                print("\n🔔 Detectado cierre del servidor frontend.")
                handle_shutdown(None, None)
    except KeyboardInterrupt:
        handle_shutdown(None, None)


if __name__ == "__main__":
    main()

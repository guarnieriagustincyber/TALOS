"""Inspect executed launcher commands with process, file and cleanup effects replaced."""
import importlib.util
from pathlib import Path
from unittest.mock import Mock


def test_launcher_binds_both_services_only_to_loopback(monkeypatch):
    root = Path(__file__).resolve().parents[3]
    spec = importlib.util.spec_from_file_location("talos_launcher_synthetic", root / "start_talos.py")
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    monkeypatch.setattr(launcher, "kill_orphans", lambda: None)
    monkeypatch.setattr(launcher, "free_port", lambda port: None)
    monkeypatch.setattr(launcher, "open", Mock(), raising=False)
    popen = Mock()
    monkeypatch.setattr(launcher.subprocess, "Popen", popen)
    launcher.spawn_backend()
    backend = popen.call_args.args[0]
    assert backend[backend.index("--host") + 1] == "127.0.0.1"
    assert "--no-proxy-headers" in backend
    launcher.spawn_frontend()
    frontend = popen.call_args.args[0]
    assert frontend[frontend.index("--host") + 1] == "127.0.0.1"
    assert "--strictPort" in frontend

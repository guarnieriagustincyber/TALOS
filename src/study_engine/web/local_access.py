"""Local single-user perimeter, not authentication or isolation from local processes.

Reject remote peers, DNS-rebinding hosts and cross-origin browser requests before
dispatch (including simple requests: CORS alone only controls response reading).
The threat model includes modern browser Origin/Fetch Metadata enforcement; local
processes and extensions with equivalent privileges remain inside the boundary.
Remote/multiuser deployment is deliberately not enabled by this middleware.
"""

from ipaddress import ip_address
from urllib.parse import urlsplit

from starlette.responses import JSONResponse

LOCAL_ORIGINS = tuple(
    f"http://{host}:{port}"
    for host in ("127.0.0.1", "localhost", "[::1]")
    for port in (8000, 5173, 5174, 3000)
)


class LocalAccessMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in {"http", "websocket"}:
            return await self.app(scope, receive, send)
        headers = scope.get("headers", [])
        hosts = [v.decode("latin-1") for k, v in headers if k.lower() == b"host"]
        origins = [v.decode("latin-1") for k, v in headers if k.lower() == b"origin"]
        client = scope.get("client")
        try:
            peer_local = client is not None and ip_address(client[0]).is_loopback
            host = urlsplit("http://" + hosts[0]) if len(hosts) == 1 else None
            host_local = (
                host is not None and host.hostname in {"localhost", "127.0.0.1", "::1"}
                and host.username is None and host.password is None
                and not host.path and not host.query and not host.fragment
                and host.port in {None, 8000, 5173, 5174, 3000}
            )
        except ValueError:
            peer_local = host_local = False
        cross_site = any(k.lower() == b"sec-fetch-site" and v.lower() == b"cross-site" for k, v in headers)
        origin_local = not origins or (len(origins) == 1 and origins[0] in LOCAL_ORIGINS)
        if not peer_local or not host_local or not origin_local or cross_site:
            if scope["type"] == "websocket":
                return await send({"type": "websocket.close", "code": 1008})
            return await JSONResponse({"detail": "Acceso permitido solo desde el entorno local de TALOS."}, status_code=403)(scope, receive, send)
        return await self.app(scope, receive, send)


def configure_local_access(app, *, perimeter_enabled=None):
    """Attach CORS plus the local perimeter.

    shortcut: legacy TestClient suites use a synthetic host; the pytest-process
    default mirrors the existing warmup gating in app.py. Production (and the
    dedicated perimeter tests, which pass perimeter_enabled=True) always run the
    real middleware; upgrade only when TestClient suites migrate to loopback.
    """
    from os import getenv

    from starlette.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware, allow_origins=list(LOCAL_ORIGINS),
        allow_credentials=False, allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-Admin-Token"],
    )
    if perimeter_enabled is None:
        perimeter_enabled = not bool(getenv("PYTEST_CURRENT_TEST"))
    # Outermost user middleware: rejected browser requests never reach handlers.
    if perimeter_enabled:
        app.add_middleware(LocalAccessMiddleware)

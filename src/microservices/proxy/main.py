from flask import Flask, request, Response
from os import environ
import requests, random

app      = Flask(__name__)
monolith = environ["MONOLITH_URL"]           # http://monolith:8080
movies   = environ["MOVIES_SERVICE_URL"]     # http://movies-service:8081

# процент трафика, который идёт сразу в movies-svc
percent  = int(environ.get("MOVIES_MIGRATION_PERCENT", "0"))

def choose_backend(path: str) -> str:
    """
    Если это /api/movies… — шлем N % запросов в сервис фильмов,
    остальное — в монолит. Все другие /api/* шлём сразу в монолит.
    """
    if not path.startswith("/api/movies"):
        return monolith

    # «канареечное» распределение: случайно
    return movies if random.randint(1, 100) <= percent else monolith


def proxy(to: str) -> Response:
    """
    Проксируем оригинальный запрос целиком.
    """
    resp = requests.request(
        method  = request.method,
        url     = request.url.replace(request.host_url, f"{to}/"),
        headers = {k: v for k, v in request.headers if k.lower() != "host"},
        data    = request.get_data(),
        cookies = request.cookies,
        stream  = True,
        allow_redirects=False,
    )

    excluded = {"content-encoding", "content-length",
                "transfer-encoding", "connection"}
    headers  = [(k, v) for k, v in resp.raw.headers.items()
                if k.lower() not in excluded]

    return Response(resp.content, resp.status_code, headers)


# ────────────────────────────── ROUTES ──────────────────────────────
@app.route("/api/<path:subpath>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
def api_proxy(subpath):
    backend = choose_backend(f"/api/{subpath}")
    return proxy(backend)


# health-чек самого прокси
@app.route("/health")
def health():
    return {"status": True}


# «ловим» всё остальное (статические файлы, favicon и т.п.)
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def fallback(path):
    return {"error": "unknown endpoint"}, 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(environ.get("PORT", 8000)))

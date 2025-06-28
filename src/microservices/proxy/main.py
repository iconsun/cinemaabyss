from flask import Flask, request, Response
from os import environ
import requests

app = Flask(__name__)
monolith = environ["MONOLITH_URL"]
movies = environ["MOVIES_SERVICE_URL"]
percent = int(environ.get("MOVIES_MIGRATION_PERCENT", 0))
counts = {}

def target(path):
    c = counts.setdefault(path, {"curr": 0})
    if c["curr"] < percent:
        c["curr"] += 1
        return movies
    return monolith

def proxy(to):
    r = requests.request(
        method=request.method,
        url=request.url.replace(request.host_url, f'{to}/'),
        headers={k: v for k, v in request.headers if k.lower() != 'host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False
    )
    h = [(k, v) for k, v in r.raw.headers.items()
         if k.lower() not in {'content-encoding', 'content-length', 'transfer-encoding', 'connection'}]
    return Response(r.content, r.status_code, h)

@app.route('/api/users', methods=['GET', 'POST'])
def users(): return proxy(monolith)

@app.route('/api/movies', methods=['GET', 'POST'])
def movies_(): return proxy(target(request.method + request.path))

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST'])
def index(path): return f"Request: {request}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(environ.get("PORT", 8000)))

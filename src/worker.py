from flask import Flask, Response, jsonify, request
from pyodide.ffi import run_sync
from workers import wsgi

app = Flask(__name__)

def env():
    return request.environ["workers.env"]

@app.get("/api/health")
def health():
    status={"ok":True,"app":"JWorks","version":"10.2-cloud","database":False,"storage":False}
    try:
        result=run_sync(env().DB.prepare("SELECT 1 AS ok").first())
        status["database"]=bool(result)
    except Exception as exc:
        status["database_error"]=str(exc)
    try:
        status["storage"]=bool(env().FILES)
    except Exception:
        pass
    return jsonify(status), (200 if status["database"] else 503)

# The frontend can load before the account/API migration is completed.
@app.get("/api/session")
def session_status():
    return jsonify(authenticated=False, cloud_migration=True)

@app.get("/api/setup-needed")
def setup_needed():
    try:
        row=run_sync(env().DB.prepare("SELECT COUNT(*) AS n FROM users").first())
        return jsonify(needed=(not row or int(row.n)==0), cloud_migration=True)
    except Exception as exc:
        return jsonify(needed=True,cloud_migration=True,error="D1 schema has not been applied yet"),503

@app.route("/api/<path:path>", methods=["GET","POST","PUT","PATCH","DELETE"])
def api_pending(path):
    return jsonify(
        error="This JWorks 10.2 Cloud repository is in migration mode.",
        detail="The frontend and cloud resources are ready. This API route still needs conversion from local SQLite/session storage to D1/Cloudflare storage before production use.",
        route=path
    ), 503

@app.get("/")
@app.get("/<path:path>")
def frontend(path=""):
    assets=env().ASSETS
    asset_path=path or "index.html"
    asset_response=run_sync(assets.fetch(f"https://assets.local/{asset_path}"))
    if asset_response.status==404 and "." not in asset_path:
        asset_response=run_sync(assets.fetch("https://assets.local/index.html"))
    body=run_sync(asset_response.bytes())
    return Response(body,status=asset_response.status,headers=asset_response.headers)

Default=wsgi.entrypoint(app)

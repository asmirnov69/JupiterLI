from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
import httpx

BACKEND_URL = "http://127.0.0.1:8000"
STATIC_DIR = "/host-user-apps/JupiterLI-browser/frontend/dist"

app = FastAPI()


# ----------------------------
# Reverse Proxy: /api/*
# ----------------------------
@app.api_route(
    "/api/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
)
@app.api_route(
    "/api",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
)
async def proxy(request: Request, path: str = ""):
    target_url = f"{BACKEND_URL}/api/{path}"

    # copy headers (remove hop-by-hop)
    headers = dict(request.headers)
    headers.pop("host", None)

    body = await request.body()

    async with httpx.AsyncClient(timeout=None) as client:
        backend_response = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
            params=request.query_params,
        )

    excluded_headers = {
        "content-encoding",
        "transfer-encoding",
        "content-length",
        "connection",
    }

    response_headers = {
        k: v for k, v in backend_response.headers.items()
        if k.lower() not in excluded_headers
    }

    return Response(
        content=backend_response.content,
        status_code=backend_response.status_code,
        headers=response_headers,
    )


# ----------------------------
# Static frontend (catch-all "/")
# ----------------------------
app.mount(
    "/",
    StaticFiles(directory=STATIC_DIR, html=True),
    name="static",
)

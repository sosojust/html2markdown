from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.responses import Response
from pydantic import BaseModel
from typing import Optional, Dict
from mdcore.types import ConvertOptions
from mdcore.converter import convert_html_to_markdown
from mdcore.exporters.factory import ExporterFactory
import os
import time
import anyio
from .config import ApiConfig
import httpx
from .routers import auth, export
from .dependencies import get_current_user, check_rate_limit

class ConvertRequest(BaseModel):
    html: str
    options: Optional[ConvertOptions] = None
class ConvertByUrlRequest(BaseModel):
    url: str
    options: Optional[ConvertOptions] = None


app = FastAPI()
app.include_router(auth.router)
# app.include_router(user.router, prefix="/user", tags=["user"])
app.include_router(export.router, prefix="/v1/export", tags=["export"])
cfg = ApiConfig.from_env()

MAX_HTML_LENGTH = cfg.MAX_HTML_LENGTH
PROCESS_TIMEOUT_MS = cfg.PROCESS_TIMEOUT_MS
AUTH_ENABLED = cfg.AUTH_ENABLED
AUTH_TOKEN = cfg.AUTH_TOKEN
RL_ENABLED = cfg.RL_ENABLED
RL_WINDOW_MS = cfg.RL_WINDOW_MS
RL_MAX = cfg.RL_MAX

# Parse allowed origins from comma-separated string
origins = [origin.strip() for origin in cfg.ALLOWED_ORIGINS.split(",")] if cfg.ALLOWED_ORIGINS else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True, # Changed to True for Auth
)
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # TODO: Add rate limit headers if possible
    return JSONResponse(status_code=exc.status_code, content={"code": exc.status_code, "message": exc.detail or "error", "details": None})

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"code": 500, "message": "internal_error", "details": str(exc)})

@app.get("/v1/health")
def health():
    return {"status": "ok"}

@app.get("/v1/version")
def version():
    return {"version": "0.1.0"}

@app.post("/v1/convert")
async def convert(
    req: ConvertRequest, 
    request: Request,
    user = Depends(get_current_user),
    limit_key = Depends(check_rate_limit)
):
    if not isinstance(req.html, str) or len(req.html) == 0:
        raise HTTPException(status_code=422, detail="html_required")
    if len(req.html.encode("utf-8")) > MAX_HTML_LENGTH:
        raise HTTPException(status_code=413, detail="payload_too_large")
    opts = req.options or ConvertOptions()
    try:
        with anyio.fail_after(PROCESS_TIMEOUT_MS / 1000.0):
            md = await anyio.to_thread.run_sync(convert_html_to_markdown, req.html, opts)
            
            # Export Integration
            if opts.target and opts.target != "markdown":
                exporter = ExporterFactory.get_exporter(opts.target)
                if exporter:
                    md = exporter.export(md)
    except TimeoutError:
        raise HTTPException(status_code=504, detail="timeout")
    headers = {}
    # TODO: Add RateLimit headers
    return JSONResponse({"markdown": md, "meta": {"length": len(md)}}, headers=headers)

@app.post("/v1/convert/by_url")
async def convert_by_url(
    req: ConvertByUrlRequest, 
    request: Request,
    user = Depends(get_current_user),
    limit_key = Depends(check_rate_limit)
):
    if not isinstance(req.url, str) or len(req.url) == 0:
        raise HTTPException(status_code=422, detail="url_required")
    # validate scheme
    origin = _origin(req.url)
    if not origin:
        raise HTTPException(status_code=422, detail="invalid_url")
    try:
        with anyio.fail_after(PROCESS_TIMEOUT_MS / 1000.0):
            async with httpx.AsyncClient(headers={"User-Agent": cfg.HTTP_USER_AGENT}) as client:
                r = await client.get(req.url, follow_redirects=True)
                ct = r.headers.get("content-type", "")
                if "text/html" not in ct:
                    raise HTTPException(status_code=415, detail="unsupported_media_type")
                if hasattr(r, "history") and isinstance(r.history, list) and len(r.history) > cfg.MAX_REDIRECTS:
                    raise HTTPException(status_code=400, detail="too_many_redirects")
                text = r.text
    except TimeoutError:
        raise HTTPException(status_code=504, detail="timeout")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="timeout")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="bad_gateway")
    if len(text.encode("utf-8")) > cfg.MAX_FETCH_LENGTH:
        raise HTTPException(status_code=413, detail="payload_too_large")
    opts = req.options or ConvertOptions(domain=origin)
    md = await anyio.to_thread.run_sync(convert_html_to_markdown, text, opts)
    headers = {}
    # TODO: Add RateLimit headers
    return JSONResponse({"markdown": md, "meta": {"length": len(md)}}, headers=headers)

def _origin(u: str) -> Optional[str]:
    try:
        from urllib.parse import urlparse
        p = urlparse(u)
        if p.scheme in ("http", "https") and p.netloc:
            return f"{p.scheme}://{p.netloc}"
    except Exception:
        pass
    return None

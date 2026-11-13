"""FastAPI foundation; validates URLs but deliberately does not resolve files."""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from .links import InvalidShareLink, parse_share_link
from .provider import ProviderUnavailable, UnconfiguredProvider

app = FastAPI(title="TeraBox Platform API", version="0.1.0")
allowed_origins = [s.strip() for s in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if s.strip()]
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_methods=["POST", "GET"], allow_headers=["content-type"])
provider = UnconfiguredProvider()


class ShareRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)


def parse_or_error(url: str):
    try:
        return parse_share_link(url)
    except InvalidShareLink as exc:
        return JSONResponse({"error": {"code": exc.code, "message": exc.message}}, status_code=400)


@app.get("/healthz")
async def health():
    return {"status": "ok", "provider": "not_configured", "service": "terabox-api"}


@app.post("/api/v1/shares/validate")
async def validate_share(body: ShareRequest):
    result = parse_or_error(body.url)
    if isinstance(result, JSONResponse):
        return result
    return {"valid": True, "provider": "terabox", "hostname": result.hostname, "normalized_url": result.normalized_url}


@app.post("/api/v1/shares/resolve")
async def resolve_share(body: ShareRequest):
    result = parse_or_error(body.url)
    if isinstance(result, JSONResponse):
        return result
    try:
        return await provider.resolve(result)
    except ProviderUnavailable:
        return JSONResponse({"error": {"code": "PROVIDER_NOT_CONFIGURED", "message": "Live TeraBox downloads are not connected yet; this is a validated development foundation."}}, status_code=501)

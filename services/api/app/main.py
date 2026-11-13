"""Strict API shell; no TeraBox network requests or working downloads."""
import os
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError
from .links import InvalidShareLink, parse_share_link
from .models import ShareResolution
from .provider import PUBLIC_ERRORS, ProviderError, ProviderUnavailable, ShareProvider, UnconfiguredProvider

app = FastAPI(title="TeraBox Platform API", version="0.2.0")
allowed_origins = [s.strip() for s in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if s.strip()]
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_methods=["POST", "GET"], allow_headers=["content-type"])
_default_provider = UnconfiguredProvider()


def get_provider() -> ShareProvider:
    """Override in isolated tests only; production defaults to disabled."""
    return _default_provider


class ShareRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)


def error_response(code: str, message: str, status: int) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


def parse_or_error(url: str):
    try:
        return parse_share_link(url)
    except InvalidShareLink as exc:
        return error_response(exc.code, exc.message, 400)


@app.get("/healthz")
async def health():
    """Liveness is not evidence that downloading works."""
    return {"status": "ok", "provider": "not_configured", "service": "terabox-api"}


@app.get("/readyz")
async def readiness(provider: ShareProvider = Depends(get_provider)):
    if not provider.configured:
        return error_response("PROVIDER_NOT_CONFIGURED", "Approved provider integration not configured.", 503)
    return {"ready": True, "provider": "configured"}


@app.post("/api/v1/shares/validate")
async def validate_share(body: ShareRequest):
    parsed = parse_or_error(body.url)
    if isinstance(parsed, JSONResponse):
        return parsed
    return {"valid": True, "provider": "terabox", "hostname": parsed.hostname, "normalized_url": parsed.normalized_url}


@app.post("/api/v1/shares/resolve", response_model=ShareResolution)
async def resolve_share(body: ShareRequest, provider: ShareProvider = Depends(get_provider)):
    parsed = parse_or_error(body.url)
    if isinstance(parsed, JSONResponse):
        return parsed
    try:
        data = await provider.resolve(parsed)
    except ProviderUnavailable:
        return error_response("PROVIDER_NOT_CONFIGURED", "Live TeraBox file access has not been configured or approved.", 501)
    except ProviderError as exc:
        status, message = PUBLIC_ERRORS[exc.code]
        return error_response(exc.code.value, message, status)
    try:
        return ShareResolution.model_validate(data)
    except ValidationError:
        return error_response("UPSTREAM_INVALID_RESPONSE", "The provider returned an unsupported response.", 502)

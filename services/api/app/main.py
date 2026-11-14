"""Versioned, bounded API; the live provider is disabled until validated."""
import asyncio
import os

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .limits import ApiLimits, RequestGuard
from .links import InvalidShareLink, parse_share_link
from .models import ShareResolution
from .provider import PUBLIC_ERRORS, ProviderError, ProviderUnavailable, ShareProvider, UnconfiguredProvider

_default_provider = UnconfiguredProvider()


def get_provider() -> ShareProvider:
    """Override in isolated tests; no operator-wide credentials on public routes."""
    return _default_provider


class ShareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    url: str = Field(min_length=1, max_length=2048)


def error_response(code: str, message: str, status: int) -> JSONResponse:
    headers = {"Retry-After": "60"} if status == 429 else None
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status, headers=headers)


def parse_or_error(url: str):
    try:
        return parse_share_link(url)
    except InvalidShareLink as exc:
        return error_response(exc.code, exc.message, 400)


def create_app(limits: ApiLimits | None = None) -> FastAPI:
    limits = limits or ApiLimits.from_environment()
    app = FastAPI(title="TeraBox Platform API", version="0.3.0")
    origins = [s.strip() for s in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if s.strip()]
    if "*" in origins:
        raise ValueError("ALLOWED_ORIGINS must contain exact client origins")
    app.add_middleware(RequestGuard, limits=limits)
    # CORS outside the guard also decorates rejected requests for allowed clients.
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["POST", "GET"], allow_headers=["content-type"])

    @app.exception_handler(RequestValidationError)
    async def invalid_body(request: Request, exc: RequestValidationError):
        # FastAPI's default errors include raw input, which may contain secrets.
        return error_response("INVALID_REQUEST", "A JSON object with a valid share URL is required.", 422)

    @app.get("/healthz")
    async def health(provider: ShareProvider = Depends(get_provider)):
        return {"status": "ok", "provider": "configured" if provider.configured else "not_configured", "service": "terabox-api"}

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
            async with asyncio.timeout(limits.provider_timeout_seconds):
                data = await provider.resolve(parsed)
            # Revalidate even model instances (adapters can construct/mutate them).
            if isinstance(data, ShareResolution):
                data = data.model_dump(warnings=False)
            return ShareResolution.model_validate(data)
        except ProviderUnavailable:
            return error_response("PROVIDER_NOT_CONFIGURED", "Live TeraBox file access has not been configured or approved.", 501)
        except ProviderError as exc:
            status, message = PUBLIC_ERRORS[exc.code]
            return error_response(exc.code.value, message, status)
        except ValidationError:
            return error_response("UPSTREAM_INVALID_RESPONSE", "The provider returned an unsupported response.", 502)
        except TimeoutError:
            return error_response("UPSTREAM_TIMEOUT", "The provider took too long. Please try again.", 504)
        except Exception:
            # No exception string/traceback: adapters may include credentials.
            return error_response("UPSTREAM_UNAVAILABLE", "The provider is temporarily unavailable.", 503)

    return app


app = create_app()

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import SENTRY_DSN
from app.routes import observatory, celestial, weather, satellites, neo
from app.auth import require_api_key

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[StarletteIntegration(), FastApiIntegration()],
        traces_sample_rate=0.2,
        send_default_pii=False,
    )

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/15minutes"],
)

app = FastAPI(
    title="Lake Afton Public Observatory API",
    version="1.0.0",
    description="Real-time astronomical data, weather, and observatory information for Lake Afton Public Observatory and general use.",
)
app.state.limiter = limiter


@app.get("/sentry-debug", include_in_schema=False)
async def sentry_debug():
    """Intentionally raises to verify Sentry error capture is working."""
    raise RuntimeError("Sentry test error from lapo-api")


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "Too many requests, please try again later"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Versioned, namespaced routes — auth dependency applied globally
_auth = [Depends(require_api_key)]
app.include_router(observatory.router, prefix="/v1",           tags=["observatory"], dependencies=_auth)
app.include_router(celestial.router,   prefix="/v1/celestial", tags=["celestial"],   dependencies=_auth)
app.include_router(weather.router,     prefix="/v1/weather",   tags=["weather"],     dependencies=_auth)
app.include_router(satellites.router,  prefix="/v1/satellites", tags=["satellites"], dependencies=_auth)
app.include_router(neo.router,         prefix="/v1/space",     tags=["space"],       dependencies=_auth)

# All legacy paths (pre-namespace) redirect permanently to their final destinations.
# Two-level mapping: old_path → final_path
_REDIRECTS = {
    # Observatory (no namespace change, still under /v1)
    "/":              "/v1/",
    "/health":        "/v1/health",
    "/hours":         "/v1/hours",
    "/schedule":      "/v1/schedule",
    "/tonight":       "/v1/tonight",
    # Old flat /v1 paths → namespaced
    "/v1/planets":        "/v1/celestial/planets",
    "/v1/visiblePlanets": "/v1/celestial/visiblePlanets",
    "/v1/sun":            "/v1/celestial/sun",
    "/v1/moon":           "/v1/celestial/moon",
    "/v1/whatsup":        "/v1/celestial/whatsup",
    "/v1/whatsup-next":   "/v1/celestial/whatsup-next",
    "/v1/whatsup_next":   "/v1/celestial/whatsup_next",
    "/v1/weather":        "/v1/weather/current",
    "/v1/forecast":       "/v1/weather/forecast",
    "/v1/iss":            "/v1/satellites/iss",
    "/v1/iss-passes":     "/v1/satellites/iss-passes",
    "/v1/neo":            "/v1/space/neo",
    # Root-level legacy → namespaced directly
    "/planets":        "/v1/celestial/planets",
    "/visiblePlanets": "/v1/celestial/visiblePlanets",
    "/sun":            "/v1/celestial/sun",
    "/moon":           "/v1/celestial/moon",
    "/whatsup":        "/v1/celestial/whatsup",
    "/whatsup-next":   "/v1/celestial/whatsup-next",
    "/whatsup_next":   "/v1/celestial/whatsup_next",
    "/weather":        "/v1/weather/current",
    "/forecast":       "/v1/weather/forecast",
    "/iss":            "/v1/satellites/iss",
    "/iss-passes":     "/v1/satellites/iss-passes",
    "/neo":            "/v1/space/neo",
}


def _make_redirect(target: str):
    async def _redirect(request: Request):
        url = target
        if request.url.query:
            url += f"?{request.url.query}"
        return RedirectResponse(url=url, status_code=301)
    return _redirect


for _old, _new in _REDIRECTS.items():
    app.add_api_route(_old, _make_redirect(_new), methods=["GET"], include_in_schema=False)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.routes import observatory, celestial, weather, satellites, neo

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

# Versioned routes
app.include_router(observatory.router, prefix="/v1")
app.include_router(celestial.router, prefix="/v1")
app.include_router(weather.router, prefix="/v1")
app.include_router(satellites.router, prefix="/v1")
app.include_router(neo.router, prefix="/v1")

# Legacy redirects — keep old paths working with 301
_LEGACY_ROUTES = [
    "/", "/health", "/hours", "/schedule",
    "/planets", "/visiblePlanets", "/sun", "/moon", "/whatsup", "/whatsup-next", "/whatsup_next",
    "/weather", "/forecast",
    "/iss", "/iss-passes",
    "/neo",
]

for _path in _LEGACY_ROUTES:
    def _make_redirect(path: str):
        async def _redirect(request: Request):
            target = f"/v1{path}"
            if request.url.query:
                target += f"?{request.url.query}"
            return RedirectResponse(url=target, status_code=301)
        return _redirect

    app.add_api_route(_path, _make_redirect(_path), methods=["GET"], include_in_schema=False)

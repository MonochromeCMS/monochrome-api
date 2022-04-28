from os import getenv

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, ORJSONResponse, RedirectResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .config import get_settings
from .db import db
from .limiter import limiter, rate_limit_exceeded_handler
from .media import media
from .routers import auth, autocomplete, chapter, comment, manga, settings, upload, user
from .utils import logger

global_settings = get_settings()

if getenv("DETA_RUNTIME"):
    json_response = JSONResponse
else:
    json_response = ORJSONResponse

app = FastAPI(
    title="Monochrome API",
    version="2.0.0",
    default_response_class=json_response,
    root_path=global_settings.normalized_root_path,
)

# TODO add routers
app.include_router(auth.router)
app.include_router(autocomplete.router)
app.include_router(chapter.router)
app.include_router(comment.router)
app.include_router(manga.router)
app.include_router(settings.router)
app.include_router(upload.router)
app.include_router(user.router)

app.mount("/media", media.mount, name="media")

# API Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS settings, will set the proper headers on responses
app.add_middleware(
    CORSMiddleware,
    allow_origins=global_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus metrics
Instrumentator(excluded_handlers=["/metrics"]).instrument(app).expose(app, tags=["Status"])


@app.on_event("startup")
async def startup_event():
    logger.info("Starting up...")
    await media.startup()
    await db.startup()


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down...")
    await db.shutdown()
    await media.shutdown()


@app.get("/", include_in_schema=False)
async def root(request: Request):
    """
    Redirects root calls to the API documentation.
    The root path is used to make sure the redirect is correct.
    """
    return RedirectResponse(f"{request.scope.get('root_path')}/docs", status_code=status.HTTP_301_MOVED_PERMANENTLY)


@app.get("/ping", tags=["Status"])
async def ping():
    """
    Ping the server
    """
    return "pong"

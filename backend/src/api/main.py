"""
FastAPI application entry-point for ASCA AI backend.

Endpoints
---------
GET  /health             — Liveness probe (UI status chips)
GET  /api/meta           — Bootstrap payload (centres + crops)
POST /api/chat           — Conversational AI (full agent pipeline)
GET  /api/market/forecast — Prophet 14-day price curve
GET  /api/market/insights — Parallel market basket scan
GET  /api/b2b/buyers          — Registered buyer registry
POST /api/b2b/match           — FEFO-ranked surplus matching
GET  /api/cultivation/crops   — DOA crop agronomic profiles
POST /api/cultivation/recommend — AI-ranked crop recommendations
GET  /api/cultivation/guide/{id} — Full cultivation guide & agronomy
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import chat as chat_router
from src.api.routes import market as market_router
from src.api.routes import b2b as b2b_router
from src.api.routes import auth as auth_router
from src.api.routes import cultivation as cultivation_router
from src.api.routes import blueprints as blueprints_router
from src.api.schemas import (
    CropOption,
    EconomicCentre,
    HealthResponse,
    MetaResponse,
)
from src.infrastructure.config import config
from src.infrastructure.logging import logger
from src.services.crop_catalog import (
    DEFAULT_CROP_BASKET,
    crop_label,
    list_centres,
)

# --------------------------------------------------------------------------- #
# App
# --------------------------------------------------------------------------- #
app = FastAPI(
    title="ASCA AI — Agricultural Supply Chain Advisory",
    description=(
        "Multi-agent AI backend for Sri Lankan agricultural market forecasting, "
        "surplus detection, and B2B buyer matching."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# --------------------------------------------------------------------------- #
# CORS — allow the Vite dev server (and any configured production origin)
# --------------------------------------------------------------------------- #
ALLOWED_ORIGINS = [
    "http://localhost:5173",   # Vite dev
    "http://localhost:4173",   # Vite preview
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------- #
# Routers
# --------------------------------------------------------------------------- #
app.include_router(auth_router.router)          # /api/auth/*         — public
app.include_router(chat_router.router)          # /api/chat           — JWT protected
app.include_router(market_router.router)        # /api/market/        — JWT protected
app.include_router(b2b_router.router)           # /api/b2b/           — JWT protected
app.include_router(cultivation_router.router)   # /api/cultivation/   — JWT protected
app.include_router(blueprints_router.router)    # /api/blueprints     — JWT protected


# --------------------------------------------------------------------------- #
# Meta / health routes
# --------------------------------------------------------------------------- #
@app.get("/health", response_model=HealthResponse, tags=["meta"])
async def health() -> HealthResponse:
    """Liveness probe polled by the frontend status chip."""
    llm_ok = bool(config.env.OPENROUTER_API_KEY or config.env.OPENAI_API_KEY or config.env.GOOGLE_API_KEY)
    ws_ok = bool(config.env.TAVILY_API_KEY)
    status = "ok" if llm_ok else "degraded"
    return HealthResponse(
        status=status,
        llm_provider=config.env.DEFAULT_LLM_PROVIDER,
        llm_configured=llm_ok,
        web_search_enabled=ws_ok,
        environment=config.env.APP_ENV,
    )


@app.get("/api/meta", response_model=MetaResponse, tags=["meta"])
async def meta() -> MetaResponse:
    """
    Bootstrap payload loaded once by the frontend at startup.
    Returns the list of economic centres and the supported crop catalogue so the
    UI never hard-codes domain constants.
    """
    raw_centres = list_centres()
    centres = [
        EconomicCentre(
            id=c["id"],
            name=c["name"],
            location=c["location"],
            short=c["short"],
        )
        for c in raw_centres
    ]
    crops = [CropOption(id=name, label=crop_label(name)) for name in DEFAULT_CROP_BASKET]

    return MetaResponse(centres=centres, crops=crops)


# --------------------------------------------------------------------------- #
# Startup / shutdown hooks
# --------------------------------------------------------------------------- #
@app.on_event("startup")
async def _startup() -> None:
    from src.infrastructure.db import init_db
    await init_db()
    logger.info("ASCA AI FastAPI server started — all agents ready.")


@app.on_event("shutdown")
async def _shutdown() -> None:
    logger.info("ASCA AI FastAPI server shutting down.")

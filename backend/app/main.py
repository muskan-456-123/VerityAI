from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

load_dotenv()

from app.database.repository import initialize
from app.models.schemas import HealthResponse
from app.routes.verification import router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    initialize()
    yield


app = FastAPI(title="VERITY API", version="0.1.0", docs_url="/api/docs", redoc_url=None, lifespan=lifespan)
app.include_router(router)


@app.get("/health", response_model=HealthResponse, include_in_schema=False)
def health() -> HealthResponse:
    return HealthResponse(
        groq_configured=bool(os.getenv("GROQ_API_KEY")),
        tavily_configured=bool(os.getenv("TAVILY_API_KEY")),
    )


frontend_dist = Path(os.getenv("FRONTEND_DIST", "frontend/dist"))
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")

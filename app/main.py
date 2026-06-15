from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import init_db
from app.routers import rates, providers
from app.scheduler import start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    yield


app = FastAPI(
    title="Electricity Tariff API",
    description="""
    Aggregates electricity tariff data scraped from provider websites.

    ## Features
    - Browse providers and their current rates
    - Filter by region, type (fixed/variable), and rate
    - Designed for Home Assistant REST sensor integration
    - Data refreshed automatically on a schedule
    """,
    version="0.1.0",
    contact={"name": "Yllen Fernandez", "url": "https://links.yllen.dev"},
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(providers.router, prefix="/providers", tags=["Providers"])
app.include_router(rates.router, prefix="/rates", tags=["rates"])


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "docs": "/docs"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}

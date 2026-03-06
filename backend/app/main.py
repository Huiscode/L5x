from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import health, parse

app = FastAPI(
    title="app-L5x API",
    version="0.1.0",
    description="Offline local backend for L5X parsing and engineering workflows.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(parse.router)

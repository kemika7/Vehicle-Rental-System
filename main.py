import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine
from models.base import Base
import models  # noqa: F401 — registers all models with Base.metadata
from routers import auth, health, vehicle, rental

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Vehicle Rental System",
    description="Office vehicle rental management API",
    version="0.1.0",
)

# Read allowed origins from env so production can lock down to the real domain.
# Default allows Vite dev server and Docker Compose nginx origin.
_cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:80,http://localhost",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(vehicle.router)
app.include_router(rental.router)

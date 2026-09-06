"""
FastAPI application factory. Imported by both:
  - lambda_handler.py (wrapped with Mangum for AWS Lambda + API Gateway)
  - local uvicorn dev server (`uvicorn app.main:app --reload`)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.utils.exceptions import register_exception_handlers

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["health"])
async def health_check():
    """Lightweight endpoint for API Gateway / load balancer health checks."""
    return {"status": "ok", "env": settings.ENV}

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.invoices import router as invoices_router
from app.api.metrics import router as metrics_router

app = FastAPI(
    title="Invoice Pipeline API",
    description="FastAPI service for invoice processing",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(invoices_router)
app.include_router(metrics_router)

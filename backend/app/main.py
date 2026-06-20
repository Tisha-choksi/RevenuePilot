from fastapi import FastAPI

from app.api.leads import router as leads_router
from app.api.workflows import router as workflows_router
from app.core.config import settings

app = FastAPI(title=settings.app_name)
app.include_router(leads_router)
app.include_router(workflows_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}

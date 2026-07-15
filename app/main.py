import uvicorn
from fastapi import FastAPI

from app.api.v1.support import router as support_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title="AI Support Ticket Resolution API", version="1.0.0")
    app.include_router(support_router)
    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)

from fastapi import FastAPI

from src.api.routes import runs_router, threads_router
from src.utils.logger import create_logger

logger = create_logger(name="LatticeAPI", path="./logs", filename="api.log")


def create_app() -> FastAPI:
    """factory function for fastapi app"""
    app = FastAPI(
        title="Lattice API",
        description="LangGraph-compatible API",
        version="0.1.0",
    )

    # include routers
    app.include_router(runs_router)
    app.include_router(threads_router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    logger.info("fastapi app created")
    return app


# for uvicorn direct run
app = create_app()

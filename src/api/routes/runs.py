from fastapi import APIRouter, HTTPException

from src.schemas.api import RunCreateStateless
from src.services.agent import invoke_agent
from src.services.stores import run_store
from src.utils.logger import create_logger

logger = create_logger(name="RunsRoute", path="./logs", filename="api.log")
router = APIRouter(tags=["runs"])


@router.post("/runs/wait")
async def create_stateless_run(request: RunCreateStateless) -> dict:
    """
    stateless run - no thread persistence
    invokes the agent and returns output immediately
    """
    logger.info("stateless run request received")

    # create a temp run for tracking (no thread)
    run = run_store.create(thread_id="stateless")
    run_store.update_status(run.run_id, "running")

    try:
        result = invoke_agent(request.input.messages)
        run_store.update_status(run.run_id, "success")
        logger.info(f"stateless run {run.run_id} completed")
        return result
    except Exception as e:
        run_store.update_status(run.run_id, "error")
        logger.error(f"stateless run failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

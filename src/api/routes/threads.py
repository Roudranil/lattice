from fastapi import APIRouter, HTTPException

from src.schemas.api import RunCreateStateful, Thread, ThreadCreate, ThreadState
from src.services.agent import get_thread_state, invoke_agent
from src.services.stores import run_store, thread_store
from src.utils.logger import create_logger

logger = create_logger(name="ThreadsRoute", path="./logs", filename="api.log")
router = APIRouter(tags=["threads"])


@router.post("/threads", response_model=Thread)
async def create_thread(request: ThreadCreate = None) -> Thread:
    """create a new conversation thread"""
    req = request or ThreadCreate()
    thread = thread_store.create(
        thread_id=req.thread_id,
        metadata=req.metadata,
    )
    logger.info(f"created thread {thread.thread_id}")
    return thread


@router.get("/threads/{thread_id}", response_model=Thread)
async def get_thread(thread_id: str) -> Thread:
    """get thread by id"""
    thread = thread_store.get(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="thread not found")
    return thread


@router.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str) -> dict:
    """delete a thread"""
    deleted = thread_store.delete(thread_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="thread not found")
    logger.info(f"deleted thread {thread_id}")
    return {"deleted": True}


@router.get("/threads/{thread_id}/state", response_model=ThreadState)
async def get_state(thread_id: str) -> ThreadState:
    """get current thread state (message history)"""
    # verify thread exists in our store
    thread = thread_store.get(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="thread not found")

    state = get_thread_state(thread_id)
    return ThreadState(**state)


@router.post("/threads/{thread_id}/runs/wait")
async def create_thread_run(thread_id: str, request: RunCreateStateful = None) -> dict:
    """
    run agent on thread and wait for output
    uses checkpointer for conversation persistence
    """
    # verify thread exists
    thread = thread_store.get(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="thread not found")

    req = request or RunCreateStateful()
    messages = req.input.messages if req.input else []

    # create run and update thread status
    run = run_store.create(thread_id=thread_id)
    thread_store.update_status(thread_id, "busy")
    run_store.update_status(run.run_id, "running")

    logger.info(f"starting run {run.run_id} on thread {thread_id}")

    try:
        result = invoke_agent(messages, thread_id=thread_id)
        run_store.update_status(run.run_id, "success")
        thread_store.update_status(thread_id, "idle")
        logger.info(f"run {run.run_id} completed")
        return result
    except Exception as e:
        run_store.update_status(run.run_id, "error")
        thread_store.update_status(thread_id, "error")
        logger.error(f"run {run.run_id} failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

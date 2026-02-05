from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# run schemas
class RunInput(BaseModel):
    messages: List[Dict[str, Any]]


class RunCreateStateless(BaseModel):
    input: RunInput


class RunCreateStateful(BaseModel):
    input: Optional[RunInput] = None


class Run(BaseModel):
    run_id: str
    thread_id: str
    status: Literal["pending", "running", "success", "error", "interrupted"]
    created_at: datetime
    updated_at: datetime


# thread schemas
class ThreadCreate(BaseModel):
    thread_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class Thread(BaseModel):
    thread_id: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
    status: Literal["idle", "busy", "interrupted", "error"]


class ThreadState(BaseModel):
    values: Dict[str, Any]
    next: List[str]


__all__ = [
    "RunInput",
    "RunCreateStateless",
    "RunCreateStateful",
    "Run",
    "ThreadCreate",
    "Thread",
    "ThreadState",
]

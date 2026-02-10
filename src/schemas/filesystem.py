from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel


class Info(BaseModel):
    name: str
    path: str
    type: Literal["file", "directory"]


class FileContent(BaseModel):
    info: Dict
    start: int
    end: int
    content: str


class FSResponse(BaseModel):
    status: str
    error: Optional[str]
    response: Optional[Any]

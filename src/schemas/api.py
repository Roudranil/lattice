from datetime import datetime
from typing import Any, Dict, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

__all__ = ["Message"]


class Message(BaseModel):
    role: str
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """validate the content of the string
        - must not be empty
        - must not contain null bytes

        Parameters
        ----------
        v : str
            the value of the content

        Returns
        -------
        str
            the validated value
        """
        if not v:
            raise ValueError("content must not be empty")
        if "\x00" in v:
            raise ValueError("content must not contain null bytes")
        return v


class Thread(BaseModel):
    thread_id: str | UUID = Field(
        title="Thread ID",
        description="Thread ID",
    )
    created_at: datetime = Field(
        ..., title="Created At", description="The time the thread was created."
    )
    updated_at: datetime = Field(
        ..., title="Updated At", description="The last time the thread was updated."
    )
    metadata: Dict[str, Any] = Field(
        ..., title="Metadata", description="The thread metadata."
    )
    config: Optional[Dict[str, Any]] = Field(
        None, title="Config", description="The thread config."
    )
    status: Literal["idle", "busy", "interrupted", "error"] = Field(
        ..., title="Status", description="The status of the thread."
    )
    values: Optional[Any] = Field(
        None, title="Values", description="The current state of the thread."
    )
    interrupts: Optional[Any] = Field(
        None, title="Interrupts", description="The current interrupts of the thread."
    )


class ThreadCreate(BaseModel):
    thread_id: Optional[UUID] = Field(
        title="Thread Id",
        description="The ID of the thread. If not provided, a random UUID will be generated.",
        default_factory=lambda: str(UUID(int=datetime.now().timestamp())),
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, title="Metadata", description="Metadata to add to thread."
    )
    if_exists: Literal["raise", "do_nothing"] = Field(
        "raise",
        title="If Exists",
        description="How to handle duplicate creation. 'raise' or 'do_nothing'.",
    )

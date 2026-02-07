from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from src.schemas.api import Run, Thread


class ThreadStore:
    """in-memory thread storage for mvp"""

    def __init__(self):
        self._threads: Dict[str, Thread] = {}

    def create(
        self, thread_id: Optional[str] = None, metadata: Optional[Dict] = None
    ) -> Thread:
        tid = thread_id or str(uuid4())
        now = datetime.utcnow()
        thread = Thread(
            thread_id=tid,
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
            status="idle",
        )
        self._threads[tid] = thread
        return thread

    def get(self, thread_id: str) -> Optional[Thread]:
        return self._threads.get(thread_id)

    def delete(self, thread_id: str) -> bool:
        if thread_id in self._threads:
            del self._threads[thread_id]
            return True
        return False

    def update_status(self, thread_id: str, status: str) -> None:
        if thread_id in self._threads:
            # pydantic is immutable by default, so recreate
            t = self._threads[thread_id]
            self._threads[thread_id] = t.model_copy(
                update={"status": status, "updated_at": datetime.utcnow()}
            )


class RunStore:
    """in-memory run metadata storage"""

    def __init__(self):
        self._runs: Dict[str, Run] = {}

    def create(self, thread_id: str) -> Run:
        rid = str(uuid4())
        now = datetime.utcnow()
        run = Run(
            run_id=rid,
            thread_id=thread_id,
            status="pending",
            created_at=now,
            updated_at=now,
        )
        self._runs[rid] = run
        return run

    def get(self, run_id: str) -> Optional[Run]:
        return self._runs.get(run_id)

    def update_status(self, run_id: str, status: str) -> None:
        if run_id in self._runs:
            r = self._runs[run_id]
            self._runs[run_id] = r.model_copy(
                update={"status": status, "updated_at": datetime.utcnow()}
            )


# singleton instances
thread_store = ThreadStore()
run_store = RunStore()

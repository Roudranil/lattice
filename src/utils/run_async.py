import asyncio
import threading
from typing import TYPE_CHECKING, Any, AsyncIterator, Coroutine


class _AsyncThread(threading.Thread):
    """helper thread class for running async coroutines in a separate thread"""

    def __init__(self, coroutine: Coroutine[Any, Any, Any]):
        self.coroutine = coroutine
        self.result = None
        self.exception = None

        super().__init__(daemon=True)

    def run(self):
        try:
            self.result = asyncio.run(self.coroutine)
        except Exception as e:
            self.exception = e


def run_async_safely(coroutine: Coroutine[Any, Any], timeout: float | None = None):
    """safely runs a coroutine with handling of an existing event loop.

    This function detects if there's already a running event loop and uses
    a separate thread if needed to avoid the "asyncio.run() cannot be called
    from a running event loop" error. This is particularly useful in environments
    like Jupyter notebooks, FastAPI applications, or other async frameworks.

    Args:
        coroutine: The coroutine to run
        timeout: max seconds to wait for. None means hanging forever

    Returns:
        The result of the coroutine

    Raises:
        Any exception raised by the coroutine
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # There's a running loop, use a separate thread
        thread = _AsyncThread(coroutine)
        thread.start()
        thread.join(timeout=timeout)

        if thread.is_alive():
            raise TimeoutError("The operation timed out after %f seconds" % timeout)

        if thread.exception:
            raise thread.exception

        return thread.result
    else:
        if timeout:
            coroutine = asyncio.wait_for(coroutine, timeout)

        return asyncio.run(coroutine)

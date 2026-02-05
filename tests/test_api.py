"""
pytest test suite for lattice api
uses fastapi testclient to test without running server
mocks the agent service functions to avoid needing api keys

run with: uv run pytest tests/test_api.py -v
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.app import app
from src.services.stores import run_store, thread_store


@pytest.fixture
def client():
    """create test client and reset stores between tests"""
    thread_store._threads.clear()
    run_store._runs.clear()
    return TestClient(app)


@pytest.fixture
def mock_agent_service():
    """
    mock invoke_agent and get_thread_state functions
    avoids importing main.py which requires env vars
    """
    mock_messages = [
        {"role": "user", "content": "Hello!"},
        {"role": "assistant", "content": "Hi there! How can I help?"},
    ]

    with (
        patch("src.api.routes.runs.invoke_agent") as mock_invoke_runs,
        patch("src.api.routes.threads.invoke_agent") as mock_invoke_threads,
        patch("src.api.routes.threads.get_thread_state") as mock_get_state,
    ):
        mock_invoke_runs.return_value = {"messages": mock_messages}
        mock_invoke_threads.return_value = {"messages": mock_messages}
        mock_get_state.return_value = {
            "values": {"messages": mock_messages},
            "next": [],
        }

        yield {
            "invoke_runs": mock_invoke_runs,
            "invoke_threads": mock_invoke_threads,
            "get_state": mock_get_state,
        }


class TestHealth:
    def test_health_returns_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


class TestThreads:
    def test_create_thread_with_defaults(self, client):
        r = client.post("/threads", json={})
        assert r.status_code == 200
        data = r.json()
        assert "thread_id" in data
        assert data["status"] == "idle"
        assert data["metadata"] == {}

    def test_create_thread_with_custom_id(self, client):
        r = client.post("/threads", json={"thread_id": "my-thread"})
        assert r.status_code == 200
        assert r.json()["thread_id"] == "my-thread"

    def test_create_thread_with_metadata(self, client):
        r = client.post("/threads", json={"metadata": {"foo": "bar"}})
        assert r.status_code == 200
        assert r.json()["metadata"] == {"foo": "bar"}

    def test_get_thread(self, client):
        r = client.post("/threads", json={})
        thread_id = r.json()["thread_id"]

        r = client.get(f"/threads/{thread_id}")
        assert r.status_code == 200
        assert r.json()["thread_id"] == thread_id

    def test_get_thread_not_found(self, client):
        r = client.get("/threads/nonexistent")
        assert r.status_code == 404

    def test_delete_thread(self, client):
        r = client.post("/threads", json={})
        thread_id = r.json()["thread_id"]

        r = client.delete(f"/threads/{thread_id}")
        assert r.status_code == 200
        assert r.json()["deleted"] is True

        r = client.get(f"/threads/{thread_id}")
        assert r.status_code == 404

    def test_delete_thread_not_found(self, client):
        r = client.delete("/threads/nonexistent")
        assert r.status_code == 404


class TestStatelessRuns:
    def test_stateless_run(self, client, mock_agent_service):
        r = client.post(
            "/runs/wait",
            json={"input": {"messages": [{"role": "user", "content": "Hello"}]}},
        )
        assert r.status_code == 200
        data = r.json()
        assert "messages" in data
        mock_agent_service["invoke_runs"].assert_called_once()


class TestThreadRuns:
    def test_run_on_thread(self, client, mock_agent_service):
        r = client.post("/threads", json={})
        thread_id = r.json()["thread_id"]

        r = client.post(
            f"/threads/{thread_id}/runs/wait",
            json={"input": {"messages": [{"role": "user", "content": "Hi"}]}},
        )
        assert r.status_code == 200
        assert "messages" in r.json()

    def test_run_on_nonexistent_thread(self, client, mock_agent_service):
        r = client.post(
            "/threads/nonexistent/runs/wait",
            json={"input": {"messages": [{"role": "user", "content": "Hi"}]}},
        )
        assert r.status_code == 404

    def test_run_updates_thread_status(self, client, mock_agent_service):
        r = client.post("/threads", json={})
        thread_id = r.json()["thread_id"]

        client.post(
            f"/threads/{thread_id}/runs/wait",
            json={"input": {"messages": [{"role": "user", "content": "Hi"}]}},
        )

        r = client.get(f"/threads/{thread_id}")
        assert r.json()["status"] == "idle"


class TestThreadState:
    def test_get_thread_state(self, client, mock_agent_service):
        r = client.post("/threads", json={})
        thread_id = r.json()["thread_id"]

        r = client.get(f"/threads/{thread_id}/state")
        assert r.status_code == 200
        data = r.json()
        assert "values" in data
        assert "next" in data

    def test_get_state_thread_not_found(self, client):
        r = client.get("/threads/nonexistent/state")
        assert r.status_code == 404

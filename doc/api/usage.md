# Lattice API Usage Guide
Python examples for using the Lattice API endpoints.
## Setup
```python
import httpx
BASE_URL = "http://localhost:8000"
client = httpx.Client(base_url=BASE_URL, timeout=60.0)
```

## Health Check
```python
r = client.get("/health")
print(r.json())
# {"status": "ok"}
```

## Stateless Runs
Single request/response without conversation persistence.
```python
r = client.post("/runs/wait", json={
    "input": {
        "messages": [
            {"role": "user", "content": "What is quantum entanglement?"}
        ]
    }
})
result = r.json()
print(result["messages"][-1]["content"])
```

## Thread Management
### Create Thread
```python
# auto-generated id
r = client.post("/threads", json={})
thread = r.json()
thread_id = thread["thread_id"]
# custom id
r = client.post("/threads", json={"thread_id": "my-session-123"})
# with metadata
r = client.post("/threads", json={
    "metadata": {"user_id": "user_456", "topic": "physics"}
})
```
### Get Thread
```python
r = client.get(f"/threads/{thread_id}")
thread = r.json()
print(thread["status"])  # "idle", "busy", "interrupted", "error"
```
### Delete Thread
```python
r = client.delete(f"/threads/{thread_id}")
print(r.json())  # {"deleted": true}
```

## Thread Runs
Run agent on a thread with conversation persistence.
```python
# create thread
r = client.post("/threads", json={})
thread_id = r.json()["thread_id"]
# first message
r = client.post(f"/threads/{thread_id}/runs/wait", json={
    "input": {
        "messages": [{"role": "user", "content": "Hello!"}]
    }
})
print(r.json()["messages"][-1]["content"])
# follow-up (context is preserved)
r = client.post(f"/threads/{thread_id}/runs/wait", json={
    "input": {
        "messages": [{"role": "user", "content": "What did I just say?"}]
    }
})
print(r.json()["messages"][-1]["content"])
```

## Thread State
Get current conversation state.
```python
r = client.get(f"/threads/{thread_id}/state")
state = r.json()
# all messages in the thread
for msg in state["values"]["messages"]:
    print(f"{msg['role']}: {msg['content'][:50]}...")
# next nodes to execute (empty if complete)
print(state["next"])
```

## Async Example
```python
import httpx
import asyncio
async def chat_async():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        # create thread
        r = await client.post("/threads", json={})
        thread_id = r.json()["thread_id"]
        # run
        r = await client.post(f"/threads/{thread_id}/runs/wait", json={
            "input": {"messages": [{"role": "user", "content": "Hi!"}]}
        })
        return r.json()
result = asyncio.run(chat_async())
```

## Error Handling
```python
r = client.get("/threads/nonexistent")
if r.status_code == 404:
    print("Thread not found")
r = client.post("/runs/wait", json={"input": {"messages": []}})
if r.status_code == 500:
    error = r.json()
    print(f"Error: {error['detail']}")
```

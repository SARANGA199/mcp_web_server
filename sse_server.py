from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from sse_starlette.sse import EventSourceResponse
import asyncio
import uvicorn
from fastmcp import FastMCP
from typing import Dict, Any

app = FastAPI(title="FastMCP No-Auth Server")
mcp = FastMCP("FastMCP-NoAuth")

sse_connections: Dict[str, asyncio.Queue] = {}

# SSE Connection Endpoint for Langflow


@app.get("/connect/{client_id}")
async def connect(client_id: str, request: Request):
    q: asyncio.Queue = asyncio.Queue()
    sse_connections[client_id] = q
    print(f"SSE client connected: {client_id}")

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=15.0)
                except asyncio.TimeoutError:
                    yield "\n"
                    continue
                yield {"event": "message", "data": msg}
        finally:
            sse_connections.pop(client_id, None)
            print(f"SSE client disconnected: {client_id}")

    return EventSourceResponse(event_generator())


# ✅ MCP Tools
@mcp.tool
async def echo(message: str) -> str:
    return f"ECHO: {message}"


@mcp.tool
async def send_sms(number: str, message: str) -> Dict[str, Any]:
    await asyncio.sleep(0.5)
    return {"to": number, "status": "sent", "message": message}


# Simple POST endpoint to trigger tools
@app.post("/run/{tool_name}")
async def run_tool(tool_name: str, payload: Dict[str, Any]):
    fn = getattr(mcp, "tools", {}).get(tool_name)
    if fn is None:
        raise HTTPException(status_code=404, detail="Tool not found")

    result = await fn(**payload)

    # Broadcast tool execution event
    for q in list(sse_connections.values()):
        try:
            q.put_nowait(f"{tool_name} executed")
        except:
            pass

    return result


# Health check
@app.get("/health")
async def health():
    return "ok"


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)

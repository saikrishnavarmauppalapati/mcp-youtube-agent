from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from mcp import Client
import json

app = FastAPI()

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Client("youtube-mcp", "http://localhost:3001")

class AgentRequest(BaseModel):
    message: str


async def call_mcp_agent(message: str):
    """
    Sends the user message to the MCP Agent and returns a structured response.
    """
    try:
        result = await client.query(message)

        # Ensure we always return a dictionary
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except:
                return {"status": result}

        if not isinstance(result, dict):
            return {"status": "Unknown MCP response"}

        # Normalize output fields
        if "videos" in result:
            return {"results": result["videos"]}

        if "results" in result:
            return {"results": result["results"]}

        if "status" in result:
            return {"status": result["status"]}

        return {"status": "Action completed"}

    except Exception as e:
        print("MCP ERROR:", e)
        return {"error": str(e)}


@app.post("/agent/run")
async def run_agent(req: AgentRequest):
    return await call_mcp_agent(req.message)

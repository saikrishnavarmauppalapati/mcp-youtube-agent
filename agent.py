from fastapi import APIRouter
from pydantic import BaseModel
from openai import OpenAI
import requests
import os

router = APIRouter()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TOOL_API = {
    "search": "http://localhost:8000/mcp/youtube/search",
    "like": "http://localhost:8000/mcp/youtube/like/",
    "comment": "http://localhost:8000/mcp/youtube/comment",
    "subscribe": "http://localhost:8000/mcp/youtube/subscribe"
}

class AgentRequest(BaseModel):
    message: str

@router.post("/agent/run")
async def run_agent(req: AgentRequest):
    user_message = req.message

    # Step 1 → Ask LLM to choose tool
    prompt = """
    You are a YouTube assistant. Choose exactly one tool to execute:
    search, like, comment, subscribe.
    Output JSON ONLY:
    {"tool": "search", "args": {"query": "text"}}
    """
    llm_resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "system", "content": prompt},
                  {"role": "user", "content": user_message}]
    )

    import json
    tool_call = json.loads(llm_resp.choices[0].message.content)
    tool_name = tool_call["tool"]
    args = tool_call.get("args", {})

    # Step 2 → Call the corresponding backend tool endpoint
    if tool_name == "search":
        r = requests.post(TOOL_API["search"], json=args)
        return r.json()
    elif tool_name == "like":
        video_id = args.get("video_id")
        r = requests.post(f"{TOOL_API['like']}{video_id}")
        return r.json()
    elif tool_name == "comment":
        r = requests.post(TOOL_API["comment"], json=args)
        return r.json()
    elif tool_name == "subscribe":
        r = requests.post(TOOL_API["subscribe"], json=args)
        return r.json()
    else:
        return {"error": "Unknown tool"}

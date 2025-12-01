import os
import requests
from fastapi import APIRouter
from pydantic import BaseModel
from openai import OpenAI
import json

router = APIRouter()

# Render URL backend
BASE_URL = "https://mcp-youtube-agent-xw94.onrender.com"

# Initialize OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Tool mapping
TOOL_API = {
    "search": f"{BASE_URL}/mcp/youtube/search",
    "like": f"{BASE_URL}/mcp/youtube/like/",
    "comment": f"{BASE_URL}/mcp/youtube/comment",
    "subscribe": f"{BASE_URL}/mcp/youtube/subscribe",
    "liked": f"{BASE_URL}/mcp/youtube/liked",
    "recommend": f"{BASE_URL}/mcp/youtube/recommend"
}

# Agent request model
class AgentRequest(BaseModel):
    message: str

@router.post("/agent/run")
async def run_agent(req: AgentRequest):
    user_message = req.message

    # Step 1 → Ask LLM to choose tool
    system_prompt = """
    You are a YouTube AI assistant.
    Choose exactly one tool to execute from: search, like, comment, subscribe, liked, recommend.
    Output JSON ONLY: {"tool": "tool_name", "args": {"param": "value"}}
    If the user asks for recommendations, use 'recommend'.
    If the user asks for liked videos, use 'liked'.
    """

    llm_resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    )

    try:
        tool_call = json.loads(llm_resp.choices[0].message.content)
    except Exception as e:
        return {"error": "Failed to parse LLM response", "details": str(e)}

    tool_name = tool_call.get("tool")
    args = tool_call.get("args", {})

    # Step 2 → Call backend tool
    if tool_name not in TOOL_API:
        return {"error": "Unknown tool"}

    if tool_name in ["search", "comment", "subscribe"]:
        r = requests.post(TOOL_API[tool_name], json=args)
    elif tool_name == "like":
        video_id = args.get("video_id")
        r = requests.post(f"{TOOL_API['like']}{video_id}")
    else:  # liked or recommend
        r = requests.get(TOOL_API[tool_name])

    try:
        return r.json()
    except:
        return {"response": r.text}

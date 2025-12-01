# agent.py
import os
import json
import requests
from fastapi import APIRouter, Request
from pydantic import BaseModel
from openai import OpenAI

router = APIRouter()
BASE_URL = "https://mcp-youtube-agent-xw94.onrender.com"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TOOL_API = {
    "search": f"{BASE_URL}/mcp/youtube/search",
    "like": f"{BASE_URL}/mcp/youtube/like/",
    "comment": f"{BASE_URL}/mcp/youtube/comment",
    "subscribe": f"{BASE_URL}/mcp/youtube/subscribe",
    "liked": f"{BASE_URL}/mcp/youtube/liked",
    "recommend": f"{BASE_URL}/mcp/youtube/recommend"
}

class AgentRequest(BaseModel):
    message: str

@router.post("/agent/run")
async def run_agent(req: AgentRequest, request: Request):
    user_message = req.message
    incoming_auth = request.headers.get("Authorization")
    headers = {"Authorization": incoming_auth} if incoming_auth else {}

    system_prompt = """
    You are a YouTube AI assistant. Output STRICTLY a JSON object with this format:
    {"tool":"<tool_name>", "args": {...}}

    Valid tools: search, like, comment, subscribe, liked, recommend
    Respond ONLY with the JSON object.
    """

    llm_resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        max_tokens=512,
    )

    raw = llm_resp.choices[0].message.content.strip()
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        tool_call = json.loads(raw[start:end])
    except Exception as e:
        return {"error": "Failed to parse LLM JSON", "raw": raw, "details": str(e)}

    tool = tool_call.get("tool") or "search"
    args = tool_call.get("args", {}) or {}
    if tool == "search" and not args.get("query"):
        args["query"] = user_message

    if tool not in TOOL_API:
        return {"error": "Invalid tool", "tool": tool}

    # call corresponding backend
    try:
        if tool in ["search", "comment", "subscribe"]:
            r = requests.post(TOOL_API[tool], json=args, headers=headers)
        elif tool == "like":
            vid = args.get("video_id")
            if not vid:
                return {"error": "like requires video_id"}
            r = requests.post(TOOL_API["like"] + vid, headers=headers)
        else:  # liked or recommend
            r = requests.get(TOOL_API[tool], headers=headers)
        return r.json()
    except Exception as e:
        return {"error": "Tool request failed", "details": str(e)}

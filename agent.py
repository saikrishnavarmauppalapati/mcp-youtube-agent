import os
import requests
from fastapi import APIRouter, Request
from pydantic import BaseModel
from openai import OpenAI
import json

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
    token = request.headers.get("Authorization")
    if not token:
        return {"error": "Please login to perform this action"}

    headers = {"Authorization": token}

    system_prompt = """
    You are a YouTube AI assistant.
    Choose exactly one tool to execute from: search, like, comment, subscribe, liked, recommend.
    Output JSON ONLY: {"tool": "tool_name", "args": {"param": "value"}}
    """

    llm_resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    )

    try:
        raw_content = llm_resp.choices[0].message.content.strip()
        start = raw_content.find("{")
        end = raw_content.rfind("}") + 1
        tool_call = json.loads(raw_content[start:end])
    except Exception as e:
        return {"error": "Failed to parse LLM response", "details": str(e), "raw": raw_content}

    tool_name = tool_call.get("tool")
    args = tool_call.get("args", {})

    if tool_name == "search" and not args.get("query"):
        args["query"] = user_message

    if tool_name not in TOOL_API:
        return {"error": "Unknown tool"}

    try:
        if tool_name in ["search", "comment", "subscribe"]:
            r = requests.post(TOOL_API[tool_name], json=args, headers=headers)
        elif tool_name == "like":
            video_id = args.get("video_id")
            if not video_id:
                return {"error": "No video_id provided for like"}
            r = requests.post(f"{TOOL_API['like']}{video_id}", headers=headers)
        else:  # liked or recommend
            r = requests.get(TOOL_API[tool_name], headers=headers)

        try:
            return r.json()
        except:
            return {"response": r.text}
    except Exception as e:
        return {"error": "Failed to call tool API", "details": str(e)}

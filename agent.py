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
    token = request.headers.get("Authorization")

    if not token:
        return {"error": "User not authenticated"}

    headers = {"Authorization": token}

    system_prompt = """
    You are a YouTube AI assistant. Always output this EXACT JSON format:

    {
        "tool": "search",
        "args": { "query": "devops" }
    }

    VALID tools:
    - search
    - like
    - comment
    - subscribe
    - liked
    - recommend

    Rules:
    - For search: args = { "query": "<search keywords>" }
    - For like: args = { "video_id": "<id>" }
    - For comment: args = { "video_id": "<id>", "text": "<comment>" }
    - For subscribe: args = { "channel_id": "<id>" }
    - For liked: args = {}
    - For recommend: args = {}

    Output ONLY JSON. No text before or after.
    """

    # -------------------------------
    # STEP 1: Ask LLM which tool to use
    # -------------------------------
    llm = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    )

    raw = llm.choices[0].message.content.strip()

    # Debug return
    print("\n\n===== RAW LLM OUTPUT =====")
    print(raw)
    print("==========================\n\n")

    # Extract only JSON
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        cleaned = raw[start:end]
        tool_call = json.loads(cleaned)
    except Exception as e:
        return {
            "error": "LLM JSON parse failed",
            "raw_output": raw,
            "details": str(e)
        }

    tool = tool_call.get("tool")
    args = tool_call.get("args", {})

    # Fallback for search text
    if tool == "search" and "query" not in args:
        args["query"] = user_message

    if tool not in TOOL_API:
        return {"error": "Invalid tool selected", "tool": tool}

    # -------------------------------
    # STEP 2: Call the backend tool
    # -------------------------------
    try:
        if tool in ["search", "comment", "subscribe"]:
            r = requests.post(TOOL_API[tool], json=args, headers=headers)

        elif tool == "like":
            r = requests.post(TOOL_API["like"] + args["video_id"], headers=headers)

        else:
            r = requests.get(TOOL_API[tool], headers=headers)

        # Debug output
        print("\n\n===== TOOL RESPONSE =====")
        print(r.text)
        print("=========================\n\n")

        try:
            return r.json()
        except:
            return {"error": "Tool returned invalid JSON", "raw": r.text}

    except Exception as e:
        return {"error": "Tool request failed", "details": str(e)}

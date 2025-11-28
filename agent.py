from fastapi import APIRouter
from pydantic import BaseModel
import os
import requests
from openai import OpenAI

router = APIRouter()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
YOUTUBE_API_URL = "http://localhost:8000/mcp/youtube/search"

client = OpenAI(api_key=OPENAI_API_KEY)

class ChatRequest(BaseModel):
    message: str

@router.post("/agent/chat")
async def agent_chat(req: ChatRequest):
    user_message = req.message
    
    # Step 1 → Ask LLM to decide action
    system_prompt = """
    You are a YouTube assistant bot.
    Your job is to understand the user query and choose EXACTLY one action:

    ACTIONS:
    1. search: Search YouTube videos
       - Output JSON: {"action":"search","query":"text"}

    If query is general, default to "search".
    Always respond EXCLUSIVELY in pure JSON ONLY.
    """

    llm = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    )

    action_json = llm.choices[0].message.content

    print("LLM DECISION:", action_json)

    # Step 2 → Parse action JSON (search only for now)
    import json
    data = json.loads(action_json)

    if data["action"] == "search":
        query = data["query"]
        res = requests.post(YOUTUBE_API_URL, json={"query": query})
        return {
            "action": "search",
            "query": query,
            "results": res.json()
        }

    return {"error": "unknown action"}

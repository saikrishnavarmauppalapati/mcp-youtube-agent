# mcp_server.py
import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from agent import router as agent_router

load_dotenv()
app = FastAPI(title="MCP YouTube Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://youtube-mcp-agent-frontend.vercel.app", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# In-memory token store
USER_TOKENS = {}

class SearchRequest(BaseModel):
    query: str

class CommentRequest(BaseModel):
    video_id: str
    text: str

class SubscribeRequest(BaseModel):
    channel_id: str

@app.get("/")
async def home():
    return {"message": "YouTube MCP Agent Running!"}

@app.get("/auth/login")
async def auth_login():
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        "&response_type=code"
        "&scope=https://www.googleapis.com/auth/youtube.force-ssl https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email"
        "&access_type=offline"
        "&prompt=consent"
    )
    return {"auth_url": auth_url}

@app.get("/auth/callback")
async def auth_callback(code: str):
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    r = requests.post(token_url, data=data)
    token_data = r.json()
    if "access_token" not in token_data:
        return {"error": "OAuth failed", "details": token_data}
    USER_TOKENS["access_token"] = token_data["access_token"]
    return {"message": "Login successful", "token": token_data}

@app.get("/auth/me")
async def auth_me(request: Request):
    token = request.headers.get("Authorization")
    if token and token.startswith("Bearer "):
        token = token.split(" ", 1)[1]
    elif USER_TOKENS.get("access_token"):
        token = USER_TOKENS["access_token"]

    if not token:
        return JSONResponse({"error": "not_authenticated"}, status_code=401)

    r = requests.get(
        "https://www.googleapis.com/oauth2/v1/userinfo?alt=json",
        headers={"Authorization": f"Bearer {token}"}
    )
    return r.json()

@app.post("/auth/logout")
async def logout():
    USER_TOKENS.clear()
    return {"status": "logged_out"}

# YouTube endpoints
@app.post("/mcp/youtube/search")
async def search_videos(req: SearchRequest, request: Request):
    headers = {"Authorization": request.headers.get("Authorization")} if request.headers.get("Authorization") else {}
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": req.query,
        "type": "video",
        "maxResults": 10,
        "key": YOUTUBE_API_KEY
    }
    r = requests.get(url, params=params, headers=headers)
    data = r.json()
    results = []
    for item in data.get("items", []):
        vid = item.get("id", {}).get("videoId") or item.get("id")
        results.append({
            "title": item["snippet"]["title"],
            "videoId": vid,
            "channelId": item["snippet"].get("channelId"),
            "description": item["snippet"].get("description"),
            "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"] if item["snippet"].get("thumbnails") else ""
        })
    return {"results": results}


# Include agent router
app.include_router(agent_router)

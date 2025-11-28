import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Load .env
load_dotenv()

# FastAPI app
app = FastAPI(title="MCP YouTube Agent")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow-Origin: https://youtube-mcp-agent-frontend.vercel.app
    allow-Credentials: true
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Simple in-memory token store
USER_TOKENS = {}  # { "access_token": "" }


# ----------------------------
# MODELS
# ----------------------------
class SearchRequest(BaseModel):
    query: str

class CommentRequest(BaseModel):
    video_id: str
    text: str

class SubscribeRequest(BaseModel):
    channel_id: str


# ----------------------------
# ROOT
# ----------------------------
@app.get("/")
async def home():
    return {"message": "YouTube MCP Agent Running!"}


# ----------------------------
# OAuth Login URL
# ----------------------------
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


# ----------------------------
# OAuth Callback
# ----------------------------
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


# ----------------------------
# USER INFO
# ----------------------------
@app.get("/auth/me")
async def auth_me():
    token = USER_TOKENS.get("access_token")
    if not token:
        return JSONResponse({"error": "not_authenticated"}, status_code=401)

    r = requests.get(
        "https://www.googleapis.com/oauth2/v1/userinfo?alt=json",
        headers={"Authorization": f"Bearer {token}"}
    )

    return r.json()


# ----------------------------
# LOGOUT
# ----------------------------
@app.post("/auth/logout")
async def logout():
    USER_TOKENS.clear()
    return {"status": "logged_out"}


# ----------------------------
# VIDEO SEARCH
# ----------------------------
@app.post("/mcp/youtube/search")
async def search_videos(req: SearchRequest):

    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": req.query,
        "type": "video",
        "maxResults": 10,
        "key": YOUTUBE_API_KEY
    }

    r = requests.get(url, params=params)
    data = r.json()

    results = []
    for item in data.get("items", []):
        results.append({
            "title": item["snippet"]["title"],
            "videoId": item["id"]["videoId"],
            "channelId": item["snippet"]["channelId"],
            "description": item["snippet"]["description"],
            "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"]
        })

    return {"results": results}


# ----------------------------
# LIKE VIDEO
# ----------------------------
@app.post("/mcp/youtube/like/{video_id}")
async def like_video(video_id: str):

    token = USER_TOKENS.get("access_token")
    if not token:
        return JSONResponse({"error": "not_authenticated"}, status_code=401)

    url = "https://www.googleapis.com/youtube/v3/videos/rate"
    params = {"id": video_id, "rating": "like"}

    headers = {"Authorization": f"Bearer {token}"}

    r = requests.post(url, params=params, headers=headers)

    return {"status": "liked", "response": r.text}


# ----------------------------
# COMMENT VIDEO
# ----------------------------
@app.post("/mcp/youtube/comment")
async def comment_video(req: CommentRequest):

    token = USER_TOKENS.get("access_token")
    if not token:
        return JSONResponse({"error": "not_authenticated"}, status_code=401)

    url = "https://www.googleapis.com/youtube/v3/commentThreads?part=snippet"

    payload = {
        "snippet": {
            "videoId": req.video_id,
            "topLevelComment": {
                "snippet": {
                    "textOriginal": req.text
                }
            }
        }
    }

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    r = requests.post(url, json=payload, headers=headers)

    return {"status": "commented", "response": r.text}


# ----------------------------
# SUBSCRIBE CHANNEL
# ----------------------------
@app.post("/mcp/youtube/subscribe")
async def subscribe(req: SubscribeRequest):

    token = USER_TOKENS.get("access_token")
    if not token:
        return JSONResponse({"error": "not_authenticated"}, status_code=401)

    url = "https://www.googleapis.com/youtube/v3/subscriptions?part=snippet"

    payload = {
        "snippet": {
            "resourceId": {
                "kind": "youtube#channel",
                "channelId": req.channel_id
            }
        }
    }

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    r = requests.post(url, json=payload, headers=headers)

    return {"status": "subscribed", "response": r.text}

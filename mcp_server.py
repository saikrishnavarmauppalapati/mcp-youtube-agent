# mcp_server.py
import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

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

# in-memory token store (kept for compatibility, but we will accept Authorization header)
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

    # store in memory for compatibility
    USER_TOKENS["access_token"] = token_data["access_token"]
    return {"message": "Login successful", "token": token_data}

@app.get("/auth/me")
async def auth_me(request: Request):
    # prefer Authorization header
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
    elif USER_TOKENS.get("access_token"):
        token = USER_TOKENS.get("access_token")

    if not token:
        return JSONResponse({"error": "not_authenticated"}, status_code=401)

    r = requests.get("https://www.googleapis.com/oauth2/v1/userinfo?alt=json",
                     headers={"Authorization": f"Bearer {token}"})
    return r.json()

@app.post("/auth/logout")
async def logout():
    USER_TOKENS.clear()
    return {"status": "logged_out"}

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
    try:
        r = requests.get(url, params=params)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return {"error": "YouTube API request failed", "details": str(e)}

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

# Helper to get auth from header or in-memory store
def _get_auth_header(request: Request):
    auth = request.headers.get("Authorization")
    if auth:
        return {"Authorization": auth}
    if USER_TOKENS.get("access_token"):
        return {"Authorization": f"Bearer {USER_TOKENS['access_token']}"}
    return {}

@app.post("/mcp/youtube/like/{video_id}")
async def like_video(video_id: str, request: Request):
    headers = _get_auth_header(request)
    if not headers:
        return JSONResponse({"error": "not_authenticated"}, status_code=401)
    url = "https://www.googleapis.com/youtube/v3/videos/rate"
    params = {"id": video_id, "rating": "like"}
    r = requests.post(url, params=params, headers=headers)
    return {"status": "liked", "response": r.text}

@app.post("/mcp/youtube/comment")
async def comment_video(req: CommentRequest, request: Request):
    headers = _get_auth_header(request)
    if not headers:
        return JSONResponse({"error": "not_authenticated"}, status_code=401)
    url = "https://www.googleapis.com/youtube/v3/commentThreads?part=snippet"
    payload = {
        "snippet": {
            "videoId": req.video_id,
            "topLevelComment": {"snippet": {"textOriginal": req.text}}
        }
    }
    r = requests.post(url, json=payload, headers={**headers, "Content-Type": "application/json"})
    return {"status": "commented", "response": r.text}

@app.post("/mcp/youtube/subscribe")
async def subscribe(req: SubscribeRequest, request: Request):
    headers = _get_auth_header(request)
    if not headers:
        return JSONResponse({"error": "not_authenticated"}, status_code=401)
    url = "https://www.googleapis.com/youtube/v3/subscriptions?part=snippet"
    payload = {"snippet": {"resourceId": {"kind": "youtube#channel", "channelId": req.channel_id}}}
    r = requests.post(url, json=payload, headers={**headers, "Content-Type": "application/json"})
    return {"status": "subscribed", "response": r.text}

@app.get("/mcp/youtube/liked")
async def liked_videos(request: Request):
    headers = _get_auth_header(request)
    if not headers:
        return JSONResponse({"error": "not_authenticated"}, status_code=401)
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {"myRating": "like", "part": "snippet", "maxResults": 10}
    r = requests.get(url, params=params, headers=headers)
    try:
        r.raise_for_status()
        data = r.json()
    except Exception:
        return {"error": "Failed to fetch liked videos"}
    results = []
    for item in data.get("items", []):
        results.append({
            "title": item["snippet"]["title"],
            "videoId": item["id"],
            "channelId": item["snippet"].get("channelId"),
            "description": item["snippet"].get("description"),
            "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"] if item["snippet"].get("thumbnails") else ""
        })
    return {"results": results}

@app.get("/mcp/youtube/recommend")
async def recommend_videos(request: Request):
    headers = _get_auth_header(request)
    if not headers:
        return JSONResponse({"error": "not_authenticated"}, status_code=401)
    liked_resp = await liked_videos(request)
    results = []
    for item in liked_resp.get("results", []):
        query = item["title"]
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {"part": "snippet", "q": query, "type": "video", "maxResults": 3, "key": YOUTUBE_API_KEY}
        r = requests.get(url, params=params)
        data = r.json()
        for vid in data.get("items", []):
            video_id = vid["id"].get("videoId") if isinstance(vid["id"], dict) else vid["id"]
            results.append({
                "title": vid["snippet"]["title"],
                "videoId": video_id,
                "channelId": vid["snippet"].get("channelId"),
                "description": vid["snippet"].get("description"),
                "thumbnail": vid["snippet"]["thumbnails"]["medium"]["url"] if vid["snippet"].get("thumbnails") else ""
            })
    return {"results": results}

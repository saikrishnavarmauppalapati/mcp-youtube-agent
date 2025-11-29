📺 MCP YouTube Agent – Backend

A lightweight FastAPI backend that provides YouTube automation (search, like, comment, subscribe) and authentication via Google OAuth.
Designed to work with the YouTube MCP Frontend and your AI Agent.

🚀 Features

🔐 Google OAuth login

🔍 Search YouTube videos

👍 Like videos

💬 Comment on videos

🔔 Subscribe to channels

👤 Fetch authenticated user profile

⚙️ FastAPI server

🔗 Fully integrated MCP tools

📁 Project Structure
backend/
├── agent.py
├── mcp_server.py
├── requirements.txt
└── __pycache__/

🔧 Installation

Clone repo:

git clone <your-backend-repo-url>
cd backend


Create virtual environment:

python3 -m venv venv
source venv/bin/activate


Install dependencies:

pip install -r requirements.txt

🔑 Environment Variables

Create a .env file:

YOUTUBE_CLIENT_ID=your_google_client_id
YOUTUBE_CLIENT_SECRET=your_google_client_secret
YOUTUBE_REDIRECT_URI=https://your-frontend.vercel.app/auth/callback

FRONTEND_URL=https://your-frontend.vercel.app
BACKEND_URL=https://your-backend.onrender.com
SECRET_KEY=any-random-string

▶️ Running the Server

Start server:

uvicorn mcp_server:app --host 0.0.0.0 --port 8000 --reload


Server runs at:

http://localhost:8000

🌐 API Endpoints
Authentication
Method	Endpoint	Description
GET	/auth/login	Returns Google OAuth login URL
GET	/auth/callback	OAuth redirect handler
GET	/auth/me	Get logged-in user info
POST	/auth/logout	Logout and clear cookies
YouTube Actions
Method	Endpoint	Description
POST	/mcp/youtube/search	Search YouTube
POST	/mcp/youtube/like/{videoId}	Like a video
POST	/mcp/youtube/comment	Comment on a video
POST	/mcp/youtube/subscribe	Subscribe to channel
🤖 MCP Tools

Backend exposes these MCP tools:

search_videos

like_video

comment_video

subscribe_channel

get_user_info

These are consumed by the frontend.

📦 Deployment on Render

Create a Render Web Service.

Build Command:

pip install -r requirements.txt


Start Command:

uvicorn mcp_server:app --host 0.0.0.0 --port 10000


Add environment variables.
Deploy.

🧪 Testing

Test server:

curl https://your-backend.onrender.com/


Test login URL:

curl https://your-backend.onrender.com/auth/login


Test search:

curl -X POST https://your-backend.onrender.com/mcp/youtube/search \
  -H "Content-Type: application/json" \
  -d '{"query": "chatgpt"}'

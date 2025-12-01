# YouTube AI Agent Backend

This repository contains the backend application for the YouTube AI Agent project. The backend is built using **FastAPI**, **Python**, and **Requests**, and provides APIs for YouTube automation and Google OAuth authentication to be used by the frontend MCP client.

---

## 🚀 Features

* 🔐 Google OAuth Login (YouTube Authentication)
* 🔍 Search YouTube videos
* 👍 Like videos
* 💬 Comment on videos
* 🔔 Subscribe to channels
* 👤 Fetch authenticated user profile
* ⚡ Fast and lightweight FastAPI server
* 🔗 Fully integrated with MCP frontend for AI-powered actions

---

## 📂 Project Structure

```
backend/
├── mcp_server.py
├── requirements.txt
└── __pycache__/
```

---

## 🛠️ Tech Stack

* **Python 3.10+**
* **FastAPI**
* **Requests**
* **Pydantic** (data validation)
* **YouTube Data API v3**
* **Google OAuth 2.0**
* **MCP Client Integration**

---

## 🔧 Setup Instructions

### 1️⃣ Clone the repository

```bash
git clone <backend_repo_url>
cd backend
```

### 2️⃣ Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Create `.env` file

```
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
REDIRECT_URI=https://your-frontend.vercel.app/auth/callback
YOUTUBE_API_KEY=your_youtube_api_key
```

### 5️⃣ Run the development server

```bash
uvicorn mcp_server:app --host 0.0.0.0 --port 8000 --reload
```

Server runs at: **[http://localhost:8000](http://localhost:8000)**

---

## 🔗 API Endpoints

### Authentication

| Method | Endpoint         | Description                    |
| ------ | ---------------- | ------------------------------ |
| GET    | `/auth/login`    | Returns Google OAuth login URL |
| GET    | `/auth/callback` | OAuth redirect handler         |
| GET    | `/auth/me`       | Get logged-in user info        |
| POST   | `/auth/logout`   | Logout user                    |

### YouTube Actions

| Method | Endpoint                      | Description            |
| ------ | ----------------------------- | ---------------------- |
| POST   | `/mcp/youtube/search`         | Search YouTube videos  |
| POST   | `/mcp/youtube/like/{videoId}` | Like a video           |
| POST   | `/mcp/youtube/comment`        | Comment on a video     |
| POST   | `/mcp/youtube/subscribe`      | Subscribe to a channel |

---

## 🧪 Testing

Test the server:

```bash
curl http://localhost:8000/
```

Test login URL:

```bash
curl http://localhost:8000/auth/login
```

Test search API:

```bash
curl -X POST http://localhost:8000/mcp/youtube/search \
  -H "Content-Type: application/json" \
  -d '{"query": "chatgpt"}'
```

---

## 🚀 Deployment

The backend can be deployed on **Render**, **Heroku**, or any Python-compatible cloud service.

**Render example:**

* **Build Command:**

```bash
pip install -r requirements.txt
```

* **Start Command:**

```bash
uvicorn mcp_server:app --host 0.0.0.0 --port 10000
```

* Set environment variables in Render dashboard.

---



MIT License

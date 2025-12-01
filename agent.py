@router.post("/agent/run")
async def run_agent(req: AgentRequest, request: Request):
    user_message = req.message

    # Extract user token from frontend
    token = request.headers.get("Authorization")  # "Bearer <token>"
    if not token:
        return {"error": "You must login to perform this action"}

    headers = {"Authorization": token}

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
        raw_content = llm_resp.choices[0].message.content
        tool_call = json.loads(raw_content)
    except Exception as e:
        return {"error": "Failed to parse LLM response", "details": str(e)}

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
        return r.json()
    except Exception as e:
        return {"error": "Failed to call tool API", "details": str(e)}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    history: list = []

@app.post("/api/chat")
async def chat(req: ChatRequest):
    messages = [
        {
            "role": "system",
            "content": "You are a helpful CRM and project tracking assistant."
        },
        *req.history,
        {"role": "user", "content": req.message}
    ]

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "qwen3:8b",  # confirm this matches your ollama list
                "stream": False,
                "messages": messages
            }
        )
        data = response.json()

    return {"reply": data["message"]["content"]}
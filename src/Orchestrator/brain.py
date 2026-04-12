from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import importlib
from src.Orchestrator.Tools.registry import get_tool, get_tool_descriptions_for_prompt

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
    context: dict = {}  # current tab, open contact, etc.

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL      = "qwen3:8b"


async def classify_intent(message: str, history: list) -> tuple[str, dict]:
    """Ask Qwen which tool to use and extract parameters."""

    tool_descriptions = get_tool_descriptions_for_prompt()

    system_prompt = f"""You are an intent classifier for a CRM assistant.
Based on the user message, choose the best tool and extract parameters.

Available tools:
{tool_descriptions}

Respond in this exact JSON format only, no other text:
{{
  "tool": "<tool_name>",
  "params": {{}}
}}

If no tool fits, use "general_query"."""

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(OLLAMA_URL, json={
            "model": MODEL,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                *history[-6:],  # last 3 turns for context
                {"role": "user", "content": message},
            ],
        })
        data = res.json()

    import json
    text = data["message"]["content"].strip()
    try:
        parsed = json.loads(text)
        return parsed.get("tool", "general_query"), parsed.get("params", {})
    except Exception:
        return "general_query", {}


async def call_agent(tool_name: str, params: dict) -> dict:
    """Dynamically import and run the right agent."""
    tool = get_tool(tool_name)
    if not tool:
        return {"error": f"Tool not found: {tool_name}"}

    module = importlib.import_module(tool.agent_module)
    params["action"] = tool_name
    return await module.run(params)


async def generate_reply(message: str, tool_result: dict, history: list) -> str:
    """Turn a tool result into a natural language reply."""
    system = """You are a helpful CRM assistant. 
Given a tool result, respond naturally and concisely to the user.
Do not mention tools or technical details."""

    content = f"Tool result: {tool_result}\nUser asked: {message}"

    async with httpx.AsyncClient(timeout=60.0) as client:
        res = await client.post(OLLAMA_URL, json={
            "model": MODEL,
            "stream": False,
            "messages": [
                {"role": "system", "content": system},
                *history[-6:],
                {"role": "user", "content": content},
            ],
        })
        data = res.json()

    return data["message"]["content"]


@app.post("/api/chat")
async def chat(req: ChatRequest):
    # 1. Classify intent and extract params
    tool_name, params = await classify_intent(req.message, req.history)

    # 2. Call the right agent
    tool_result = await call_agent(tool_name, {**params, **req.context})

    # 3. Generate natural language reply
    reply = await generate_reply(req.message, tool_result, req.history)

    return {
        "reply": reply,
        "tool_used": tool_name,
        "tool_result": tool_result,  # useful for frontend to act on (e.g. open_tab)
    }
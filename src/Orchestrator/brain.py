from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import importlib
from src.Orchestrator.Agents import task_agent
from src.Orchestrator.Tools.registry import get_tool, get_tool_descriptions_for_prompt
from src.Orchestrator.Agents.email_agent import get_db
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    history: list = []
    context: dict = {}  # current tab, open contact, etc.
    model: str | None = None
    intent_model: str | None = None

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL      = "qwen3:8b"
INTENT_MODEL = "gemma4:e4b"  # can be different if you want a smaller/faster model for intent classification

OLLAMA_TIMEOUT = httpx.Timeout(
    connect=10.0,   # time to establish connection
    read=300.0,     # time to wait for response — models can be slow (increased to 5 min)
    write=10.0,
    pool=10.0
)


def parse_ollama_content(data: dict, default: str = "") -> str:
    message = data.get("message")
    if not message:
        print(f"[WARN] Ollama response missing 'message' field: {data}")
        return default

    content = message.get("content")
    if content is None:
        print(f"[WARN] Ollama response missing 'content': {data}")
        return default

    if not isinstance(content, str):
        print(f"[WARN] Ollama response content is not a string: {type(content).__name__} - {content}")
        return str(content)

    return content


async def classify_intent(message: str, history: list, intent_model: str = INTENT_MODEL) -> dict:
    """
    Use a small model to classify if the user query is general small talk OR needs tool-based action.
    Does NOT have access to tool registry - just summarizes intent.
    
    Returns a dict with:
    - is_general_query: bool
    - direct_response: str (if general query - the small model's answer)
    - intent_summary: str (if needs action - summary of what user wants)
    """

    system_prompt = """You are an intent analyzer for a CRM assistant.
Analyze the user message and determine if they are:
1. Making small talk / general conversation (greetings, casual questions)
2. Asking for something that requires system actions (adding contacts, checking emails, etc)

Respond in this exact JSON format only, no other text:
{
  "type": "small_talk" OR "action_needed",
  "intent_summary": "what the user is trying to accomplish",
  "details": "any important details from their request"
}

Examples:
- "Hi there!" → type: "small_talk"
- "Add a contact named John" → type: "action_needed"
- "How are you?" → type: "small_talk"
- "Show me my emails" → type: "action_needed"
"""

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            res = await client.post(OLLAMA_URL, json={
                "model": intent_model,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    *history[-6:],
                    {"role": "user", "content": message},
                ],
            })
            data = res.json()
            content = parse_ollama_content(data)
            # Debug logging
            print(f"[DEBUG] Model used: {data.get('model', 'unknown')}")
            print(f"[DEBUG] Raw response: {content[:200]}")  # first 200 chars

        import json
        text = content.strip()
        try:
            print(f"[DEBUG] Raw intent response: {text}")
            parsed = json.loads(text)
            intent_type = parsed.get("type", "small_talk")
            
            # If it's small talk, have the small model answer directly
            if intent_type == "small_talk":
                answer_prompt = """You are a helpful CRM assistant. 
Respond naturally and concisely to the user's message."""
                
                async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
                    answer_res = await client.post(OLLAMA_URL, json={
                        "model": INTENT_MODEL,
                        "stream": False,
                        "messages": [
                            {"role": "system", "content": answer_prompt},
                            *history[-6:],
                            {"role": "user", "content": message},
                        ],
                    })
                    answer_data = answer_res.json()
                
                return {
                    "is_general_query": True,
                    "direct_response": parse_ollama_content(
                        answer_data,
                        default="I'm sorry, I could not generate a reply."
                    ),
                }
            
            # If it needs action, return the intent summary for the large model
            return {
                "is_general_query": False,
                "intent_summary": parsed.get("intent_summary", message),
                "details": parsed.get("details", ""),
            }
        except Exception as e:
            print(f"[WARN] Failed to parse intent JSON: {e}")
            return {
                "is_general_query": False,
                "intent_summary": message,
                "details": "",
            }
    except Exception as e:
        print(f"[WARN] Ollama classify_intent failed: {e}. Treating as action_needed.")
        return {
            "is_general_query": False,
            "intent_summary": message,
            "details": "",
        }


async def resolve_tool(intent_summary: str, details: str, history: list, model: str = MODEL) -> tuple[str, dict]:
    """
    Use the large model with access to tool registry to determine which tool to call.
    The intent has already been summarized by the small model.
    """

    tool_descriptions = get_tool_descriptions_for_prompt()

    system_prompt = f"""You are a tool resolver for a CRM assistant.
Given a user's intent, choose the best tool to use and extract parameters.

Available tools:
{tool_descriptions}

Respond in this exact JSON format only, no other text:
{{
  "tool": "<tool_name>",
  "params": {{}}
}}
"""

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            res = await client.post(OLLAMA_URL, json={
                "model": model,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    *history[-6:],
                    {"role": "user", "content": f"Intent: {intent_summary}\nDetails: {details}"},
                ],
            })
            data = res.json()
            content = parse_ollama_content(data)
            print(f"[DEBUG] Model used: {data.get('model', 'unknown')}")
            print(f"[DEBUG] Raw response: {content[:200]}")  # first 200 chars

        import json
        text = content.strip()
        try:
            parsed = json.loads(text)
            return parsed.get("tool", "general_query"), parsed.get("params", {})
        except Exception:
            return "general_query", {}
    except Exception as e:
        print(f"[WARN] Ollama resolve_tool failed: {e}. Falling back to general_query.")
        return "general_query", {}


async def call_agent(tool_name: str, params: dict, model: str | None = None) -> dict:
    """Dynamically import and run the right agent."""
    tool = get_tool(tool_name)
    if not tool:
        return {"error": f"Tool not found: {tool_name}"}

    module = importlib.import_module(tool.agent_module)
    params["action"] = tool_name
    if model:
        params["model"] = model
    return await module.run(params)


async def generate_reply(message: str, tool_result: dict, history: list, model: str = MODEL) -> str:
    """Turn a tool result into a natural language reply."""
    system = """You are a helpful CRM assistant. 
Given a tool result, respond naturally and concisely to the user.
Do not mention tools or technical details."""

    content = f"Tool result: {tool_result}\nUser asked: {message}"

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            res = await client.post(OLLAMA_URL, json={
                "model": model,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system},
                    *history[-6:],
                    {"role": "user", "content": content},
                ],
            })
            data = res.json()

        content = parse_ollama_content(data, default="")
        if not content.strip():
            print(f"[WARN] Ollama generate_reply returned empty content: {data}")
            raise ValueError("Empty Ollama response content")
        return content
    except Exception as e:
        print(f"[WARN] Ollama generate_reply failed: {e}. Returning fallback response.")
        return f"Tool executed successfully: {tool_result}"


@app.get("/api/clients")
async def get_clients():
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, name, domain FROM clients ORDER BY name"
        )
        rows = await cursor.fetchall()
        clients = []
        for client_id, name, domain in rows:
            contact_cursor = await db.execute(
                "SELECT id, name, email, role FROM contacts WHERE client_id = ? ORDER BY name",
                (client_id,)
            )
            contacts = [
                {
                    "id": contact_id,
                    "name": contact_name,
                    "email": email,
                    "role": role,
                }
                for contact_id, contact_name, email, role in await contact_cursor.fetchall()
            ]
            clients.append({
                "id": client_id,
                "name": name,
                "domain": domain,
                "contacts": contacts,
            })
        return {"clients": clients}
    finally:
        await db.close()


@app.post("/api/chat")
async def chat(req: ChatRequest):
    import asyncio
    try:
        # Wrap entire operation with timeout (6 minutes for model processing)
        async def _chat():
            # 1. Classify intent using SMALL model (no tool registry - just summarizes)
            intent_result = await classify_intent(
                req.message,
                req.history,
                intent_model=req.intent_model or INTENT_MODEL,
            )
            
            # If it's a general query, return the small model's direct response
            if intent_result["is_general_query"]:
                return {
                    "reply": intent_result["direct_response"],
                    "tool_used": "general_query",
                    "tool_result": {"type": "general_response", "message": req.message},
                }
            
            llm_model = req.model or MODEL
            intent_model = req.intent_model or INTENT_MODEL

            # 2. Use LARGE model to resolve which tool to call based on the intent summary
            tool_name, params = await resolve_tool(
                intent_result["intent_summary"], 
                intent_result["details"], 
                req.history,
                model=llm_model,
            )
            
            # 3. Call the right agent
            tool_result = await call_agent(tool_name, {**params, **req.context}, model=llm_model)

            # 4. Generate natural language reply using the larger model
            reply = await generate_reply(req.message, tool_result, req.history, model=llm_model)

            return {
                "reply": reply,
                "tool_used": tool_name,
                "tool_result": tool_result,
            }
        
        result = await asyncio.wait_for(_chat(), timeout=360.0)
        return result
    except asyncio.TimeoutError:
        return {
            "reply": "The operation took too long to complete. Please try a simpler request or check that Ollama is running.",
            "tool_used": None,
            "tool_result": {"error": "Timeout - operation exceeded 6 minutes"},
        }
    except Exception as e:
        print(f"[ERROR] Chat endpoint error: {e}")
        return {
            "reply": f"Error: {str(e)}",
            "tool_used": None,
            "tool_result": {"error": str(e)},
        }
        
        
@app.post("/api/tasks/list")
async def list_tasks():
    return await task_agent.run({"action": "list_tasks"})

@app.post("/api/tasks/move")
async def move_task(payload: dict):
    return await task_agent.run({
        "action": "move_task",
        "task_id": payload.get("task_id"),
        "column": payload.get("column"),
    })

@app.post("/api/tasks/delete")
async def delete_task(payload: dict):
    return await task_agent.run({
        "action": "delete_task",
        "task_id": payload.get("task_id"),
    })

@app.post("/api/tasks/create")
async def create_task(payload: dict):
    return await task_agent.run({
        "action": "create_task",
        "title": payload.get("title"),
        "description": payload.get("description"),
        "priority": payload.get("priority"),
        "column": payload.get("column"),
        "due_date": payload.get("due_date"),
    })
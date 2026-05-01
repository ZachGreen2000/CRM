from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import importlib
from src.Orchestrator.Tools.registry import get_tool, get_tool_descriptions_for_prompt

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

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL      = "qwen3:8b"
INTENT_MODEL = "gemma4:e4b"  # can be different if you want a smaller/faster model for intent classification

OLLAMA_TIMEOUT = httpx.Timeout(
    connect=10.0,   # time to establish connection
    read=300.0,     # time to wait for response — models can be slow (increased to 5 min)
    write=10.0,
    pool=10.0
)


async def classify_intent(message: str, history: list) -> dict:
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
                "model": INTENT_MODEL,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    *history[-6:],
                    {"role": "user", "content": message},
                ],
            })
            data = res.json()
            # Debug logging
            print(f"[DEBUG] Model used: {data.get('model', 'unknown')}")
            print(f"[DEBUG] Raw response: {data['message']['content'][:200]}")  # first 200 chars

        import json
        text = data["message"]["content"].strip()
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
                    "direct_response": answer_data["message"]["content"],
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


async def resolve_tool(intent_summary: str, details: str, history: list) -> tuple[str, dict]:
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
                "model": MODEL,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    *history[-6:],
                    {"role": "user", "content": f"Intent: {intent_summary}\nDetails: {details}"},
                ],
            })
            data = res.json()
            print(f"[DEBUG] Model used: {data.get('model', 'unknown')}")
            print(f"[DEBUG] Raw response: {data['message']['content'][:200]}")  # first 200 chars

        import json
        text = data["message"]["content"].strip()
        try:
            parsed = json.loads(text)
            return parsed.get("tool", "general_query"), parsed.get("params", {})
        except Exception:
            return "general_query", {}
    except Exception as e:
        print(f"[WARN] Ollama resolve_tool failed: {e}. Falling back to general_query.")
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

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
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
    except Exception as e:
        print(f"[WARN] Ollama generate_reply failed: {e}. Returning fallback response.")
        return f"Tool executed successfully: {tool_result}"


@app.post("/api/chat")
async def chat(req: ChatRequest):
    import asyncio
    try:
        # Wrap entire operation with timeout (6 minutes for model processing)
        async def _chat():
            # 1. Classify intent using SMALL model (no tool registry - just summarizes)
            intent_result = await classify_intent(req.message, req.history)
            
            # If it's a general query, return the small model's direct response
            if intent_result["is_general_query"]:
                return {
                    "reply": intent_result["direct_response"],
                    "tool_used": "general_query",
                    "tool_result": {"type": "general_response", "message": req.message},
                }
            
            # 2. Use LARGE model to resolve which tool to call based on the intent summary
            tool_name, params = await resolve_tool(
                intent_result["intent_summary"], 
                intent_result["details"], 
                req.history
            )
            
            # 3. Call the right agent
            tool_result = await call_agent(tool_name, {**params, **req.context})

            # 4. Generate natural language reply using the larger model
            reply = await generate_reply(req.message, tool_result, req.history)

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
        
        
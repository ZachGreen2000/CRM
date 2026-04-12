# agents/general_agent.py
async def run(params: dict) -> dict:
    # direct pass-through to Qwen — no tool needed
    return {"reply": "stub general response", "message": params.get("message")}
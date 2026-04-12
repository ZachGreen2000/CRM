# agents/ui_agent.py
async def run(params: dict) -> dict:
    action = params.get("action")

    if action == "open_tab":
        return {"action": "open_tab", "tab_id": params.get("tab_id"), "label": params.get("label")}

    if action == "get_page_guidance":
        return await get_page_guidance(
            tab_id=params.get("current_tab_id"),
            question=params.get("question", ""),
        )

    return {"error": f"Unknown action: {action}"}


async def get_page_guidance(tab_id: str, question: str) -> dict:
    # call Qwen with page context
    return {"guidance": "stub response", "tab_id": tab_id}
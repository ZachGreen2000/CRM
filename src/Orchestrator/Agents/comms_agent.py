# agents/contact_agent.py
async def run(params: dict) -> dict:
    action = params.get("action")

    if action == "summarise_contact":
        return await summarise_contact(contact_id=params.get("contact_id"))

    return {"error": f"Unknown action: {action}"}


async def summarise_contact(contact_id: str) -> dict:
    return {"summary": "stub summary", "contact_id": contact_id}
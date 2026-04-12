# agents/email_agent.py
async def run(params: dict) -> dict:
    action = params.get("action")  # "fetch_emails" or "update_contact_from_email"

    if action == "fetch_emails":
        return await fetch_emails(
            limit=params.get("limit", 10),
            folder=params.get("folder", "INBOX"),
        )

    if action == "update_contact_from_email":
        return await update_contact_from_email(
            email_data=params.get("email_data"),
            contact_id=params.get("contact_id"),
        )

    return {"error": f"Unknown action: {action}"}


async def fetch_emails(limit: int, folder: str) -> dict:
    # IMAP logic goes here
    return {"emails": [], "status": "stub"}


async def update_contact_from_email(email_data: dict, contact_id: str) -> dict:
    # summarise email → update contact logic goes here
    return {"updated": False, "status": "stub"}
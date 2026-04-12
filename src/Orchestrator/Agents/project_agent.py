# agents/project_agent.py
async def run(params: dict) -> dict:
    action = params.get("action")

    if action == "summarise_project":
        return await summarise_project(
            project_id=params.get("project_id"),
            detail_level=params.get("detail_level", "normal"),
        )

    return {"error": f"Unknown action: {action}"}


async def summarise_project(project_id: str, detail_level: str) -> dict:
    return {"summary": "stub summary", "project_id": project_id}
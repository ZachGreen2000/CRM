import httpx
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:8b"
OLLAMA_TIMEOUT = httpx.Timeout(connect=10.0, read=300.0, write=10.0, pool=10.0)

async def run(params: dict) -> dict:
    action = params.get("action")

    if action == "open_tab":
        return {"action": "open_tab", "tab_id": params.get("tab_id"), "label": params.get("label")}

    if action == "get_page_guidance":
        return await get_page_guidance(
            tab_id=params.get("current_tab_id") or params.get("active_tab_id"),
            question=params.get("question", ""),
            context=params.get("context", {}) or {"active_tab_id": params.get("active_tab_id")},
        )

    return {"error": f"Unknown action: {action}"}


async def get_page_guidance(tab_id: str | None, question: str, context: dict | None = None) -> dict:
    ui_context_text = build_ui_context_text(tab_id, context or {})
    question_text = question.strip() or "Describe the current UI state and how to use the platform."

    system_prompt = (
        "You are a CRM UI assistant. Use the provided UI context to answer user questions about the sidebar, tabs, and navigating the application. "
        "Be concise, practical, and explain the interface in user-friendly language."
    )

    user_prompt = (
        f"Current tab: {tab_id or 'unknown'}\n"
        f"{ui_context_text}\n"
        f"User question: {question_text}\n"
        "Provide guidance for the user based on this UI context."
    )

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            response = await client.post(
                OLLAMA_URL,
                json={
                    "model": MODEL,
                    "stream": False,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                },
            )
            data = response.json()
            message = data.get("message") or {}
            content = message.get("content") if isinstance(message, dict) else message
            guidance = content or "I could not generate guidance from the UI context."
            return {"guidance": guidance, "tab_id": tab_id, "context": context or {}}
    except Exception as exc:
        return {"guidance": f"Failed to generate UI guidance: {exc}", "tab_id": tab_id, "context": context or {}}


def build_ui_context_text(tab_id: str | None, context: dict) -> str:
    lines = []
    lines.append("Platform UI context:")
    lines.append("- Sidebar: contains the main navigation and client/contact sections.")
    lines.append("- User icon: indicates the signed-in user and their role.")
    lines.append("- Tab window: shows the currently open page or record.")

    active_tab = context.get("active_tab_id")
    if active_tab:
        lines.append(f"- Active tab: {active_tab}")

    tabs = context.get("tabs")
    if isinstance(tabs, list) and tabs:
        open_tabs = []
        for tab in tabs:
            if isinstance(tab, dict):
                label = tab.get("label") or tab.get("id")
                open_tabs.append(label)
            else:
                open_tabs.append(str(tab))
        lines.append(f"- Open tabs: {', '.join(open_tabs)}")

    user = context.get("user")
    if user:
        lines.append(f"- User profile: {user}")

    sidebar_items = context.get("sidebar_items")
    if sidebar_items:
        lines.append(f"- Sidebar items: {sidebar_items}")

    if tab_id:
        if tab_id.startswith("client-"):
            lines.append(f"- The current tab is a client record: {tab_id}.")
        elif tab_id.startswith("contact-"):
            lines.append(f"- The current tab is a contact record: {tab_id}.")
        else:
            lines.append(f"- The current tab is: {tab_id}.")

    return "\n".join(lines)

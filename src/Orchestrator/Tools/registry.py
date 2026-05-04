# tool_registry.py
# Central registry of all tools the brain can call.
# Each tool maps to an agent file and describes when/how to use it.

from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class Tool:
    name: str                        # unique tool identifier
    description: str                 # what the tool does — used in LLM prompt
    agent_module: str                # dotted path to the agent file
    parameters: list[str]            # required parameters
    optional_params: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)  # example phrases that trigger this tool


TOOLS: dict[str, Tool] = {

    # ── Email ──────────────────────────────────────────────────────────────────
    "fetch_emails": Tool(
        name="fetch_emails",
        description=(
            "Connects to the IMAP inbox and fetches recent unread emails. "
            "Use when the user wants to check emails, sync inbox, or update contacts from email."
        ),
        agent_module="src.Orchestrator.Agents.email_agent",
        parameters=[],
        optional_params=["limit", "folder", "since_date"],
        examples=[
            "check my emails",
            "pull from inbox",
            "any new emails?",
            "sync my inbox",
        ],
    ),

    "search_emails": Tool(
        name="search_emails",
        description=(
            "Search through email content using semantic similarity. "
            "Find relevant emails based on meaning rather than exact keywords. "
            "Can filter by specific contact if contact_id is provided."
        ),
        agent_module="src.Orchestrator.Agents.email_agent",
        parameters=["query"],
        optional_params=["contact_id", "limit"],
        examples=[
            "find emails about project deadlines",
            "search for complaints from this contact",
            "look for emails mentioning budget",
            "find recent communications about pricing",
        ],
    ),

    # ── UI / Navigation ────────────────────────────────────────────────────────
    "open_tab": Tool(
        name="open_tab",
        description=(
            "Opens a tab in the frontend UI. Use when the user asks to navigate "
            "to a page, view a contact, open a project, or go to a section."
        ),
        agent_module="src.Orchestrator.Agents.ui_agent",
        parameters=["tab_id"],
        optional_params=["label"],
        examples=[
            "open the dashboard",
            "go to settings",
            "show me the contacts page",
            "open project X",
            "take me to tasks",
        ],
    ),

    "get_page_guidance": Tool(
        name="get_page_guidance",
        description=(
            "Provides contextual help and advice about the current page or feature "
            "the user is looking at. Use when the user asks how to do something "
            "in the app or what a section is for."
        ),
        agent_module="src.Orchestrator.Agents.ui_agent",
        parameters=["current_tab_id"],
        optional_params=["question"],
        examples=[
            "how do I use this page",
            "what can I do here",
            "help me with this section",
            "what does this tab do",
            "how do I add a contact",
        ],
    ),

    # ── Projects ───────────────────────────────────────────────────────────────
    "summarise_project": Tool(
        name="summarise_project",
        description=(
            "Generates an AI summary of a project including status, open tasks, "
            "recent activity, and next actions. Use when the user asks for a "
            "project overview or update."
        ),
        agent_module="src.Orchestrator.Agents.project_agent",
        parameters=["project_id"],
        optional_params=["detail_level"],
        examples=[
            "summarise project X",
            "give me an update on this project",
            "what's the status of project X",
            "how is project X going",
            "overview of current projects",
        ],
    ),

    # ── Contacts ───────────────────────────────────────────────────────────────
    "_generate_contact_summary": Tool(
        name="_generate_contact_summary",
        description=(
            "Generates an AI summary of a contact including recent interactions, "
            "open tasks, and relationship notes."
        ),
        agent_module="src.Orchestrator.Agents.email_agent",
        parameters=["contact_id"],
        optional_params=[],
        examples=[
            "summarise this contact",
            "give me a rundown on John",
            "what's the history with this client",
            "who is Jane Smith",
        ],
    ),

    "add_client": Tool(
        name="add_client",
        description=(
            "Adds a new client (business) to the CRM database. "
            "Use when the user wants to create or register a new company or organisation."
        ),
        agent_module="src.Orchestrator.Agents.email_agent",
        parameters=["name"],
        optional_params=["domain"],
        examples=[
            "add a new client",
            "create a client called Acme Ltd",
            "register a new company",
            "add Acme Ltd to the CRM",
            "new client: Acme Ltd, acme.com",
        ],
    ),

    "add_contact": Tool(
        name="add_contact",
        description=(
            "Adds a new contact (person) to the CRM database and links them to an existing client. "
            "Use when the user wants to add a person to a company already in the CRM. "
            "Requires a name and email. Client can be identified by name or ID."
        ),
        agent_module="src.Orchestrator.Agents.email_agent",
        parameters=["name", "email"],
        optional_params=["client_name", "client_id", "role"],
        examples=[
            "add a new contact",
            "add John Smith from Acme Ltd",
            "create a contact for jane@acme.com",
            "new contact: John Smith, CEO at Acme Ltd",
            "register a contact under Acme Ltd",
        ],
    ),

    # ── General ────────────────────────────────────────────────────────────────
    "general_query": Tool(
        name="general_query",
        description=(
            "Handles general conversation, questions, and anything that doesn't "
            "map to a specific tool. Falls back to direct Qwen response."
        ),
        agent_module="src.Orchestrator.Agents.general_agent",
        parameters=["message"],
        optional_params=["history"],
        examples=[],
    ),
}


def get_tool(name: str) -> Optional[Tool]:
    return TOOLS.get(name)


def get_all_tools() -> list[Tool]:
    return list(TOOLS.values())


def get_tool_descriptions_for_prompt() -> str:
    """
    Formats all tools into a string for injection into the
    intent classification prompt so the LLM knows what's available.
    """
    lines = []
    for tool in TOOLS.values():
        lines.append(f"- {tool.name}: {tool.description}")
    return "\n".join(lines)
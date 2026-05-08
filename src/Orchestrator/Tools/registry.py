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
            "Provides contextual help and advice about the current UI, sidebar, and open tab. "
            "Use when the user asks how to use the platform, what the current page does, "
            "or how to navigate the CRM interface."
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
            "Adds a new contact (person) to the CRM database and links them to a client. "
            "Use when the user wants to add a person to a company in the CRM. "
            "Requires name and email. Use CLIENT NAME to identify the company - "
            "the system will auto-create the client if it doesn't exist."
        ),
        agent_module="src.Orchestrator.Agents.email_agent",
        parameters=["name", "email", "client_name"],
        optional_params=["role"],
        examples=[
            "add a new contact",
            "add John Smith from Acme Ltd",
            "create a contact for jane@acme.com",
            "new contact: John Smith, CEO at Acme Ltd",
            "register a contact under Acme Ltd",
        ],
    ),

        # ── Tasks ──────────────────────────────────────────────────────────────────
    "create_task": Tool(
        name="create_task",
        description=(
            "Creates a new task on the task board. "
            "Use when the user wants to add, create, or log a task. "
            "Assigns it to a column (backlog, todo, inprogress, done) with an optional "
            "priority, due date, and description."
        ),
        agent_module="src.Orchestrator.Agents.task_agent",
        parameters=["title"],
        optional_params=["description", "priority", "column", "due_date"],
        examples=[
            "add a task to fix the login bug",
            "create a new task called update homepage",
            "log a high priority task for the client review",
            "new task: write release notes, due May 15",
            "add 'send invoice' to my to-do list",
        ],
    ),
 
    "update_task": Tool(
        name="update_task",
        description=(
            "Updates one or more fields on an existing task. "
            "Can change the title, description, priority, due date, or column. "
            "Use when the user wants to edit, rename, reprioritise, or reschedule a task. "
            "Requires task_id — use list_tasks or search_tasks first if the id is unknown."
        ),
        agent_module="src.Orchestrator.Agents.task_agent",
        parameters=["task_id"],
        optional_params=["title", "description", "priority", "column", "due_date"],
        examples=[
            "change the priority of the auth bug to critical",
            "rename the deploy task to 'deploy to production'",
            "update the due date on task 7 to May 20",
            "mark the performance audit as high priority",
            "edit the release task description",
        ],
    ),
 
    "move_task": Tool(
        name="move_task",
        description=(
            "Moves a task from one board column to another. "
            "Use when the user wants to progress, promote, or requeue a task. "
            "Accepted column values: backlog, todo, inprogress, done."
        ),
        agent_module="src.Orchestrator.Agents.task_agent",
        parameters=["task_id", "column"],
        optional_params=[],
        examples=[
            "move the deploy task to in progress",
            "mark task 6 as done",
            "put the auth bug back in backlog",
            "move release v2.3.0 to done",
            "start working on the performance audit",
            "push the migration task to to-do",
        ],
    ),
 
    "delete_task": Tool(
        name="delete_task",
        description=(
            "Permanently deletes a task from the board. "
            "Use only when the user explicitly asks to delete, remove, or discard a task. "
            "Requires task_id — use list_tasks or search_tasks first if the id is unknown."
        ),
        agent_module="src.Orchestrator.Agents.task_agent",
        parameters=["task_id"],
        optional_params=[],
        examples=[
            "delete the user interview task",
            "remove task 3 from the board",
            "discard the postgres migration task",
            "get rid of the old onboarding task",
        ],
    ),
 
    "list_tasks": Tool(
        name="list_tasks",
        description=(
            "Returns a list of tasks on the board, optionally filtered by column or priority. "
            "Use when the user wants to see what tasks exist, review the board, or before "
            "performing an update/move/delete when the task_id is unknown."
        ),
        agent_module="src.Orchestrator.Agents.task_agent",
        parameters=[],
        optional_params=["column", "priority", "due_date"],
        examples=[
            "what tasks do I have",
            "show me everything in backlog",
            "list all critical tasks",
            "what's in progress right now",
            "show me today's tasks",
            "what's on my board",
        ],
    ),
 
    "search_tasks": Tool(
        name="search_tasks",
        description=(
            "Searches tasks by title or description using semantic similarity. "
            "Use when the user refers to a task by a vague name or concept rather than "
            "an exact title, or when task_id is needed before an update/move/delete."
        ),
        agent_module="src.Orchestrator.Agents.task_agent",
        parameters=["query"],
        optional_params=["column", "limit"],
        examples=[
            "find the task about the login bug",
            "which task is about the staging environment",
            "look up the accessibility task",
            "find tasks related to deployment",
            "is there a task for the API docs",
        ],
    ),
 
    "summarise_tasks": Tool(
        name="summarise_tasks",
        description=(
            "Generates an AI summary of the current task board: overall progress, "
            "critical blockers, overdue items, and suggested next actions. "
            "Use when the user wants a high-level status report or daily standup briefing."
        ),
        agent_module="src.Orchestrator.Agents.task_agent",
        parameters=[],
        optional_params=["column", "project_id"],
        examples=[
            "give me a task summary",
            "what's the state of the board",
            "summarise my tasks for today",
            "what should I focus on",
            "give me a standup update",
            "any blockers or critical tasks?",
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
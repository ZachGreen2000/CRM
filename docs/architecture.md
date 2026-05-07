# Project Architecture Overview

This system employs a sophisticated, multi-layered, agent-driven architecture designed for complex, stateful reasoning. It is fundamentally a hybrid system combining modern SPA frontend capabilities with a powerful, modular Python backend core.

## 1. Architectural Layers

The system is structured into four primary, interacting layers:

### A. Presentation Layer (Frontend)
*   **Technology:** React/JSX (SPA).
*   **Purpose:** Provides the user interface for interaction.
*   **Key Components:** Components like `ContactProfile.jsx` and `Floatingchat.jsx` suggest direct user interaction points.

### B. Orchestration Layer (Backend Core)
*   **Technology:** Python.
*   **Core Module:** `src/Orchestrator/` (The "Brain").
*   **Function:** Acts as the central workflow director. It receives user intent, determines which specialized agent to invoke, manages the sequence of calls, and coordinates data flow between memory and services.
*   **Key Components:**
    *   **Agents:** Specialized workers (e.g., `email_agent`, `task_agent`) encapsulating specific business logic or personas.
    *   **Providers:** Abstracted interfaces for external LLM APIs (`openai`, `anthropic`, `ollama`).
    *   **Tools:** Defined interfaces allowing agents to perform controlled side effects on the system.

### C. Memory & State Layer
*   **Purpose:** To provide context and knowledge persistence, preventing context window overflow and enabling long-term recall.
*   **Components:**
    *   **Vector Store (`src/Memory/`):** Uses ChromaDB (`chroma_db/`) for semantic retrieval (RAG).
    *   **Summarization:** `thread_summarizer.py` actively compresses conversation history into actionable summaries.
    *   **Knowledge Graph:** `graph.py` suggests modeling explicit relationships between entities.

### D. Persistence Layer
*   **Purpose:** To store structured, factual, and semi-structured data.
*   **Components:**
    *   **Relational DB:** SQLite (`src/Database/crm.db`, defined by `schema.sql`). Used for structured records (e.g., CRM data).
    *   **Embeddings Store:** Dedicated storage for email embeddings (`src/Database/emailEmbeddings.sql`), linking unstructured content to structured retrieval.

## 2. Data Flow Summary
The typical flow is: **User Input $\rightarrow$ Orchestrator $\rightarrow$ (Retrieve Context from Memory/DB) $\rightarrow$ Agent Execution $\rightarrow$ (Call Tool/Provider) $\rightarrow$ State Update (Write to Memory/DB) $\rightarrow$ Response.**

## 3. Key Architectural Patterns
*   **Factory Pattern:** Used in `src/Settings/provider_factory.py` to decouple the core logic from specific LLM vendor implementations.
*   **Agent Pattern:** Specialized, role-based modules within `src/Orchestrator/Agents/`.
*   **Hybrid Persistence:** Seamlessly combines vector search (semantic) with relational storage (factual).
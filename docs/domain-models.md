# Core Domain Models\n\nThis document outlines the primary entities and their relationships as modeled across the system's persistence and logic layers.\n\n## 1. Core Entities\n\n### A. User/Client (Entity)
*   **Source:** `src/Database/crm.db`.
*   **Description:** Represents the primary individual or organization interacting with the system.
*   **Attributes (Inferred):** Client ID, Contact Information, Interaction History Summary.

### B. Conversation Thread (Knowledge Unit)\n*   **Source:** `src/Memory/`.
*   **Description:** A sequence of interactions between the user and the system. This is the raw, evolving context.
*   **Lifecycle:** Raw $\rightarrow$ Summarized $\rightarrow$ Vectorized.

### C. Knowledge Graph (Relationship Model)\n*   **Source:** `src/Memory/graph.py`.
*   **Description:** Models explicit relationships between entities (e.g., *Client A* **is associated with** *Project X*).

### D. Email/Communication Record (Data Point)\n*   **Source:** `src/Database/` (via `emailEmbeddings.sql`).
*   **Description:** A specific piece of communication data. It must be indexed both relationally (if metadata is key) and semantically (via embeddings).

## 2. Relationships & Data Flows\n
*   **Client $\leftrightarrow$ Conversation Thread:** A Client generates multiple Conversation Threads over time.
*   **Conversation Thread $\rightarrow$ Knowledge Graph:** Key facts extracted from a Conversation Thread are mapped into structured relationships within the Knowledge Graph.
*   **Knowledge Graph $\rightarrow$ Client:** The graph informs the system about the client's overall context, which is then used by the Orchestrator.
*   **Email Record $\leftrightarrow$ Knowledge Graph:** An email record can serve as the evidence supporting a relationship modeled in the Knowledge Graph.

## 3. Data Consistency Requirement\n
Maintaining consistency across the **Relational DB** (facts), the **Vector Store** (semantics), and the **Knowledge Graph** (relationships) is the most critical domain challenge for the system.
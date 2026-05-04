# CRM Email Assistant

A sophisticated CRM system with AI-powered email processing, vector embeddings, and incremental summarization.

## Architecture Overview

### Core Components

- **Frontend**: React-based UI for managing contacts, clients, and email interactions
- **Backend**: FastAPI server with AI orchestration
- **Database**: SQLite for relational data (emails, contacts, clients)
- **Vector Store**: ChromaDB for semantic search and embeddings
- **AI Models**: Ollama for embeddings and text generation

### Email Processing Pipeline

1. **Ingestion**: IMAP connection fetches unread emails
2. **Contact Resolution**: Matches emails to existing CRM contacts
3. **Vector Storage**: Email content embedded and stored in ChromaDB
4. **Thread Summarization**: Incremental AI summaries for email threads
5. **Retrieval**: Semantic search across email history

## Key Features

### Vector Embeddings & Retrieval
- Emails stored in SQLite with metadata
- Content embeddings stored in ChromaDB for efficient similarity search
- Semantic search capabilities for finding relevant emails

### Incremental Thread Summarization
- Thread summaries updated incrementally as new emails arrive
- Cached summaries reduce AI processing overhead
- Context-aware summarization using conversation history

### AI-Powered Contact Management
- Automatic contact summary generation
- Relationship insights from email patterns
- Smart contact matching and resolution

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 16+
- Ollama (for AI models)
- Gmail account with app password

### Installation

1. **Clone and setup Python environment:**
```bash
cd crm
python -m venv .venv
source .venv/Scripts/activate  # Windows
pip install -r requirements.txt
```

2. **Install ChromaDB:**
```bash
pip install chromadb
```

3. **Setup Ollama models:**
```bash
ollama pull nomic-embed-text  # For embeddings
ollama pull llama3            # For text generation
ollama pull qwen3:8b          # For intent classification
ollama pull gemma4:e4b        # For small tasks
```

4. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your Gmail credentials
```

5. **Initialize database:**
```bash
python migrate_db.py
```

6. **Setup frontend:**
```bash
npm install
npm start
```

7. **Start backend:**
```bash
npm run backend  # or: uvicorn src.Orchestrator.brain:app --reload --port 5000
```

## Database Schema

### Core Tables
- `clients`: Business organizations
- `contacts`: People within businesses
- `emails`: Individual email messages
- `contact_summaries`: AI-generated contact relationship summaries
- `thread_summaries`: Incremental email thread summaries

### Vector Collections (ChromaDB)
- `emails`: Email content embeddings with metadata
- `contact_summaries`: Contact summary embeddings
- `thread_summaries`: Thread summary embeddings

## API Endpoints

- `POST /api/chat`: Main AI chat interface
- Email processing handled through tool system

## Available Tools

- `fetch_emails`: Import emails from IMAP
- `search_emails`: Semantic search through email history
- `update_contact_from_email`: Update contact summaries
- `add_client`: Create new client records
- `add_contact`: Create new contact records

## Architecture Benefits

### Performance
- Vector similarity search for fast email retrieval
- Incremental summarization reduces AI API calls
- ChromaDB optimized for embedding operations

### Scalability
- Separate storage for relational vs vector data
- Efficient metadata filtering in vector searches
- Cached summaries for quick access

### Intelligence
- Semantic understanding of email content
- Context-aware conversation summarization
- Relationship insights from communication patterns

## Development

### Adding New Tools
1. Create agent function in `src/Orchestrator/Agents/`
2. Register tool in `src/Orchestrator/Tools/registry.py`
3. Add to agent's `run()` method

### Vector Store Operations
```python
from src.Memory.vector_store import get_vector_store

vector_store = get_vector_store()
# Store embeddings
await vector_store.store_email_embedding(email_id, content, embedding, metadata)
# Search similar content
results = await vector_store.search_similar_emails(query_embedding, contact_id=contact_id)
```

### Thread Summarization
```python
from src.Memory.thread_summarizer import get_thread_summarizer

summarizer = get_thread_summarizer()
# Update thread summary with new email
await summarizer.generate_incremental_summary(thread_id, contact_id, email_content, metadata)
```

## Troubleshooting

### Common Issues
- **Environment variables not loading**: Ensure `.env` file exists and `load_dotenv()` is called
- **ChromaDB connection issues**: Check if `./chroma_db` directory is writable
- **Ollama model not found**: Run `ollama pull <model_name>`
- **IMAP authentication failed**: Verify Gmail app password and 2FA settings

### Logs
Check console output for detailed logging:
- `[EMAIL_AGENT]`: Email processing steps
- `[VECTOR_STORE]`: Vector database operations
- `[THREAD_SUMMARIZER]`: Summary generation process

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.

### `npm test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can't go back!**

If you aren't satisfied with the build tool and configuration choices, you can `eject` at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point you're on your own.

You don't have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn't feel obligated to use this feature. However we understand that this tool wouldn't be useful if you couldn't customize it when you are ready for it.

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).

### Code Splitting

This section has moved here: [https://facebook.github.io/create-react-app/docs/code-splitting](https://facebook.github.io/create-react-app/docs/code-splitting)

### Analyzing the Bundle Size

This section has moved here: [https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size](https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size)

### Making a Progressive Web App

This section has moved here: [https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app](https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app)

### Advanced Configuration

This section has moved here: [https://facebook.github.io/create-react-app/docs/advanced-configuration](https://facebook.github.io/create-react-app/docs/advanced-configuration)

### Deployment

This section has moved here: [https://facebook.github.io/create-react-app/docs/deployment](https://facebook.github.io/create-react-app/docs/deployment)

### `npm run build` fails to minify

This section has moved here: [https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify](https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify)

# Smart Multi-User Chatbot with Data Analytics

Production-ready FastAPI backend for a multi-user, dataset-aware chatbot that uses Gemini + LangChain + FAISS for Retrieval-Augmented Generation (RAG), PostgreSQL for operational data, and Socket.IO for realtime chat.

## Overview

Users can:
- Register and authenticate with JWT
- Upload CSV or JSON datasets
- Automatically chunk and embed dataset rows with Gemini embeddings
- Chat with uploaded data using RAG
- Persist conversations and messages in PostgreSQL
- Access analytics for popular queries, dataset usage, and latency
- Receive realtime bot replies through Socket.IO
- Run locally with Docker Compose using API, PostgreSQL, Redis, and pgAdmin

## Tech Stack

- Backend: FastAPI
- ORM: SQLAlchemy Async
- Database: PostgreSQL
- GenAI: Google Gemini API
- RAG: LangChain
- Vector Store: FAISS
- Realtime: Socket.IO
- Testing: Pytest
- Containerization: Docker + Docker Compose

## Project Structure

```text
/project-root
├── app/
│   ├── config/
│   ├── controllers/
│   ├── db/
│   ├── middleware/
│   ├── models/
│   ├── repositories/
│   ├── routes/
│   ├── schemas/
│   ├── services/
│   ├── sockets/
│   ├── utils/
│   ├── dependencies.py
│   └── main.py
├── scripts/
│   └── create_indexes.sql
├── storage/
│   ├── faiss/
│   └── uploads/
├── tests/
├── postman_collection.json
├── Dockerfile
├── docker-compose.yml
├── README.md
├── requirements.txt
└── .env.example
```

## Architecture Diagram

```text
Client / Postman / Frontend
        |
        v
FastAPI REST + Socket.IO ASGI
        |
        v
Controllers
        |
        v
Services
  |        |         |         |
  |        |         |         +--> AnalyticsService
  |        |         +------------> AuthService
  |        +----------------------> DatasetService
  +-------------------------------> ChatService
                                      |
                                      +--> VectorService -> LangChain -> Gemini Embeddings -> FAISS
                                      +--> GeminiService -> Gemini Chat Model
                                      +--> Repositories -> PostgreSQL
```

## End-to-End Flow

1. User logs in and receives a JWT token.
2. User uploads a CSV or JSON dataset through `/api/v1/datasets/upload`.
3. `DatasetService` parses the file, stores normalized records, and converts rows into LangChain documents.
4. `VectorService` chunks documents using `RecursiveCharacterTextSplitter`.
5. Gemini embeddings are generated and written into a dataset-specific FAISS index under `storage/faiss/<dataset_id>`.
6. Metadata about the index is saved in `embeddings_metadata`.
7. User sends a chat message through REST or Socket.IO.
8. `ChatService` retrieves top-k chunks from FAISS, combines them with recent conversation history, and sends a constrained prompt to Gemini.
9. The answer, sources, and latency are stored in PostgreSQL and returned to the client.
10. `AnalyticsService` aggregates usage patterns from persisted chat data.

## RAG Pipeline Design

- Chunking strategy:
  Dataset rows are converted into structured text blocks and split with `chunk_size` and `chunk_overlap` from environment variables.
- Embeddings:
  Gemini embeddings are generated through `GoogleGenerativeAIEmbeddings`.
- Storage:
  FAISS stores vector indexes locally per dataset; metadata is tracked in PostgreSQL.
- Retrieval:
  Query-time similarity search fetches the top-k relevant chunks.
- Generation:
  Gemini receives retrieved context plus recent conversation history and is instructed to answer only from dataset evidence.

## Database Schema

### Tables

- `users`
  `id`, `email`, `full_name`, `password_hash`, `is_active`, timestamps
- `datasets`
  `id`, `owner_id`, `name`, `description`, `file_path`, `file_type`, `record_count`, `status`, `metadata_json`, timestamps
- `embeddings_metadata`
  `id`, `dataset_id`, `faiss_index_path`, `chunk_count`, `embedding_dimension`, `model_name`, `processing_time_ms`, `metadata_json`, timestamps
- `conversations`
  `id`, `user_id`, `dataset_id`, `title`, `status`, `metadata_json`, timestamps
- `messages`
  `id`, `conversation_id`, `role`, `content`, `latency_ms`, `metadata_json`, timestamps

### Relationships

- One user has many datasets
- One user has many conversations
- One dataset has many embedding metadata records
- One dataset has many conversations
- One conversation has many messages

### Indexing

SQL indexes are included in [scripts/create_indexes.sql](</d:/AI Projects/smart-chatbot-with-data-analytics/scripts/create_indexes.sql:1>) for:
- `datasets(owner_id, status)`
- `conversations(user_id, dataset_id)`
- `messages(conversation_id, role)`
- `messages(created_at)`

## API Usage

### 1. Register

`POST /api/v1/auth/register`

```json
{
  "email": "alice@example.com",
  "full_name": "Alice Analyst",
  "password": "StrongPass123"
}
```

### 2. Login

`POST /api/v1/auth/login`

```json
{
  "email": "alice@example.com",
  "password": "StrongPass123"
}
```

### 3. Upload Dataset

`POST /api/v1/datasets/upload`

Content type: `multipart/form-data`

Fields:
- `name`
- `description`
- `file`

Supported files:
- `.csv`
- `.json`

### 4. Query Dataset

`POST /api/v1/chat/{dataset_id}/message`

```json
{
  "message": "Which city has the highest revenue?",
  "conversation_id": null
}
```

### 5. List Conversations

`GET /api/v1/chat/conversations`

### 6. Analytics Overview

`GET /api/v1/analytics/overview`

### Standard Response Shape

```json
{
  "success": true,
  "data": {}
}
```

### Standard Error Shape

```json
{
  "success": false,
  "error": {
    "code": 500,
    "message": "Internal server error",
    "correlation_id": "..."
  }
}
```

## Socket.IO Events

Server events and handlers:
- `connect`
- `disconnect`
- `user_message`
- `bot_response`
- `typing_indicator`
- `error_event`

### Socket Payload Example

```json
{
  "dataset_id": "dataset-uuid",
  "message": "Summarize the cancellation reasons",
  "conversation_id": null
}
```

Client should connect with:

```json
{
  "token": "jwt-token"
}
```

## Setup

### Python Version

Use Python `3.11`, `3.12`, or `3.13` for this project. Python `3.14` is currently too new for parts of the dependency stack such as `pydantic-core` on Windows.

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Set at minimum:
- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `GOOGLE_API_KEY`

### 4. Start PostgreSQL

Create a PostgreSQL database named `smart_chatbot` or update `DATABASE_URL` accordingly. The default config uses the async `psycopg` SQLAlchemy driver:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/smart_chatbot
```

### 5. Start the API server

```bash
uvicorn app.main:app --reload
```

### 6. Optional index creation

Run the SQL in [scripts/create_indexes.sql](</d:/AI Projects/smart-chatbot-with-data-analytics/scripts/create_indexes.sql:1>) after tables are created.

## Docker Setup

The project includes a full Docker stack with:
- `api`: FastAPI application
- `postgres`: PostgreSQL 16
- `redis`: Redis 7
- `pgadmin`: pgAdmin 4 UI

### Default Container Ports

- API: `8000`
- PostgreSQL: `5432`
- Redis: `6379`
- pgAdmin: `5050`

### Default Service Credentials

- PostgreSQL database: `smart_chatbot`
- PostgreSQL user: `app`
- PostgreSQL password: `app`
- pgAdmin email: `admin@example.com`
- pgAdmin password: `admin123`

### Docker Environment Notes

When running through Docker Compose, these service endpoints are used automatically:

```env
DATABASE_URL=postgresql+psycopg://app:app@postgres:5432/smart_chatbot
REDIS_URL=redis://redis:6379/0
```

Only make sure your `.env` contains a valid `JWT_SECRET_KEY` and `GOOGLE_API_KEY`.

### Start The Full Stack

```bash
docker compose up --build
```

### Start In Background

```bash
docker compose up --build -d
```

### Stop The Stack

```bash
docker compose down
```

### Stop And Remove Volumes

```bash
docker compose down -v
```

### Access URLs

- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/v1/health`
- pgAdmin: `http://localhost:5050`

### Docker Startup Flow

1. Docker Compose starts PostgreSQL and Redis with health checks.
2. The API container waits for PostgreSQL using `scripts/wait_for_postgres.py`.
3. FastAPI starts through `scripts/start.sh`.
4. App startup creates tables and executes [scripts/create_indexes.sql](</d:/AI Projects/smart-chatbot-with-data-analytics/scripts/create_indexes.sql:1>).
5. The API becomes available on port `8000`.

## Performance Notes

- Async SQLAlchemy engine with connection pooling is enabled through environment config.
- Query caching uses a TTL cache for repeated prompts.
- Retrieval top-k, chunk sizes, and model settings are configurable through environment variables.
- Cached responses can return in under 2 seconds depending on deployment conditions.
- Embeddings are processed in a reusable vector service and stored per dataset for fast lookup.

## Error Handling and Observability

- Centralized FastAPI exception handlers
- Structured JSON errors
- Logging configured through a single application logger
- Correlation IDs generated for unhandled errors
- Retry behavior on Gemini client access

## Testing

Run tests with:

```bash
pytest
```

Included test coverage:
- Auth service unit tests
- Chat service unit tests with mocked LLM behavior
- API health endpoint test

## Postman

Import [postman_collection.json](</d:/AI Projects/smart-chatbot-with-data-analytics/postman_collection.json>) into Postman and set:
- `baseUrl`
- `token`
- `datasetId`

## Key Implementation Files

- [app/main.py](</d:/AI Projects/smart-chatbot-with-data-analytics/app/main.py:1>)
- [app/dependencies.py](</d:/AI Projects/smart-chatbot-with-data-analytics/app/dependencies.py:1>)
- [app/services/chat_service.py](</d:/AI Projects/smart-chatbot-with-data-analytics/app/services/chat_service.py:1>)
- [app/services/dataset_service.py](</d:/AI Projects/smart-chatbot-with-data-analytics/app/services/dataset_service.py:1>)
- [app/services/vector_service.py](</d:/AI Projects/smart-chatbot-with-data-analytics/app/services/vector_service.py:1>)
- [app/sockets/server.py](</d:/AI Projects/smart-chatbot-with-data-analytics/app/sockets/server.py:1>)

## Notes

- This project intentionally avoids hardcoded business logic by pushing operational settings into environment variables.
- The current implementation uses local FAISS persistence. In production, mount persistent storage for the `storage/` directory.
- Redis is listed in configuration for future distributed caching or queue integration, though the current build does not require Celery.

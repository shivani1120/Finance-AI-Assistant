# Finance RAG Assistant

A portfolio backend for asking grounded questions about uploaded financial reports. **Phases 1–9 and Phase 11 are implemented:** the service skeleton, PDF ingestion, semantic retrieval, RAG chat, LangGraph orchestration, modular guardrails, JWT authentication with role checks, per-user query history, an evaluation harness, and request-level observability. **Phase 10 (test coverage) is deferred for now.**

## Current architecture (Phases 1–9 and 11)

```text
PDF ──> validation ──> extraction ──> chunking ──> embeddings ──> Chroma
                                                                 ▲
Question ──> input guardrails ──> query embedding ──> top-K retrieval
                                                     │
                                      document safety filter ──> context ──> LLM
                                                                              │
Client ──HTTP──> FastAPI API ──> LangGraph workflow <── output guardrails <───┘
                                                     └──> answer + sources
                    ├── original PDF in a persistent uploads volume
                    └── PostgreSQL (users, roles, password hashes, private query history)
```

The API exposes liveness, account registration and login, PDF upload, semantic search, RAG chat, and query history endpoints. The chat endpoint runs through a LangGraph workflow. Each chunk retains its document ID, filename, company, reporting year when supplied, document type, one-based page number, chunk ID, and owning user ID. PostgreSQL stores user accounts, roles, and account-scoped chat history.

## Tech stack

- Python 3.12, FastAPI, Uvicorn
- Pydantic Settings for environment configuration
- LangChain Community PDF loader and recursive text splitter
- LangChain embedding integrations for OpenAI and Ollama
- LangChain chat integrations for OpenAI, Anthropic, Ollama, and Groq
- LangGraph state graph for chat orchestration
- Chroma vector search with metadata filters
- PostgreSQL 16 with SQLAlchemy for user accounts, roles, and query history
- Chroma server for future local vector storage
- Docker Compose for local orchestration
- pytest and FastAPI TestClient for the basic health route test

## Start locally with Docker Compose

```bash
cp .env.example .env
openssl rand -hex 32
# Paste the generated value into JWT_SECRET_KEY in .env before proceeding.
docker compose up --build
```

The sample `.env` is for local development only. Configure `JWT_SECRET_KEY` as above, and set the optional bootstrap admin credentials before the first start if you need an administrator account. Change the database password before sharing the setup. Compose waits for PostgreSQL to become healthy and starts Chroma and Ollama before the API; Chroma and Ollama do not have container health checks in this setup. API docs are available at <http://localhost:8000/docs>. This local Compose setup serves plain HTTP for local development; put the API behind an HTTPS reverse proxy before exposing it to a network.

To stop the containers while retaining database/vector data:

```bash
docker compose down
```

To remove containers and their persisted local data:

```bash
docker compose down -v
```

## Health endpoint

```bash
curl http://localhost:8000/health
```

Expected response: `{"status":"ok"}`. This is an API liveness check; it does not yet check PostgreSQL or Chroma connectivity.

## Authentication and roles (Phase 7)

Set a private JWT signing key in `.env` before starting the API. Generate one with:

```bash
openssl rand -hex 32
```

Copy the result into `JWT_SECRET_KEY`. Do not commit `.env` or share the key. The API creates its initial `users` table on startup. For the first administrator, set both `BOOTSTRAP_ADMIN_EMAIL` and `BOOTSTRAP_ADMIN_PASSWORD` in `.env` before the first start; use a strong password of at least 12 characters. Remove those bootstrap values after the admin account has been created. Public registration can only create regular `user` accounts.

Register a user with `POST /auth/register`:

```bash
curl -X POST http://localhost:8000/auth/register -H 'Content-Type: application/json' -d '{"email":"analyst@example.com","password":"use-a-long-unique-password"}'
```

Get a bearer token at `POST /auth/token` using form data (`username` is the email and `password` is the password):

```bash
curl -X POST http://localhost:8000/auth/token -H 'Content-Type: application/x-www-form-urlencoded' -d 'username=analyst@example.com&password=use-a-long-unique-password'
```

Provide the returned token as `Authorization: Bearer <token>` to upload, search, and chat endpoints. Tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES` (30 by default). `/auth/me` returns the signed-in account. Admins can list users and change roles using `/admin/users` and `/admin/users/{user_id}/role`.

Passwords are sent in the registration or login request body. A POST request does not encrypt them: HTTPS/TLS encrypts the connection between the client and server, so use HTTPS outside local development. Passwords are stored as Argon2 hashes, not plaintext. The JWT is a different credential issued after login; its payload is encoded and readable, and this app puts only the user ID and token timestamps in it. The signature detects edits but does not hide the payload. Never put a password or other secret in a JWT.

Uploads are tagged with their owning user ID, and search/chat always filter by the authenticated account. Documents uploaded before Phase 7 lack ownership metadata and won’t appear in the new user-scoped searches; upload those PDFs again after signing in. The `users` table is initialized with SQLAlchemy `create_all` for this initial version; schema changes later should use database migrations. Rate limiting, email verification, password reset, refresh/revocation tokens, and audit logging are not included yet. Use HTTPS and a managed secret store outside local development.

## Upload a PDF

Set a valid `OPENAI_API_KEY` in `.env`; embeddings are sent to OpenAI, and the resulting vectors plus chunk metadata are stored in the local Chroma service. No key is included in the repository. The embedding provider and model are configured with `EMBEDDING_PROVIDER` and `EMBEDDING_MODEL`.

```bash
curl -X POST http://localhost:8000/documents/upload \\
  -F 'file=@./annual-report.pdf;type=application/pdf' \\
  -F 'company=Apple Inc.' \\
  -F 'reporting_year=2025' \\
  -F 'document_type=annual_report'
```

The endpoint accepts PDF files up to `MAX_UPLOAD_SIZE_MB` (25 MB by default). It checks the filename, media type, and PDF file signature. Company, year, and document type are supplied as upload metadata; they are not guessed from the PDF. PDFs with selectable text are supported. Scanned/image-only PDFs need OCR, which is not part of this phase.

Chunking uses 1,000 characters with 150 characters of overlap by default. The recursive splitter tries paragraph, line, sentence, and word boundaries in that order; overlap helps preserve facts that land across a chunk boundary. Both values are configurable. These are initial settings, not universally optimal values; later retrieval evaluation can guide tuning. Financial tables may still need a table-aware extraction path.

## Search uploaded documents

`POST /retrieval/search` embeds the question with the configured embedding model, asks Chroma for the nearest chunks, and returns those chunks with source metadata and distance scores. It does not generate an answer. Use optional metadata filters to limit which uploaded documents can match.

```bash
curl -X POST http://localhost:8000/retrieval/search \\
  -H 'Content-Type: application/json' \\
  -d '{"question":"What caused revenue to increase?","top_k":5,"filters":{"company":"Apple Inc.","reporting_year":2025,"document_type":"annual_report"}}'
```

`RETRIEVAL_TOP_K` controls the default number of chunks (5); `RETRIEVAL_MAX_TOP_K` caps a caller-supplied `top_k` (20). Chroma returns cosine distance, where lower means closer. The API also returns `similarity_score = 1 - distance` as an easier-to-read ranking score; it is not a probability or an answer-confidence measure.

## Ask a grounded question

Set `LLM_PROVIDER` to `openai` or `anthropic`, then set `LLM_MODEL` to a model enabled for that provider account. OpenAI chat uses `OPENAI_API_KEY`; Anthropic chat uses `ANTHROPIC_API_KEY`. Embeddings are still generated with the configured OpenAI embedding integration, so `OPENAI_API_KEY` is required for retrieval with either chat provider.

```bash
curl -X POST http://localhost:8000/chat \\
  -H 'Content-Type: application/json' \\
  -d '{"question":"What caused revenue to increase?","top_k":5,"filters":{"company":"Apple Inc.","reporting_year":2025,"document_type":"annual_report"}}'
```

The prompt asks the model to answer from retrieved passages, abstain when they do not contain enough evidence, distinguish document facts from interpretation, cite passages as `[S1]` and so on, and avoid personalized investment advice. The response includes the answer and a source list with document, page, and chunk identifiers. Input and output checks are described below. If retrieval returns no safe chunks, the API returns an abstention without calling the LLM.

## Query history (Phase 8)

Accepted chat questions and their answers are saved in PostgreSQL with source references and a timestamp. Each history endpoint scopes records by the authenticated user's account; an administrator sees their own history through these endpoints. Requests rejected by the input guardrails are not saved. Use `GET /history?limit=20&offset=0` to page through recent entries, `GET /history/{entry_id}` to fetch one, and `DELETE /history/{entry_id}` or `DELETE /history` to delete one or all of your entries. There is no automatic retention period yet, so users control deletion themselves. History can contain financial questions and answers; treat the database as sensitive data and secure its backups.

## LangGraph workflow

```text
START → input guardrails → query analysis → retrieval → document safety filter
                                                       ├── no safe chunks → abstention → END
                                                       └── safe chunks → context → generation → output guardrails
                                                                                           ├── accepted → END
                                                                                           └── rejected → safe response → END
```

The graph state carries the question, optional user ID and metadata filters, intent, retrieved chunks, context, answer, sources, and validation result. Query analysis uses simple deterministic rules to choose a response style (fact, cause, comparison, or risk summary); it keeps the original question for vector search. The graph has no checkpoint or conversation memory.

## Evaluation (Phase 9)

The evaluation harness reads a JSON Lines (`.jsonl`) dataset with one case per line. Each case contains a unique `case_id`, the question, the owning `user_id`, optional retrieval filters, manually judged `relevant_chunk_ids`, an `expected_answerable` flag, and (for answerable cases) a `reference_answer` when answer evaluation is requested. The user ID must own the benchmark documents so the normal account-scoped retrieval rules still apply.

Example answerable case:

```json
{"case_id":"revenue-2025","question":"What was revenue in 2025?","user_id":"12","filters":{"company":"Example Corp","reporting_year":2025},"relevant_chunk_ids":["document-uuid:3"],"expected_answerable":true,"reference_answer":"Revenue was $42 billion."}
```

Example unanswerable case:

```json
{"case_id":"missing-metric","question":"What was the company's market share?","user_id":"12","filters":{"company":"Example Corp"},"relevant_chunk_ids":[],"expected_answerable":false}
```

Run retrieval-only evaluation (it still uses the configured embedding provider):

```bash
python -m app.evaluation.run --dataset evaluation/my_cases.jsonl --output evaluation/reports/retrieval.json --top-k 5
```

Add `--answers` to run the RAG model for each case. This can incur embedding and chat model costs; every answerable case must have a `reference_answer`:

```bash
python -m app.evaluation.run --dataset evaluation/my_cases.jsonl --output evaluation/reports/answers.json --top-k 5 --answers
```

The report includes precision@K, recall@K, mean reciprocal rank, and nDCG@K. Answer runs also include answerability accuracy, token F1 against the reference, and citation ID/relevance checks. Token overlap and citation relevance are useful for comparing prompt or retrieval changes, but they do not establish that an answer is factually correct or that a citation semantically supports a claim. Review representative cases manually and keep the dataset/report files protected because they refer to user-owned financial documents.

## Request observability (Phase 11)

The API assigns each HTTP request a UUID request ID, returns it in `X-Request-ID`, and emits one structured JSON completion log with the request method, normalized route path when available, response status, duration in milliseconds, and exception type for unhandled errors. A caller-supplied `X-Request-ID` is reused only when it is a valid UUID; otherwise the API creates one. The request ID is also attached to application log records during request handling so related events can be correlated.

The completion log intentionally omits request and response bodies, query-string values, authorization headers, and user identifiers. This keeps passwords, bearer tokens, and financial questions out of these request logs. To follow API logs in local Compose, run `docker compose logs -f api`; the Docker command disables Uvicorn's duplicate access log so the structured request event is the access record. For example, `curl -i http://localhost:8000/health` shows the request ID response header.

This phase adds logs and correlation IDs, not distributed traces or a metrics backend. Logs may still contain application-level error details from other code paths; review those before forwarding logs to a third-party service.

## Guardrails (Phase 6)

Guardrail code is grouped under `app/guardrails/` by the data boundary it protects:

- `input/` rejects empty or oversized questions, known prompt override attempts, requests to expose sensitive personal data, personalized buy/sell/hold advice, and questions that do not appear related to financial documents. Rejected questions do not reach retrieval or the model.
- `documents/` scans retrieved passages for known instruction override or secret-exfiltration patterns and drops matching chunks before context construction. If no safe passages remain, chat abstains.
- `output/` checks that the answer is non-empty, citation IDs exist, financial or numeric claims have citations, numbers in claims occur in their cited passages, and the answer does not contain a recognized personalized recommendation.

These checks are deterministic heuristics, not a proof of safety or semantic entailment. Scope and pattern matching can miss paraphrases or reject valid questions. The numeric check may reject legitimate calculations or rounded values absent verbatim from a source. The document scan catches known patterns only. Keep provider credentials out of questions and uploaded files; this scanner is not a secret detection system.

## Run the basic tests

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

## Configuration

Copy `.env.example` to `.env`. Settings are read from environment variables and the optional `.env` file. Compose uses service DNS names (`postgres`, `chroma`) inside containers; when running the API directly on the host, use `localhost` and the published ports instead.

## Groq chat with local embeddings

The default configuration uses Groq for chat (`qwen/qwen3.8-27b`) and Ollama's `nomic-embed-text` model for embeddings. Set `GROQ_API_KEY` in `.env`; the chat model runs in Groq Cloud, while embeddings run locally through the Ollama service. Groq's free tier has model-specific request and token limits that can change; check the current [Groq rate limits](https://console.groq.com/docs/rate-limits).

```bash
docker compose up --build -d
docker compose exec ollama ollama pull nomic-embed-text
```

The embedding model download uses local disk and memory. Groq receives chat prompts and the retrieved document passages used as context. Existing Chroma collections created with a different embedding model should be re-indexed before using `nomic-embed-text` for retrieval.

## Planned phases

1. Project skeleton, service configuration, health endpoint, and local infrastructure
2. PDF ingestion and chunking
3. Semantic retrieval and metadata filters
4. Basic grounded RAG endpoint
5. LangGraph orchestration
6. Modular guardrails
7. JWT authentication and RBAC
8. Query history
9. Retrieval and answer evaluation (current)
10. Unit, integration, and API test coverage (deferred for now)
11. Request-level observability (current)

Later phases will expand this README with ingestion/retrieval diagrams, endpoints, security behavior, evaluation, design decisions, limitations, and SDE2 interview explanations.

# Finance AI Assistant

A portfolio project that lets you upload a financial report and ask questions about it. The app searches the report for relevant passages and uses an AI model to write an answer with sources.

This repository contains the **backend API**. It does not include a website or mobile app. You can try the API in its built-in interactive page at `/docs`.

## What it can do

- Create accounts and sign in with a password.
- Upload text-based PDF reports.
- Find relevant report passages using semantic search.
- Answer questions using retrieved passages and show the sources.
- Keep each user's documents and chat history separate.
- Apply basic checks to questions, documents, and answers.

## How it works

1. Upload a PDF and add details such as company and year.
2. The API extracts the text and splits it into smaller pieces.
3. FastEmbed turns each piece into a vector, which Chroma stores for search.
4. Ask a question. Chroma finds related passages and the chat model uses them to write an answer.
5. The API returns the answer and its sources.

PostgreSQL stores accounts and chat history. Docker Compose starts the API, PostgreSQL, and Chroma together.

## Run it on your computer

You need Docker Desktop and a Groq API key. The default embedding model runs locally through FastEmbed, so you do not need an OpenAI key for embeddings.

1. Copy the example settings file:

   ```bash
   cp .env.example .env
   ```

2. Generate a private key for signing login tokens:

   ```bash
   openssl rand -hex 32
   ```

   Copy the result into `JWT_SECRET_KEY` in `.env`. Add your Groq key to `GROQ_API_KEY` in that same file. Keep `.env` private; it is excluded from Git.

3. Build and start the services:

   ```bash
   docker compose up --build
   ```

   FastEmbed downloads its model the first time you upload a document or search. This can make that first request take longer.

4. Open [http://localhost:8000/docs](http://localhost:8000/docs) to try the API. To check whether the API process is running, open [http://localhost:8000/health](http://localhost:8000/health).

Press `Control+C` to stop the services. Run `docker compose down` to stop and remove their containers while keeping saved data. **`docker compose down -v` also deletes the local database, Chroma vectors, and uploaded PDFs.**

## Try the API

In `/docs`:

1. Use `POST /auth/register` to create an account.
2. Click **Authorize** and sign in with that email and password.
3. Use `POST /documents/upload` to upload a PDF and add its company and year.
4. Use `POST /chat` to ask a question about your report, or `POST /retrieval/search` to see matching passages without an AI-generated answer.

Protected endpoints require you to sign in. Each account can search only its own uploaded documents.

## Main endpoints

| Endpoint | What it does |
| --- | --- |
| `GET /health` | Checks that the API process is running. |
| `POST /auth/register` | Creates an account. |
| `POST /auth/token` | Signs in and returns an access token. |
| `GET /auth/me` | Shows the signed-in account. |
| `POST /documents/upload` | Uploads and indexes a PDF. |
| `POST /retrieval/search` | Finds relevant passages in your documents. |
| `POST /chat` | Answers a question using your documents. |
| `/history` | Lists or deletes your saved chat history. |
| `/admin/users` | Lets an administrator view accounts and change roles. |

## Models and settings

- **Embeddings:** FastEmbed with `BAAI/bge-small-en-v1.5` by default. It runs locally and needs no embedding API key.
- **Chat:** Groq by default. Set `GROQ_API_KEY` in `.env`.
- **Other embedding options:** Jina and OpenAI are available. Their APIs receive the text being embedded and may have usage limits or charges. Configure their keys in the server environment; do not put secrets in GitHub.

Settings such as chunk size, upload size, and model provider are in `.env.example`. Make local changes in `.env`, which is ignored by Git.

## Current limitations

- Only PDFs with selectable text are supported. Scanned PDFs need OCR, which is not included.
- Complex financial tables may not extract cleanly.
- The app does not yet include email verification, password reset, or request rate limiting.
- Use public or sample reports for a portfolio demo. Do not expose the API publicly with real financial documents until access limits, HTTPS, data retention, and backups are configured.
- If you change the embedding model, use a new Chroma collection and upload the PDFs again. Vectors from different models cannot be mixed.
- Automated test coverage is limited.

## Tech used

Python, FastAPI, LangChain, FastEmbed, Groq, Chroma, PostgreSQL, SQLAlchemy, LangGraph, and Docker Compose.

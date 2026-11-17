# Finance AI Assistant

A portfolio project that lets you upload a financial report and ask questions about it. The app searches the report for relevant passages and uses an AI model to write an answer with sources.

This repository includes a web app and a backend API. Sign in, upload financial reports, ask questions, and inspect the report passages used to answer them. The API's interactive page is still available at `/docs`.

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

You need Docker Desktop and a Groq API key. The default embedding model runs locally through FastEmbed, so you do not need an OpenAI key for embeddings. Docker builds the website and API together.

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

4. Open [http://localhost:8000](http://localhost:8000) to use the website. Open [http://localhost:8000/docs](http://localhost:8000/docs) to try the API directly, or [http://localhost:8000/health](http://localhost:8000/health) to check the API.

Press `Control+C` to stop the services. Run `docker compose down` to stop and remove their containers while keeping saved data. **`docker compose down -v` also deletes the local database, Chroma vectors, and uploaded PDFs.**

## Use the website

1. Open the site at `http://localhost:8000`.
2. Register an account and sign in.
3. Upload a text-based PDF report and add its company and year, or paste a public PDF link from `www.ril.com`. For Reliance links, the app fills in the company and detects the year from the filename.
4. Ask a question. The answer can show matching report pages and passages when available.
5. Use **Recent questions** to reopen a previous saved question and answer.

The site talks to the same FastAPI backend and uses its existing authentication and data. The backend stores individual question-and-answer records, not multi-turn conversation threads.

## Try the API

In `/docs`:

1. Use `POST /auth/register` to create an account.
2. Click **Authorize** and sign in with that email and password.
3. Use `POST /documents/upload` to upload a PDF and add its company and year.
   Or use `POST /documents/import-url` with a public Reliance PDF URL. Company, year, and report type are optional; defaults are supplied when they can be inferred.
4. Use `POST /chat` to ask a question about your report, or `POST /retrieval/search` to see matching passages without an AI-generated answer.

Protected endpoints require you to sign in. Each account can search only its own uploaded documents.

## Main endpoints

| Endpoint | What it does |
| --- | --- |
| `GET /health` | Checks the API. Returns a status. |
| `POST /auth/register` | Creates an account from email and password. Returns `id`, `email`, and `role`. |
| `POST /auth/token` | Signs in using form fields `username` (email) and `password`. Returns `access_token`, `token_type`, and `expires_in`. |
| `GET /auth/me` | Returns the signed-in user's `id`, `email`, and `role`. |
| `POST /documents/upload` | Uploads a PDF plus `company`, `document_type`, and optional `reporting_year`. Returns document details and `chunk_count`. |
| `POST /documents/import-url` | Downloads and indexes a public HTTPS PDF from `www.ril.com`. Only `url` is required; company, year, and report type can be provided to override the inferred defaults. |
| `POST /retrieval/search` | Accepts `question`, optional filters and `top_k`. Returns matching passage records including `content`, filename, page, and ranking scores. |
| `POST /chat` | Accepts the same question format. Returns `answer` and source references (`filename`, page, and chunk IDs). |
| `GET /history` | Returns saved question-and-answer items with timestamps and sources. |
| `/admin/users` | Lets an administrator view accounts and change roles. |

Requests to protected endpoints use `Authorization: Bearer <access_token>`. Chat responses do not include passage excerpts; the UI looks them up through `/retrieval/search` when possible. The backend does not currently provide conversation IDs, ticket escalation, or feedback endpoints, so those are not represented as working features in this UI.

## Models and settings

- **Embeddings:** FastEmbed with `BAAI/bge-small-en-v1.5` by default. It runs locally and needs no embedding API key.
- **Chat:** Groq by default. Set `GROQ_API_KEY` in `.env`.
- **Other embedding options:** Jina and OpenAI are available. Their APIs receive the text being embedded and may have usage limits or charges. Configure their keys in the server environment; do not put secrets in GitHub.

Settings such as chunk size, upload size, and model provider are in `.env.example`. Make local changes in `.env`, which is ignored by Git.

## Current limitations

- Only PDFs with selectable text are supported. Scanned PDFs need OCR, which is not included.
- Complex financial tables may not extract cleanly.
- The app does not yet include email verification, password reset, or request rate limiting.
- Registration checks the email format and domain's mail DNS records, but it does not verify mailbox ownership with a confirmation email.
- Use public or sample reports for a portfolio demo. Do not expose the API publicly with real financial documents until access limits, HTTPS, data retention, and backups are configured.
- If you change the embedding model, use a new Chroma collection and upload the PDFs again. Vectors from different models cannot be mixed.
- Automated test coverage is limited.

## Frontend development

The React, TypeScript, and Tailwind source is in `frontend/`. `frontend/.env.example` shows the optional API origin setting. You need Node.js 22 or newer to run the frontend development server outside Docker.

```bash
cd frontend
npm install
npm run dev
```

The Vite server runs at `http://localhost:5173` and forwards API requests to FastAPI at `http://localhost:8000`. Start the backend separately with `docker compose up` from the repository root. To run frontend checks and create production assets, use `npm test` and `npm run build` from `frontend/`; Docker runs these checks when building the production image.

## Tech used

React, TypeScript, Tailwind CSS, Vite, Python, FastAPI, LangChain, FastEmbed, Groq, Chroma, PostgreSQL, SQLAlchemy, LangGraph, and Docker Compose.

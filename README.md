# Email agent

Reads new mail every day, writes a prioritized summary (urgent, needs a reply, informational) and prepares reply drafts. A human reviews and approves every draft in a dashboard. The agent never sends email.

Status: work in progress.

- Done: settings, domain models, persistence (PostgreSQL, Alembic migrations, repositories), provider interfaces with demo and fake implementations, services, the factory, the REST API, the daily scheduler, the dashboard, the Gmail provider and the LangChain model provider (through OpenRouter).
- Next: a complete Docker Compose setup.

## Architecture

See [docs/architecture.md](docs/architecture.md).

## Stack

Python 3.12, FastAPI, Pydantic, LangChain, SQLAlchemy 2, Alembic, APScheduler, PostgreSQL, React.

## Run locally

Requires Docker and [uv](https://docs.astral.sh/uv/).

```bash
cp .env.example .env   # then fill in the values
docker compose up -d db
cd backend && uv sync
uv run alembic upgrade head   # create the database tables
uv run fastapi dev            # API at http://127.0.0.1:8000, docs at /docs
```

Dashboard (Node 24 and npm), in a second terminal:

```bash
cd frontend && npm install
npm run dev                   # http://localhost:5173, proxies /api to the API on port 8000
```

To run everything as one process, the way it is served in production, build the dashboard and let the API serve it:

```bash
cd frontend && npm run build
cd ../backend && uv run fastapi run   # dashboard and API at http://127.0.0.1:8000
```

Frontend checks: `npm run lint`, `npm run build` (type-checks the app and its tests) and `npm test`.

## Demo mode

Runs on fictitious emails and needs no mailbox credentials (`DEMO_MODE=true`). Open `/docs` and call `POST /api/demo/run` to load and analyse the demo emails. They are dated relative to today, so the demo always looks current. `POST /api/demo/reset` wipes the data and loads them again.

## Real Gmail mode

Use a dedicated test account, never your own mailbox.

1. In Google Cloud Console create a project, enable the Gmail API and set up the OAuth consent screen as External. Add the test account as a test user.
2. Create an OAuth client of type Desktop app and put its client id and secret in `.env` (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`).
3. Run `uv run python -m app.cli authorize-gmail` from `backend/`, sign in, and paste the printed `GOOGLE_REFRESH_TOKEN=...` line into `.env`.
4. Set `DEMO_MODE=false`. Keep `LLM_PROVIDER=fake` to try the mailbox without a real model, or connect one (next section).
5. Run `uv run python -m app.cli run-pipeline` to fetch and analyse the mail now. Otherwise the daily run does it.

The app asks for `gmail.readonly` and `gmail.compose`. Approving a draft creates it in the Gmail account and never sends it. While the Google Cloud app is in Testing, the refresh token expires after 7 days and the step 3 command has to be repeated. Publishing the app (In production, unverified, only for your own account) avoids that.

## Real model

The model is reached through [OpenRouter](https://openrouter.ai), which gives access to many vendors with one key. In `.env` set:

```
LLM_PROVIDER=openrouter
LLM_MODEL=anthropic/claude-haiku-5.5
OPENROUTER_API_KEY=<a key from https://openrouter.ai/keys>
```

Any OpenRouter model that supports structured outputs works as `LLM_MODEL`. It is only used outside demo mode. The model has no tools: it answers with a structured analysis that is validated before anything is stored, and the email is handed to it as untrusted data. Each email goes to OpenRouter and the vendor behind the model, so use a test mailbox.

## Security

- No credentials in the repository. Configuration is read from environment variables only.
- Gmail access uses the minimum OAuth scopes. The mail provider has no send operation.
- Secrets are scanned with gitleaks on every commit and in CI.

## License

MIT

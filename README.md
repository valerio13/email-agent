# Email agent

Reads new mail every day, writes a prioritized summary (urgent, needs a reply, informational) and prepares reply drafts. A human reviews and approves every draft in a dashboard. The agent never sends email.

Status: work in progress.

- Done: settings, domain models, persistence (PostgreSQL, Alembic migrations, repositories), provider interfaces with demo and fake implementations, services, the factory and the REST API.
- Next: scheduler, dashboard, then the Gmail and LangChain providers.

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

## Demo mode

Runs on fictitious emails and needs no mailbox credentials (`DEMO_MODE=true`). Open `/docs` and call `POST /api/demo/run` to load and analyse the demo emails.

## Security

- No credentials in the repository. Configuration is read from environment variables only.
- Gmail access uses the minimum OAuth scopes. The mail provider has no send operation.
- Secrets are scanned with gitleaks on every commit and in CI.

## License

MIT

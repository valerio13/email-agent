# Email agent

Reads new mail every day, writes a prioritized summary (urgent, needs a reply, informational) and prepares reply drafts. A human reviews and approves every draft in a dashboard. The agent never sends email.

Status: work in progress.

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
```

## Demo mode

Runs on fictitious emails and needs no mailbox credentials (`DEMO_MODE=true`).

## Security

- No credentials in the repository. Configuration is read from environment variables only.
- Gmail access uses the minimum OAuth scopes. The mail provider has no send operation.
- Secrets are scanned with gitleaks on every commit and in CI.

## License

MIT

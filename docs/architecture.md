# Architecture

## Flow

```
Gmail / demo data -> Ingest -> Analyzer -> LLM provider
                                  |
                              PostgreSQL <-> API <-> Dashboard <-> reviewer
                                              |
                                        Gmail drafts (never sent)
```

1. A scheduler runs once a day and fetches new mail through a `MailProvider`.
2. The analyzer asks an `LLMProvider` for structured output (category, priority, summary, needs reply, draft) validated with Pydantic.
3. Results are stored in PostgreSQL.
4. The reviewer opens the dashboard, edits a draft and approves or discards it.
5. On approval the API creates the draft in the mailbox. Nothing is ever sent.

## Backend layers

Each layer depends only on the one below it.

| Layer | Folder | Responsibility |
|---|---|---|
| Entry points | `app/scheduler.py`, `app/api/` | Scheduled run and REST API |
| Services | `app/services/` | Ingest, analysis, daily digest, drafts |
| Ports and adapters | `app/providers/mail/`, `app/providers/llm/`, `app/db/` | Mail, LLM and persistence behind interfaces |
| Cross-cutting | `app/domain/`, `app/core/` | Pydantic models, enums, settings from environment |

## Design rules

1. `MailProvider` has no send operation, and a test guarantees it.
2. The LLM provider is swappable and implemented with LangChain (`providers/llm/langchain_provider.py`). Vendor and model come from `LLM_PROVIDER` and `LLM_MODEL`. A fake provider is used in tests and demo mode.
3. Dependencies are injected through constructors. A single factory reads the settings and builds the services, so services never know which vendor is behind `LLMProvider`.
4. Email content is untrusted input. The LLM has no tools and its output is validated before it is stored.
5. Configuration comes only from environment variables.

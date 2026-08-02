# Refactor architecture and operating contract

This repository remains a modular monolith: skills keep their domain-specific
logic, while shared runtime concerns move into small, importable modules. The
goal is to improve correctness and operability without forcing a broad rewrite
of every skill at once.

## Boundaries

```text
CLI / dashboard / scheduler
            |
            v
   pipeline orchestration
            |
            +--> trading_core.contracts
            +--> trading_core.config
            +--> trading_core.clock
            +--> trading_core.jobs
            +--> trading_core.sqlite
            |
            +--> skill adapters and domain services
                         |
                         +--> market data providers
                         +--> paper-trade simulator
                         +--> signal ledger
```

`src/trading_core` owns stable cross-cutting contracts. It must not import
dashboard code or a specific skill. Skills may depend on the core contracts,
but the core must remain usable from a CLI, a web request, a scheduled job, or
a test process.

## Execution modes

All automated execution should resolve to one explicit mode:

- `dry_run`: calculate and record decisions; do not create paper or live orders.
- `paper`: create simulated trades only.
- `live`: currently rejected by the safety gate. Enabling live trading requires
  a separate review of credentials, approvals, and kill-switch behavior.

Legacy boolean configuration is still accepted for compatibility, but new
callers should use `execution_mode`. A configuration must never silently turn a
missing or malformed value into live execution.

## Durable job evidence

Long-running jobs write lifecycle rows through `trading_core.jobs.JobRunStore`:

```text
queued/running -> success
                  \-> failed
```

Each run has a `run_id`, timestamps in UTC, an execution mode, and a compact
error/result payload. The dashboard exposes the latest row at
`/api/jobs/latest?job_name=<name>`. This is intentionally separate from health:
health means the process responds; job status shows whether the scheduled work
actually ran and completed.

## SQLite rules

New SQLite-backed components should use `trading_core.sqlite.connect_sqlite`
and `apply_migrations`. This gives every database the same WAL, foreign-key,
busy-timeout, row-factory, and migration bookkeeping behavior. Existing
databases remain compatible; migrations are additive and must be idempotent.

## Migration sequence

1. Keep the legacy skill interface and add an adapter around it.
2. Add a contract test for the adapter before changing callers.
3. Move one caller at a time to the shared service or provider.
4. Keep compatibility wrappers until all callers and tests use the canonical
   implementation.
5. Delete the wrapper only after a repository-wide import search and a full
   targeted test run.

The Yahoo Finance client migration follows this sequence. FMP clients should
follow the same pattern, but each skill's endpoint behavior and fallback policy
must be preserved by contract tests before deduplication.

## Verification commands

```powershell
uv sync --extra dev
uv run pytest tests/core tests/dashboard
uv run pytest scripts/tests/test_daily_signal_pipeline.py scripts/tests/test_dashboard_live_api.py
uv run ruff check scripts dashboard src tests
python scripts/validate_skills_index.py --strict-workflows --strict-metadata
```

The default test paths intentionally exclude known pre-existing suites that
require optional dependencies or contain unrelated drift. Run those suites
explicitly when working on them; exclusion is not a claim that they are green.
The CI smoke run includes the Gemini/local-only improvement-loop contract,
the VCP FMP integration flow, and the previously Windows-sensitive breadth,
downtrend, breakout, IBD, and parabolic skill suites. These suites now use
explicit UTF-8 I/O, deterministic environment isolation, and current behavior
contracts.

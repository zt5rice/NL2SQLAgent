# Resume Notes

Updated English bullets that are fully backed by this repository's code and
benchmarks. Keep every number tied to a script or measured run before publishing.

## Project: Enterprise NL2SQL Data Analytics Agent

```
Enterprise NL2SQL Data Analytics Agent | 2026
- Built an LLM-powered NL2SQL agent (FastAPI + LangChain) that turns natural-
  language questions into read-only SQL behind a defense-in-depth guard,
  streaming answers and auto-generated ECharts to a React dashboard over SSE.
- Engineered a provider-agnostic LLM layer (OpenCode Go / deepseek-v4-flash)
  and a deterministic ~1.03M-row indexed sample warehouse, keeping GROUP BY /
  JOIN queries under 250 ms and cutting end-to-end query latency from ~25s to
  ~7s by switching models.
- Designed a production-grade chat pipeline with sliding-window session
  memory, SSE event streaming (thinking/text/sql/data/chart/done), persisted
  chart payloads, and markdown normalization that keeps live and stored
  answers byte-identical.
- Shipped with 81 backend + 51 frontend tests and real-key end-to-end
  verification scripts, enforcing a one-PR-per-ticket workflow across 50+
  tracked issues.
```

## Evidence map (repo -> claim)

- 1.03M-row warehouse: `backend/app/db/connection.py` (`build_sales_seed`,
  `EXPECTED_SALES_ROWS = 1,028,160`) + indexes.
- Sub-250ms aggregations: README "Performance" section (measured on the seeded
  database).
- Read-only guard: `backend/app/core/agent.py` (`assert_read_only`).
- Streaming pipeline: `backend/app/api/chat.py` (SSE events) + frontend SSE
  client (`frontend/src/services/api.ts`).
- Test counts: `cd backend && pytest` (81), `cd frontend && npm test` (51).

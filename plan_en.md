<div align="center">
  <strong>English</strong> · <a href="plan_cn.md">中文</a>
</div>

# Implementation Plan for the NL2SQLAgent Intelligent Data Analysis System

## Summary

Build a complete intelligent data analysis system: a backend of FastAPI + LangChain SQLDatabaseToolkit Agent + Bailian Qwen3-max (ChatTongyi) that runs read-only queries against a built-in SQLite sample database and streams responses over SSE; a frontend of React 18 + Vite + TypeScript + Tailwind CSS + Zustand + ECharts with a dark three-pane layout (left: session management, middle: Q&A, right: visualization). Runs locally as a single user with no login/authentication.

## Implementation Changes

**Repository structure**
- Restructure the existing root-level Python scaffold into separate frontend/backend directories: `backend/` (FastAPI app + `requirements.txt` + `.env.example`) and `frontend/` (Vite app); remove the root-level `pyproject.toml` and `src/` placeholder package.

**Backend (FastAPI + LangChain)**
- Config module: `.env` manages `LLM_API_KEY`, the model name (default `deepseek-v4-flash`), and CORS origins; the data directory is auto-initialized on startup.
- LLM module: provider-pluggable (default: OpenCode Go OpenAI-compatible endpoint via `ChatOpenAI` with `deepseek-v4-flash`; `ChatTongyi` kept as a legacy fallback); non-streaming calls to obtain complete `tool_calls`, producing SSE events across agent iterations.
- Agent module: reuse the `SQLDatabaseToolkit` (list_tables / schema / query_checker / query) agentic loop; the system prompt explicitly forbids write statements (INSERT/UPDATE/DELETE/DROP); query results are limited to top 10 by default; tool result parsing uses `ast.literal_eval` to avoid the security risks of `eval`.
- Memory module: loads the last 10 rounds (20 messages) of history per session from the messages table, converts them to LangChain message format, with an in-memory cache.
- Session storage: a single SQLite file `backend/data/app.db` containing both business tables (`sales`, `employees` with Chinese sample data) and metadata tables (`chat_sessions`, `chat_messages`).
- API routes: `/api/sessions` CRUD and message query, `/api/chat` SSE chat, `/api/database/schema|tables`, `/health`.

**Frontend (React + Tailwind)**
- Layout: `ChatSidebar` (session list / create / delete / rename, auto-titled from the first question), `ChatArea` (message stream, SQL display, stop generation, auto session creation), `ChartPanel` (chart/table view toggle, bar/line/pie switching, SQL display, backend connection status).
- State & communication: a zustand store manages sessions/messages/chart state; `api.ts` parses SSE with fetch + ReadableStream; `useSession` / `useChat` hooks encapsulate session operations and streaming chat.
- Charts: ECharts renders `{type, title, data:[{name,value}], xField, yField}` with a dark theme.

## Interfaces & Data Contracts

- `POST /api/sessions` (create), `GET /api/sessions` (list), `GET/PUT/DELETE /api/sessions/{id}`, `GET /api/sessions/{id}/messages`.
- `POST /api/chat`: request body `{session_id, message}`, response `text/event-stream`.
- SSE events: `thinking` (tool call progress), `text` (answer text), `sql` (executed SQL), `data` (`{columns, rows, raw}`), `chart` (chart config), `error`, `done`.
- Chart heuristic: GROUP BY with ≤6 rows → pie, otherwise bar; ORDER BY + LIMIT → bar; default bar; the frontend can switch between bar/line/pie and the chart/table views.

## Test Plan

- Backend: session CRUD and message persistence tests; memory window trimming and cache tests; SSE event flow integration tests (mock LLM returning fixed SQL, verify the thinking → sql → data → chart → done sequence); invalid SQL, tool error, and empty-result paths; read-only constraint verification (no write tools in the prompt/toolset).
- Frontend: SSE client event parsing; chart type switching and chart/table view toggling; session create/switch/delete component interactions.
- End-to-end: with a real API key, run `test_qwen3` (connectivity), `test_nl2sql` (NL2SQL correctness), and `test_e2e` (full pipeline); acceptance scenario: "monthly sales totals → chart rendered on the right panel".

## Assumptions & Defaults

- Feature scope stays at the current baseline with no additional features (no writes, no file uploads, no multi-user).
- Local development only: `uvicorn app.main:app --reload --port 8000` + `npm run dev` (5173); no Docker.
- Business data and session metadata share `app.db`; memory window of 10 rounds, result limit of 10, model `deepseek-v4-flash` — all configurable.
- Chinese UI, API prefix `/api`, CORS restricted to localhost:5173.

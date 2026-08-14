<div align="center">
  <a href="plan_en.md">English</a> · <strong>中文</strong>
</div>

# NL2SQLAgent 智能数据分析系统实现规划

## 概述

构建一个完整的智能数据分析系统：后端 FastAPI + LangChain SQLDatabaseToolkit Agent + 百炼 Qwen3-max（ChatTongyi），只读查询内置 SQLite 示例库，SSE 流式返回；前端 React 18 + Vite + TypeScript + Tailwind CSS + Zustand + ECharts，采用左侧会话管理、中间问答、右侧可视化的暗色三栏布局。单用户本地运行，不做登录认证。

## 实现变更

**仓库结构**
- 将现有根级 Python 脚手架调整为前后端目录布局：`backend/`（FastAPI 应用 + `requirements.txt` + `.env.example`）与 `frontend/`（Vite 应用），移除根级 `pyproject.toml` 与 `src/` 占位包。

**后端（FastAPI + LangChain）**
- 配置模块：`.env` 管理 `LLM_API_KEY`、模型名（默认 `deepseek-v4-flash`）、CORS 来源；启动时自动初始化数据目录。
- LLM 模块：供应商可插拔（默认 OpenCode Go 的 OpenAI 兼容端点，经 `ChatOpenAI` 接入 `deepseek-v4-flash`；`ChatTongyi` 作为旧方案保留），非流式调用获取完整 `tool_calls`，按 Agent 迭代产出 SSE 事件。
- Agent 模块：复用 `SQLDatabaseToolkit`（list_tables / schema / query_checker / query）的 agentic 循环，系统提示词明确禁止 INSERT/UPDATE/DELETE/DROP 等写操作，查询结果默认限制 top 10；工具执行结果解析使用 `ast.literal_eval`，避免 `eval` 的安全隐患。
- 记忆模块：按会话 ID 从消息表加载最近 10 轮（20 条消息）历史，转换为 LangChain 消息格式，带内存缓存。
- 会话存储：单 SQLite 文件 `backend/data/app.db`，同时包含业务表（`sales`、`employees` 中文示例数据）与元数据表（`chat_sessions`、`chat_messages`）。
- API 路由：`/api/sessions` CRUD 与消息查询、`/api/chat` SSE 聊天、`/api/database/schema|tables`、`/health`。

**前端（React + Tailwind）**
- 布局：`ChatSidebar`（会话列表/新建/删除/重命名，自动用首条提问命名）、`ChatArea`（消息流、SQL 展示、停止生成、自动创建会话）、`ChartPanel`（图表/表格视图切换、柱状/折线/饼图切换、SQL 展示、后端连接状态）。
- 状态与通信：zustand store 管理会话/消息/图表状态；`api.ts` 用 fetch + ReadableStream 解析 SSE；`useSession` / `useChat` hooks 封装会话操作与流式聊天。
- 图表：ECharts 渲染 `{type, title, data:[{name,value}], xField, yField}`，暗色主题。

## 接口与数据契约

- `POST /api/sessions`（创建）、`GET /api/sessions`（列表）、`GET/PUT/DELETE /api/sessions/{id}`、`GET /api/sessions/{id}/messages`。
- `POST /api/chat`：请求体 `{session_id, message}`，响应 `text/event-stream`。
- SSE 事件：`thinking`（工具调用过程）、`text`（回答文本）、`sql`（执行的 SQL）、`data`（`{columns, rows, raw}`）、`chart`（图表配置）、`error`、`done`。
- 图表启发式：GROUP BY 且 ≤6 行→饼图，否则柱状；ORDER BY + LIMIT→柱状；默认柱状；前端可切换柱状/折线/饼图及表格视图。

## 测试计划

- 后端：会话 CRUD 与消息持久化测试；记忆窗口裁剪与缓存测试；SSE 事件流集成测试（mock LLM 返回固定 SQL，验证 thinking→sql→data→chart→done 序列）；非法 SQL、工具错误、空结果路径；只读约束验证（提示词/工具集不含写工具）。
- 前端：SSE 客户端事件解析；图表类型切换与图表/表格视图切换；会话创建/切换/删除组件交互。
- 端到端：配置真实 API Key 后执行 `test_qwen3`（连通性）、`test_nl2sql`（NL2SQL 正确性）、`test_e2e`（完整链路），验收"按月统计销售额→右侧渲染图表"场景。

## 假设与默认值

- 功能范围以当前基线为准，不额外增加新功能（无写操作、无文件上传、无多用户）。
- 本地开发运行：`uvicorn app.main:app --reload --port 8000` + `npm run dev`（5173），不做 Docker。
- 业务数据与会话元数据共用 `app.db`；内存窗口 10 轮、结果上限 10 条、模型 `deepseek-v4-flash`，均可通过配置调整。
- 界面为中文，API 前缀 `/api`，CORS 仅允许 localhost:5173。

# Development Workflow Rule (AGENTS.md)

This file lets Codex manage the development workflow with everyday spoken language: say "start the login system feature" and Codex automatically updates the Linear task status, recommends a branch, and suggests a commit message.

## Project configuration (edit this block to switch projects)

project:
    name: "NL2SQLAgent Intelligent Data Analysis System"
    team: "ZHA"   # Linear team key; when the MCP needs the team ID, use <YOUR_LINEAR_TEAM_ID>
    repo: "git@github.com:zt5rice/NL2SQLAgent.git"

## How it works

When the user mentions a project task in everyday language, follow the mapping below. All Linear reads/writes go through the Linear MCP tools. Before any write operation (changing status, creating an issue), state in one sentence what you are about to do, then do it directly — app-level permission prompts are handled by the system; a second confirmation from the user is not needed.

Note: Chinese trigger phrases are also recognized (e.g. 开始做 <功能>, 完成了, 查看进度).

### Spoken commands → actions

| User says | Codex does |
| --- | --- |
| start <feature> / start working on <feature> / do <feature> / start <ID> | If the user gives an issue ID (e.g. ZHA-12), locate it directly by ID, no fuzzy matching. Otherwise: 1) search issues in the configured team + project by title keywords; 2) unique match → set status to In Progress; multiple candidates → show 2-3 and let the user pick; none → ask whether to create one; 3) recommend a branch `feat/<issue-id>-<kebab-slug>` (e.g. `feat/ZHA-12-login-page`) and give the `git checkout -b` command |
| finish <feature> / done <feature> / complete <feature> | 1) find the issue; 2) run project validation first (backend `pytest`, frontend `npm run build`; only proceed if green); 3) set status to Done when passed; 4) suggest a conventional commit message (e.g. `feat: complete login system (#ZHA-12)`) plus push/PR hints |
| pause <feature> / put <feature> on hold | set status back to Todo (or Backlog); note the branch is kept and can be restored with `git checkout` |
| fix bug / fix <issue> / something is broken | prefer issues whose title contains bug/fix; set status to In Progress; branch `fix/<issue-id>-<kebab-slug>` |
| show progress / list tasks / todo / status / where are we | list tasks with completion (done/total + percentage) and summarize by milestone and status |
| start Phase N / next phase | list unfinished issues of that milestone and work through them in order |
| cancel <ID> / cancel task <xxx> | set the issue status to Canceled (not delete) |
| create project <name> | create a new Linear Project under the configured team and split it into issues from the plan file (e.g. plan_en.md / phased_plan_en.md) |
| new task <xxx> / add task <xxx> | create a Linear Issue (assigned to the current project; attach the milestone matching the feature's phase) |
| commit code / push / commit | check `git status` and `git diff` first, generate a conventional commit message, then `git add` + `git commit` + `git push` |
| create branch / switch branch | create and switch to a feature branch `feat/<issue-id>-<kebab-slug>` based on the current in-progress task (confirm the working tree is clean first) |
| sync to Linear | read the plan file (plan_en.md / phased_plan_en.md) and batch-create/reconcile issues, attaching the matching milestones |
| delete/archive <task> | confirm with the user first, then execute |

### Matching rules

- Only search within this project's team + project scope; derive keywords from the user's request (strip verbs like "start"/"finish").
- When the user gives an issue ID (e.g. ZHA-12), use that ID directly; no fuzzy matching.
- Only auto-change status when the match is unambiguous; otherwise list candidates and let the user choose — never guess.
- New issues: if the project has milestones (Phase 1-4), attach the milestone matching the feature's phase.

### Branch conventions

- Feature: `feat/<issue-id>-<kebab-slug>`
- Bug: `fix/<issue-id>-<kebab-slug>`
- Docs/refactor: `docs/`, `refactor/` likewise
- Before creating a branch, check the current branch and working-tree state; branch off main (or the repo's default branch).

### Commit and acceptance

- Use Conventional Commits and reference the issue: `type(scope): description (#ZHA-12)`
- Before marking any task Done, the matching validation must pass: backend `pytest`, frontend `npm run build`; for integration features, also confirm the SSE event sequence is correct.

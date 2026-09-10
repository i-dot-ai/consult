# Developer experience

Notes on tooling that speeds up work on this repo. Everything here is optional and
per-developer - none of it is required to build or run the app, and no shared
credentials or config are committed (auth is individual, via your own accounts).

## Agentic coding

We use [Claude Code](https://claude.com/claude-code) or [Opencode](https://opencode.ai/) for agentic coding on this repo.
It's most useful here when paired with a few integrations: the **GitHub CLI** for PRs
and CI, plus MCP servers/plugins for **Linear** (issues) and **Context7** (up-to-date docs).

### Model access via the i.AI LiteLLM gateway

Point your coding agent at the **i.AI LiteLLM gateway** rather than
the native provider API. For repos handling Official-Sensitive information this keeps
prompt and code context inside our managed gateway for security and privacy, gives us
central control of model access and spend, and lets model versions be upgraded centrally.

The [`ai gateway tooling docs`](https://llm-gateway-console.i.ai.gov.uk/tooling)
site has instructions on how to set up both claude code and OpenCode configs.

### Suggested MCP servers / plugins

MCP (Model Context Protocol) servers give the agent extra tools; plugins bundle skills
and MCP servers together. The suggested set for this repo:

### Suggested MCP servers / plugins

| Tool                                                                      | Type       | What it's for                                         | Setup                                                                     |
|---------------------------------------------------------------------------|------------|-------------------------------------------------------|---------------------------------------------------------------------------|
| [GitHub CLI (`gh`)](https://cli.github.com/)                              | CLI        | Open PRs, check CI, read failed job logs              | `brew install gh` then `gh auth login`                                    |
| [Linear MCP](https://linear.app/docs/mcp)                                 | MCP server | Read/update `EDU-*` issues, attach PRs, create issues | `claude mcp add --transport sse linear-server https://mcp.linear.app/sse` |
| [Context7](https://context7.com/) | MCP Server | Finds up-to-date docs for relevant tools/techniques   | `npx ctx7 setup`, then get API key from the site                          |

### GitHub CLI (`gh`)

Used for everything PR- and CI-related from the terminal.

```bash
gh pr create --base main --title "..." --body "..."   # open a PR
gh pr checks <number>                                 # CI status for a PR
gh run view --job <job-id> --log-failed               # logs for a failed job
gh pr list --state merged --limit 20                  # recent merged PRs
```

Coding agents drive `gh` directly, so once authenticated it can open PRs and inspect CI
on your behalf. Follow repo conventions: branch off `main`, and only commit or push when
you intend to. For PR and review conventions, see [CONTRIBUTING.md](../CONTRIBUTING.md).

### Linear

Our work is tracked in the **Consult** workspace, largely in the **Product** team (issue keys `PRO-*`). The Linear
MCP lets the agent list what's in progress, move issues to Done as their PRs merge,
attach PR links, and create issues for new work. First use opens a browser to authorise
against your Linear account.

Conventions:

- Keep status honest: **In Review** when a PR is open, **Done** when it merges; link the
  PR on the issue. You can copy the branch name from the Linear item to link them from creation time.
- If an issue is only partly delivered, note that in the description rather than closing
  it (e.g. "engineering done, content outstanding"). Raise the follow-up ticket.
- Sub-issues that ship in the same PR as their parent get closed together.
- Respect the planned backlog: pick up prioritised work rather than starting something
  off-plan. Adding **sub-issues** under an existing ticket is fine, but avoid doing
  unplanned work and then raising a **top-level ticket** to describe what you already
  built - that bypasses prioritisation. If new work seems worth doing, raise it as an
  issue and let it be prioritised before picking it up.
- Similar to above, follow the milestones and targets set out by the project tech-lead


## Safety notes

- Coding agents should ask before hard-to-reverse or outward-facing actions (pushing, opening PRs,
  posting comments). Approve deliberately.
- Never commit secrets or personal agent state. `.claude/settings.local.json` is
  per-developer and stays local; real env values live in SSM, not the repo.
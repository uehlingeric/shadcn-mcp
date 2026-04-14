# shadcn MCP

MCP server that provides direct access to the [shadcn/ui v4](https://ui.shadcn.com/) component registry. Built for [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

## What It Does

Fetches shadcn/ui v4 component source code, blocks, and metadata directly from the official GitHub registry — so Claude Code can look up component implementations, search for blocks, and reference source code without leaving the terminal.

- **Component lookup** — fetch any shadcn/ui v4 component source code
- **Block browsing** — list and fetch pre-built page sections (login forms, dashboards, sidebars)
- **Search** — find components and blocks by keyword
- **1-hour cache** — avoids repeated GitHub fetches

## MCP Tools

| Tool | Description |
|------|-------------|
| `list_components` | List all available shadcn/ui v4 components |
| `get_component` | Fetch source code for a specific component (e.g., `button`, `dialog`) |
| `list_blocks` | List all blocks, optionally filtered by category |
| `get_block` | Fetch source code for a specific block (e.g., `login-01`, `dashboard-01`) |
| `search` | Search components and blocks by name or keyword |

## Data Source

All data is fetched from the official shadcn/ui v4 GitHub repository:
- **Registry index:** `__index__.tsx` (component metadata, file paths, categories)
- **Blocks index:** `__blocks__.json` (pre-built page sections)
- **Style:** `new-york-v4`

## Setup

### Prerequisites

- Python 3.10+

### Install Dependencies

```bash
pip install httpx mcp
```

### Configure Claude Code

Add to your Claude Code MCP settings (`~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "shadcn": {
      "command": "python3",
      "args": ["/path/to/shadcn-mcp/server.py"]
    }
  }
}
```

### Skill (Optional)

Copy `SKILL.md` to `~/.claude/skills/shadcn/SKILL.md` to enable the `/shadcn` slash command with formatted output and natural language mode.

## Usage

```
> Show me the dialog component source

[shadcn] get_component ..................... 0.3s
  dialog (registry:ui)
  File: new-york-v4/ui/dialog.tsx
  ...source code...
```

```
> What authentication blocks are available?

[shadcn] list_blocks ....................... 0.2s
  login-01 [authentication] — Simple email login
  login-02 [authentication] — Login with social providers
  ...
```

## Architecture

Single-file MCP server (`server.py`, ~355 lines) using the Python MCP SDK with stdio transport. Parses the shadcn/ui v4 `__index__.tsx` at startup to build a component registry. HTTP fetches use `httpx` with a 1-hour in-memory cache.

## License

MIT

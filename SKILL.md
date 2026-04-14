---
name: shadcn
description: "Look up shadcn/ui v4 components, blocks, and source code. Use when the user needs component source code, wants to find shadcn components, or is building a frontend with shadcn/ui. Triggers on: /shadcn, shadcn component lookups, 'how does the shadcn X component work', UI component reference requests."
---

# shadcn — shadcn/ui v4 Component Reference

Fetches component source code, blocks, and metadata directly from the official shadcn/ui v4 GitHub registry.

## CLI Interface

```
/shadcn <command> [args]
```

## Commands

| Command | Description |
|---------|-------------|
| `list` | List all available components |
| `get <name>` | Get source code for a component (e.g. `button`, `dialog`) |
| `blocks [category]` | List all blocks, optionally filtered by category |
| `block <name>` | Get source code for a block (e.g. `login-01`, `dashboard-01`) |
| `search <query>` | Search components and blocks by keyword |
| (no command) | Natural language — infer the intent |

## Execution Rules

### Timing

Track elapsed time for every shadcn MCP tool call. Print timing inline:

```
[shadcn] get_component ..................... 0.3s
  button (registry:ui)
  File: new-york-v4/ui/button.tsx (2.1KB)
```

Use `date +%s%N` before and after each `mcp__shadcn__*` tool call. Format as `Xs` for under 60s, `Xm Ys` for 60s+.

### Output Format

After every MCP tool call, immediately print a formatted summary. The format is:

```
[shadcn] <tool_name> ....................... <elapsed>
  <summary>
```

For `get_component` and `get_block`, show the full source code after the summary line.

For `list_components` and `list_blocks`, show a compact table.

For `search`, show matching results with type labels.

### Natural Language Mode

When no explicit command is given, infer intent:

- "show me the button component" -> get_component button
- "what dialog components are there" -> search dialog
- "list authentication blocks" -> list_blocks authentication
- "how does the form component work" -> get_component form

### Data Source

All data is fetched from the official shadcn/ui v4 GitHub repository:
- Components: `https://raw.githubusercontent.com/shadcn-ui/ui/main/apps/v4/registry/new-york-v4/ui/`
- Blocks: `https://raw.githubusercontent.com/shadcn-ui/ui/main/apps/v4/registry/new-york-v4/blocks/`
- Index: `https://raw.githubusercontent.com/shadcn-ui/ui/main/apps/v4/registry/__index__.tsx`

Results are cached for 1 hour to avoid repeated fetches.

### Block Categories

Common categories: `authentication`, `login`, `dashboard`, `sidebar`, `calendar`, `products`

### Error Handling

If a component or block is not found:

```
[shadcn] get_component .................... FAILED (0.1s)
  Component 'xyz' not found
```

Suggest running `search` to find similar components.

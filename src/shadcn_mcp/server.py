#!/usr/bin/env python3
"""shadcn — MCP server for shadcn/ui v4 component registry."""

import asyncio
import json
import re
import sys
import time

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

GITHUB_RAW = "https://raw.githubusercontent.com/shadcn-ui/ui/main/apps/v4/registry"
STYLE = "new-york-v4"

# ── Cache ───────────────────────────────────────────────────────────────────

_cache: dict[str, tuple[float, any]] = {}
CACHE_TTL = 3600  # 1 hour


def _get_cache(key: str):
    if key in _cache:
        ts, val = _cache[key]
        if time.time() - ts < CACHE_TTL:
            return val
    return None


def _set_cache(key: str, val):
    _cache[key] = (time.time(), val)


# ── HTTP ────────────────────────────────────────────────────────────────────

async def _fetch(url: str) -> str:
    cached = _get_cache(url)
    if cached is not None:
        return cached
    async with httpx.AsyncClient(timeout=30) as c:
        resp = await c.get(url)
        resp.raise_for_status()
        text = resp.text
        _set_cache(url, text)
        return text


async def _fetch_json(url: str):
    return json.loads(await _fetch(url))


# ── Registry Index ──────────────────────────────────────────────────────────

_index: dict[str, dict] = {}


async def _load_index():
    """Parse the __index__.tsx to extract component metadata."""
    global _index
    raw = await _fetch(f"{GITHUB_RAW}/__index__.tsx")

    # Extract entries from the new-york-v4 section
    entries = {}
    current_name = None
    current_entry = {}
    in_style = False

    for line in raw.split("\n"):
        stripped = line.strip()

        # Detect start of new-york-v4 block
        if '"new-york-v4"' in stripped:
            in_style = True
            continue

        if not in_style:
            continue

        # Match component name at indent level 4
        m = re.match(r'^    ([\w][\w-]*)\s*:\s*\{', line)
        if m and not line.startswith("      "):
            if current_name and current_entry:
                entries[current_name] = current_entry
            current_name = m.group(1)
            current_entry = {"name": current_name}
            continue

        if current_name:
            # Extract simple string fields
            for field in ("type", "description", "title"):
                m = re.match(rf'^\s+{field}:\s*"([^"]*)"', stripped)
                if m:
                    current_entry[field] = m.group(1)

            # Extract file paths
            m = re.match(r'^\s+path:\s*"([^"]*)"', stripped)
            if m:
                current_entry.setdefault("files", []).append(m.group(1))

            # Extract categories
            m = re.match(r'^\s+categories:\s*\[(.+)\]', stripped)
            if m:
                cats = re.findall(r'"([^"]*)"', m.group(1))
                current_entry["categories"] = cats

    if current_name and current_entry:
        entries[current_name] = current_entry

    _index = entries


def _classify(entry: dict) -> str:
    t = entry.get("type", "")
    if "block" in t:
        return "block"
    if "example" in t:
        return "example"
    return "component"


# ── Blocks Index ────────────────────────────────────────────────────────────

_blocks: list[dict] = []


async def _load_blocks():
    global _blocks
    try:
        _blocks = await _fetch_json(f"{GITHUB_RAW}/__blocks__.json")
    except Exception:
        _blocks = []


# ── Tools ───────────────────────────────────────────────────────────────────

TOOLS = [
    Tool(
        name="list_components",
        description="List all shadcn/ui v4 components.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="get_component",
        description="Get source code for a shadcn/ui v4 component.",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Component name (e.g. 'button', 'dialog')"},
            },
            "required": ["name"],
        },
    ),
    Tool(
        name="list_blocks",
        description="List all shadcn/ui v4 blocks (pre-built page sections).",
        inputSchema={
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Filter by category (e.g. 'authentication', 'dashboard')"},
            },
        },
    ),
    Tool(
        name="get_block",
        description="Get source code for a shadcn/ui v4 block.",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Block name (e.g. 'login-01', 'dashboard-01')"},
            },
            "required": ["name"],
        },
    ),
    Tool(
        name="search",
        description="Search components and blocks by name or keyword.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
            },
            "required": ["query"],
        },
    ),
]


# ── Handlers ────────────────────────────────────────────────────────────────

app = Server("shadcn")


def _log(msg: str):
    print(msg, file=sys.stderr, flush=True)


@app.list_tools()
async def list_tools():
    return TOOLS


async def _fetch_source(file_path: str) -> str:
    """Fetch a source file from the GitHub registry."""
    url = f"{GITHUB_RAW}/{file_path}"
    return await _fetch(url)


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    t0 = time.perf_counter()
    try:
        if name == "list_components":
            components = [
                {"name": e["name"], "type": e.get("type", "?")}
                for e in _index.values()
                if _classify(e) == "component"
            ]
            components.sort(key=lambda x: x["name"])
            lines = [f"{c['name']}" for c in components]
            elapsed = time.perf_counter() - t0
            return [TextContent(type="text", text=f"── list_components ── {elapsed:.1f}s ── {len(lines)} components ──\n" + "\n".join(lines))]

        elif name == "get_component":
            comp_name = arguments["name"]
            entry = _index.get(comp_name)
            if not entry:
                return [TextContent(type="text", text=f"Component '{comp_name}' not found")]

            files = entry.get("files", [])
            if not files:
                # Try default path
                files = [f"{STYLE}/ui/{comp_name}.tsx"]

            parts = [f"── {comp_name} ──"]
            if entry.get("type"):
                parts.append(f"Type: {entry['type']}")
            if entry.get("description") and entry["description"] != "":
                parts.append(f"Description: {entry['description']}")

            for fp in files:
                try:
                    src = await _fetch_source(fp)
                    parts.append(f"\n── {fp} ──")
                    parts.append(src)
                except Exception as e:
                    parts.append(f"\n── {fp} ── FAILED: {e}")

            elapsed = time.perf_counter() - t0
            parts.insert(0, f"── get_component ── {elapsed:.1f}s ──")
            return [TextContent(type="text", text="\n".join(parts))]

        elif name == "list_blocks":
            category = arguments.get("category", "").lower()
            blocks = _blocks
            if category:
                blocks = [b for b in blocks if category in [c.lower() for c in b.get("categories", [])]]
            lines = []
            for b in blocks:
                cats = ", ".join(b.get("categories", []))
                desc = b.get("description", "")
                line = b["name"]
                if cats:
                    line += f" [{cats}]"
                if desc:
                    line += f" — {desc}"
                lines.append(line)
            elapsed = time.perf_counter() - t0
            return [TextContent(type="text", text=f"── list_blocks ── {elapsed:.1f}s ── {len(lines)} blocks ──\n" + "\n".join(lines))]

        elif name == "get_block":
            block_name = arguments["name"]
            # Blocks are in the examples directory typically
            entry = _index.get(block_name)
            files = []
            if entry:
                files = entry.get("files", [])

            if not files:
                # Try common block paths
                for prefix in [f"{STYLE}/blocks/{block_name}", f"{STYLE}/examples/{block_name}"]:
                    try:
                        src = await _fetch_source(f"{prefix}.tsx")
                        files = [f"{prefix}.tsx"]
                        break
                    except Exception:
                        continue

            if not files:
                return [TextContent(type="text", text=f"Block '{block_name}' not found")]

            parts = ["── get_block ──"]
            if entry and entry.get("description"):
                parts.append(f"Description: {entry['description']}")

            for fp in files:
                try:
                    src = await _fetch_source(fp)
                    parts.append(f"\n── {fp} ──")
                    parts.append(src)
                except Exception as e:
                    parts.append(f"\n── {fp} ── FAILED: {e}")

            elapsed = time.perf_counter() - t0
            parts.insert(0, f"── {elapsed:.1f}s ──")
            return [TextContent(type="text", text="\n".join(parts))]

        elif name == "search":
            query = arguments["query"].lower()
            results = []
            for e in _index.values():
                score = 0
                if query in e["name"]:
                    score += 2
                if query in e.get("description", "").lower():
                    score += 1
                cats = e.get("categories", [])
                if any(query in c.lower() for c in cats):
                    score += 1
                if score > 0:
                    results.append((score, e))
            results.sort(key=lambda x: (-x[0], x[1]["name"]))
            lines = []
            for _, e in results[:30]:
                kind = _classify(e)
                line = f"{e['name']} ({kind})"
                if e.get("description"):
                    line += f" — {e['description'][:80]}"
                lines.append(line)
            elapsed = time.perf_counter() - t0
            return [TextContent(type="text", text=f"── search '{query}' ── {elapsed:.1f}s ── {len(lines)} results ──\n" + "\n".join(lines))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        elapsed = time.perf_counter() - t0
        return [TextContent(type="text", text=f"── {name} FAILED ── {elapsed:.1f}s ──\n{e}")]


# ── Main ────────────────────────────────────────────────────────────────────

async def main():
    _log("shadcn: loading index...")
    await _load_index()
    await _load_blocks()
    _log(f"shadcn: {len(_index)} entries, {len(_blocks)} blocks loaded")
    async with stdio_server() as (read, write):
        await app.run(read, write, app.create_initialization_options())

def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()

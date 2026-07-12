# Changelog

All notable changes to this project are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows [SemVer](https://semver.org/).

## [1.0.0] - 2026-07-11

### Added

- MCP tools: `list_components`, `get_component`, `list_blocks`, `get_block`, `search`
- Fetches component and block source from the official shadcn/ui v4 registry (`new-york-v4` style)
- 1-hour in-memory cache to avoid repeated GitHub fetches

### Changed

- Migrated to uv-managed packaging: `pyproject.toml`, `uv.lock`, `src/shadcn_mcp/` layout, `shadcn-mcp` console script

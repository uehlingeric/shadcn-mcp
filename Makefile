.PHONY: setup lint run clean

setup:
	uv sync

lint:
	uv run ruff check src/
	uv run ruff format --check src/

run:
	uv run shadcn-mcp

clean:
	rm -rf .venv src/shadcn_mcp/__pycache__

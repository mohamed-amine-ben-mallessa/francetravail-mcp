"""
francetravail-mcp — MCP server for the official France Travail API.

This is a thin entry point for `python server.py` (legacy mode).
The canonical source is the `francetravail_mcp` package.
"""
from francetravail_mcp import *  # noqa: F403

if __name__ == "__main__":
    main()

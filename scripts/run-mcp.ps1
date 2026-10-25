$ErrorActionPreference = "Stop"
if (!(Test-Path ".venv")) { python -m venv .venv }
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\nifty-mcp.exe

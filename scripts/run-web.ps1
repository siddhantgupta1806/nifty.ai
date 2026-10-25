$ErrorActionPreference = "Stop"
if (!(Test-Path ".venv")) { python -m venv .venv }
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\nifty.exe web --host 127.0.0.1 --port 8766

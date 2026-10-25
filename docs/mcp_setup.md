# MCP Server Setup

Nifty.AI ships a stdio MCP server for local AI assistants.

## Run

```powershell
.\.venv\Scripts\nifty-mcp.exe
```

## Tools

- `nifty_status`: runtime configuration summary.
- `run_csv_backtest`: run a CSV-backed local backtest.
- `create_html_report`: generate an HTML report from DuckDB.
- `openalgo_analyzer_status`: inspect Analyzer Mode through OpenAlgo.

## Example Client Config

```json
{
  "mcpServers": {
    "nifty-ai": {
      "command": "C:/Shashwat/nifty.ai/.venv/Scripts/nifty-mcp.exe",
      "cwd": "C:/Shashwat/nifty.ai"
    }
  }
}
```

## Security

The MCP server runs with local file access from its working directory. Only connect it to assistants you trust with this workspace.

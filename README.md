# Proxy MCP Server

An MCP (Model Context Protocol) Server that acts as a proxy for the SDR Backend, enabling AI agents to upload CSV files to campaigns.

## Available Tools

### `upload_csv`
Upload customers from a CSV file to a campaign.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `user_id` | string | Yes | The ID of the user |
| `conversation_id` | string | Yes | The ID of the campaign/conversation |
| `csv_url` | string | Yes | URL of the CSV file to upload |
| `force_proceed` | boolean | No | Force upload even if optional headers are missing |

## Setup

### 1. Install Dependencies
```bash
uv venv
uv pip install -e .
```

### 2. Configure Environment
Create a `.env` file:
```env
SERVER_AUTH_KEY=your-backend-auth-key
BACKEND_URL=http://localhost:8000/api/v1
HOST=0.0.0.0
PORT=8001
```

### 3. Run the Server
```bash
uv run uvicorn src.server:app --host 0.0.0.0 --port 8001
```

## Usage with AI Agents

### Claude Desktop
Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "sdr-proxy": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/proxy-mcp-server",
        "run",
        "uvicorn",
        "src.server:app",
        "--host", "127.0.0.1",
        "--port", "8001"
      ],
      "env": {
        "SERVER_AUTH_KEY": "your-backend-auth-key",
        "BACKEND_URL": "http://localhost:8000/api/v1"
      }
    }
  }
}
```

### Cursor / VS Code with MCP Extension
Add to your MCP settings:

```json
{
  "mcpServers": {
   "sdr-proxy": {
      "serverUrl": "http://127.0.0.1:8001/sse",
      "transport": "sse"
  }
}
```

## Testing with MCP Inspector

```bash
npx @modelcontextprotocol/inspector http://localhost:8001/sse
```

This opens a browser UI where you can test the tools.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/sse` | GET | SSE connection for MCP |
| `/messages` | POST | MCP message handler |

## Requirements

- Python 3.10+
- uv (Python package manager)
- Running SDR Backend on port 8000

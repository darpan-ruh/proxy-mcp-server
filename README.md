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
uv run python -m src.server
```

### 4. Expose via Cloudflare Tunnel (for remote access)
```bash
cloudflared tunnel --url http://localhost:8001
```

## Usage with AI Agents

### Antigravity / Cursor / VS Code
Add to your MCP config:

```json
{
  "mcpServers": {
    "sdr-proxy": {
      "url": "https://your-tunnel-url.trycloudflare.com/mcp",
      "transport": "streamable-http"
    }
  }
}
```

### Claude Desktop (Local)
Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "sdr-proxy": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/proxy-mcp-server",
        "run",
        "python",
        "-m",
        "src.server"
      ],
      "env": {
        "SERVER_AUTH_KEY": "your-backend-auth-key",
        "BACKEND_URL": "http://localhost:8000/api/v1"
      }
    }
  }
}
```

## Testing with MCP Inspector

```bash
npx @modelcontextprotocol/inspector http://localhost:8001/mcp
```

This opens a browser UI where you can test the tools.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/mcp` | POST | StreamableHTTP endpoint for MCP |

## Architecture

```
AI Agent 
        ↓
        ↓ (StreamableHTTP)
        ↓
[Proxy MCP Server] ──→ localhost:8000 (SDR Backend)
        ↑
        ↑ (Cloudflare Tunnel for remote access)
        ↑
Remote AI Agents
```

## Requirements

- Python 3.10+
- uv (Python package manager)
- Running SDR Backend on port 8000
- cloudflared (for remote access)

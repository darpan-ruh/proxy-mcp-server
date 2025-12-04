import json
import httpx
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse
import mcp.types as types
from src.config import BACKEND_URL, SERVER_AUTH_KEY, HOST, PORT
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP Server
mcp_server = Server("proxy-mcp-server")

# SSE Transport - must be initialized before routes
sse = SseServerTransport("/messages")

@mcp_server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="upload_csv",
            description="Upload customers from a CSV file to a campaign",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "The ID of the user"},
                    "conversation_id": {"type": "string", "description": "The ID of the campaign/conversation"},
                    "csv_url": {"type": "string", "description": "The URL of the CSV file to upload"},
                    "force_proceed": {"type": "boolean", "description": "Force upload even if optional headers are missing", "default": False}
                },
                "required": ["user_id", "conversation_id", "csv_url"]
            }
        )
    ]

@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution"""
    logger.info(f"Tool called: {name} with arguments: {arguments}")
    
    if name == "upload_csv":
        if not arguments:
            raise ValueError("Missing arguments")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{BACKEND_URL}/customers/csv",
                    json=arguments,
                    headers={"X-Server-Auth-Key": SERVER_AUTH_KEY},
                    timeout=60.0
                )
                
                # Get full response with status code
                status_code = response.status_code
                try:
                    result = response.json()
                except:
                    result = {"raw_text": response.text}
                
                # Build complete response
                full_response = {
                    "status_code": status_code,
                    "success": status_code == 200,
                    "response": result
                }
                
                logger.info(f"Backend response (status {status_code}): {result}")
                return [types.TextContent(type="text", text=json.dumps(full_response, indent=2))]
                
            except Exception as e:
                logger.error(f"Error calling backend: {e}")
                error_response = {
                    "status_code": 500,
                    "success": False,
                    "error": str(e)
                }
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
    
    raise ValueError(f"Unknown tool: {name}")


async def handle_sse(request: Request):
    """Handle SSE connection"""
    logger.info("SSE connection requested")
    async with sse.connect_sse(
        request.scope, 
        request.receive, 
        request._send
    ) as streams:
        logger.info("SSE connection established, running MCP server")
        await mcp_server.run(
            streams[0], 
            streams[1], 
            mcp_server.create_initialization_options()
        )


async def handle_messages(request: Request):
    """Handle POST messages"""
    logger.info("Message received")
    await sse.handle_post_message(request.scope, request.receive, request._send)


async def health_check(request: Request):
    """Health check endpoint"""
    return JSONResponse({"status": "ok", "server": "proxy-mcp-server"})


# Routes
routes = [
    Route("/", endpoint=health_check, methods=["GET"]),
    Route("/sse", endpoint=handle_sse, methods=["GET"]),
    Route("/messages", endpoint=handle_messages, methods=["POST"]),
]

# Middleware
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
]

# Create Starlette app
app = Starlette(routes=routes, middleware=middleware)


if __name__ == "__main__":
    logger.info(f"Starting Proxy MCP Server on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)

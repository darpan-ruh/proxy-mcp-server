import json
import httpx
import contextlib
import uvicorn
import logging
from mcp.server import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Route
from starlette.responses import JSONResponse
import mcp.types as types
from src.config import BACKEND_URL, SERVER_AUTH_KEY, HOST, PORT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP Server
mcp_server = Server("proxy-mcp-server")


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
                
                status_code = response.status_code
                try:
                    result = response.json()
                except:
                    result = {"raw_text": response.text}
                
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


async def health_check(request):
    """Health check endpoint"""
    return JSONResponse({"status": "ok", "server": "proxy-mcp-server"})


async def create_app():
    """Create the Starlette application with StreamableHTTP transport"""
    
    # Create the session manager for StreamableHTTP
    session_manager = StreamableHTTPSessionManager(
        app=mcp_server,
        json_response=False,
        stateless=False,
    )
    
    # Handler for StreamableHTTP connections
    class HandleStreamableHttp:
        def __init__(self, session_manager):
            self.session_manager = session_manager
        
        async def __call__(self, scope, receive, send):
            try:
                logger.info("Handling Streamable HTTP connection...")
                await self.session_manager.handle_request(scope, receive, send)
                logger.info("Streamable HTTP connection closed.")
            except Exception as e:
                logger.error(f"Error handling Streamable HTTP request: {e}")
                await send({
                    "type": "http.response.start",
                    "status": 500,
                    "headers": [(b"content-type", b"application/json")],
                })
                await send({
                    "type": "http.response.body",
                    "body": json.dumps({"error": f"Internal server error: {str(e)}"}).encode("utf-8"),
                })
    
    # Routes
    routes = [
        Route("/", endpoint=health_check, methods=["GET"]),
        Route("/mcp", endpoint=HandleStreamableHttp(session_manager), methods=["POST"]),
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
    
    # Lifespan for session manager
    @contextlib.asynccontextmanager
    async def lifespan(app):
        async with session_manager.run():
            logger.info("Application started with StreamableHTTP session manager!")
            try:
                yield
            finally:
                logger.info("Application shutting down...")
    
    return Starlette(routes=routes, middleware=middleware, lifespan=lifespan)


async def start_server():
    """Start the server asynchronously"""
    app = await create_app()
    logger.info(f"Starting Proxy MCP Server on {HOST}:{PORT}")
    
    config = uvicorn.Config(app, host=HOST, port=PORT)
    server = uvicorn.Server(config)
    await server.serve()


# For uvicorn to import
app = None

if __name__ == "__main__":
    import asyncio
    asyncio.run(start_server())

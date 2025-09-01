#!/usr/bin/env python3
"""Standalone MCP server for ChatR integration with agentic frameworks."""

import uvicorn
import typer
from pathlib import Path
import logging

from ..mcp.server import create_mcp_server
from ..core.config import ChatRConfig

logger = logging.getLogger(__name__)

def serve_mcp(
    host: str = "localhost",
    port: int = 8002,  # Different port from main ChatR server
    log_level: str = "info"
):
    """Start standalone ChatR MCP server."""
    
    print(f"🚀 Starting ChatR MCP Server...")
    print(f"📡 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"📚 Endpoints: http://{host}:{port}/mcp/")
    
    try:
        # Load ChatR config
        config = ChatRConfig.load_config()
        config.setup_directories()
        
        # Create MCP FastAPI app
        mcp_app = create_mcp_server(config)
        
        print("✅ MCP server configured successfully")
        print("\n📋 Available endpoints:")
        print(f"   • GET  http://{host}:{port}/mcp/tools")
        print(f"   • POST http://{host}:{port}/mcp/execute") 
        print(f"   • GET  http://{host}:{port}/mcp/health")
        
        # Start server
        uvicorn.run(
            mcp_app,
            host=host,
            port=port,
            log_level=log_level.lower()
        )
        
    except Exception as e:
        print(f"❌ Failed to start MCP server: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app = typer.Typer()
    
    @app.command()
    def serve(
        host: str = typer.Option("localhost", help="Host to bind to"),
        port: int = typer.Option(8002, help="Port to bind to"),
        log_level: str = typer.Option("info", help="Log level")
    ):
        """Start ChatR MCP server."""
        serve_mcp(host, port, log_level)
    
    app()
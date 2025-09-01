"""MCP Server for exposing ChatR tools to agentic frameworks."""

import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ..core.assistant import ChatRAssistant
from ..core.config import ChatRConfig
from ..rag.retriever import HybridRetriever
from ..rag.indexer import RDocumentationIndexer
from ..r_integration.executor import SecureRExecutor

logger = logging.getLogger(__name__)


class MCPRequest(BaseModel):
    """Standard MCP request format."""
    tool: str = Field(..., description="Tool name to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional context")


class MCPResponse(BaseModel):
    """Standard MCP response format."""
    success: bool = Field(..., description="Whether the operation was successful")
    result: Any = Field(..., description="Tool execution result")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ChatRMCPServer:
    """MCP Server exposing ChatR tools for agentic frameworks."""
    
    def __init__(self, config: Optional[ChatRConfig] = None):
        """Initialize MCP server with ChatR components."""
        self.config = config or ChatRConfig.load_config()
        
        # Initialize core components
        self.config.setup_directories()
        self.indexer = RDocumentationIndexer(
            cache_dir=self.config.cache_dir,
            cran_mirror=self.config.cran_mirror
        )
        self.retriever = HybridRetriever(index_dir=self.config.index_dir)
        self.r_executor = SecureRExecutor(
            timeout=self.config.r_timeout,
            max_output_lines=self.config.max_output_lines
        )
        self.assistant = ChatRAssistant(config=self.config)
        
        # Initialize FastAPI app
        self.app = FastAPI(
            title="ChatR MCP Server",
            description="MCP endpoints for ChatR tools - integrate R help into any agent",
            version="1.0.0"
        )
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register MCP endpoint routes."""
        
        @self.app.get("/mcp/tools")
        async def list_tools():
            """List available ChatR tools for MCP clients."""
            return {
                "tools": [
                    {
                        "name": "r_help",
                        "description": "Get R function help and documentation",
                        "parameters": {
                            "function_name": {"type": "string", "required": True},
                            "package": {"type": "string", "required": False}
                        }
                    },
                    {
                        "name": "r_search",
                        "description": "Search R documentation and help topics",
                        "parameters": {
                            "query": {"type": "string", "required": True},
                            "limit": {"type": "integer", "required": False, "default": 10}
                        }
                    },
                    {
                        "name": "r_execute",
                        "description": "Execute R code safely in sandbox",
                        "parameters": {
                            "code": {"type": "string", "required": True},
                            "timeout": {"type": "integer", "required": False, "default": 30}
                        }
                    },
                    {
                        "name": "r_explain",
                        "description": "Explain R code or concepts with ChatR AI",
                        "parameters": {
                            "query": {"type": "string", "required": True},
                            "context": {"type": "string", "required": False}
                        }
                    },
                    {
                        "name": "r_package_info",
                        "description": "Get comprehensive information about R packages",
                        "parameters": {
                            "package_name": {"type": "string", "required": True},
                            "include_functions": {"type": "boolean", "required": False, "default": True}
                        }
                    },
                    {
                        "name": "r_vignettes",
                        "description": "Get package vignettes and tutorials",
                        "parameters": {
                            "package_name": {"type": "string", "required": True}
                        }
                    }
                ]
            }
        
        @self.app.post("/mcp/execute", response_model=MCPResponse)
        async def execute_tool(request: MCPRequest):
            """Execute a ChatR tool via MCP interface."""
            try:
                if request.tool == "r_help":
                    result = await self._handle_r_help(request.parameters)
                elif request.tool == "r_search":
                    result = await self._handle_r_search(request.parameters)
                elif request.tool == "r_execute":
                    result = await self._handle_r_execute(request.parameters)
                elif request.tool == "r_explain":
                    result = await self._handle_r_explain(request.parameters)
                elif request.tool == "r_package_info":
                    result = await self._handle_r_package_info(request.parameters)
                elif request.tool == "r_vignettes":
                    result = await self._handle_r_vignettes(request.parameters)
                else:
                    raise HTTPException(status_code=400, detail=f"Unknown tool: {request.tool}")
                
                return MCPResponse(
                    success=True,
                    result=result,
                    metadata={"tool": request.tool, "execution_time": "fast"}
                )
                
            except Exception as e:
                logger.error(f"MCP tool execution error: {e}")
                return MCPResponse(
                    success=False,
                    result=None,
                    error=str(e),
                    metadata={"tool": request.tool}
                )
        
        @self.app.get("/mcp/health")
        async def health_check():
            """Health check for MCP server."""
            return {
                "status": "healthy",
                "version": "1.0.0",
                "components": {
                    "indexer": "ready",
                    "retriever": "ready", 
                    "r_executor": "ready",
                    "assistant": "ready"
                }
            }
    
    async def _handle_r_help(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle R help requests."""
        function_name = params.get("function_name")
        package = params.get("package")
        
        if not function_name:
            raise ValueError("function_name is required")
        
        # Search for help documentation
        query = f"{function_name}"
        if package:
            query = f"{package}::{function_name}"
        
        docs = self.retriever.retrieve(query, k=3)
        
        if docs:
            help_content = docs[0].content
            return {
                "function": function_name,
                "package": package,
                "help_content": help_content,
                "additional_docs": len(docs) - 1
            }
        else:
            return {
                "function": function_name,
                "package": package,
                "help_content": f"No documentation found for {function_name}",
                "additional_docs": 0
            }
    
    async def _handle_r_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle R documentation search."""
        query = params.get("query")
        limit = params.get("limit", 10)
        
        if not query:
            raise ValueError("query is required")
        
        docs = self.retriever.retrieve(query, k=limit)
        
        results = []
        for doc in docs:
            results.append({
                "title": doc.metadata.get("title", "Unknown"),
                "package": doc.metadata.get("package", "Unknown"),
                "function": doc.metadata.get("function", "Unknown"),
                "content_preview": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                "relevance_score": getattr(doc, 'score', 0.0)
            })
        
        return {
            "query": query,
            "total_results": len(results),
            "results": results
        }
    
    async def _handle_r_execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle R code execution."""
        code = params.get("code")
        timeout = params.get("timeout", 30)
        
        if not code:
            raise ValueError("code is required")
        
        # Update executor timeout if specified
        original_timeout = self.r_executor.timeout
        self.r_executor.timeout = timeout
        
        try:
            result = self.r_executor.execute_code(code)
            
            return {
                "code": code,
                "success": result.success,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time": result.execution_time,
                "timeout_used": timeout
            }
        finally:
            # Restore original timeout
            self.r_executor.timeout = original_timeout
    
    async def _handle_r_explain(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle R concept explanation requests."""
        query = params.get("query")
        context = params.get("context", "")
        
        if not query:
            raise ValueError("query is required")
        
        # Use ChatR assistant to explain
        full_query = f"Explain: {query}"
        if context:
            full_query += f" Context: {context}"
        
        response = self.assistant.process_query(full_query)
        
        return {
            "query": query,
            "explanation": response if isinstance(response, str) else str(response),
            "context_used": bool(context),
            "sources": []
        }
    
    async def _handle_r_package_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle R package information requests."""
        package_name = params.get("package_name")
        include_functions = params.get("include_functions", True)
        
        if not package_name:
            raise ValueError("package_name is required")
        
        # Get package documentation
        docs = self.indexer.extract_man_pages(package_name)
        
        functions = []
        if include_functions and docs:
            functions = [
                {
                    "name": doc.metadata.get("function", "Unknown"),
                    "description": doc.content[:100] + "..." if len(doc.content) > 100 else doc.content
                }
                for doc in docs[:20]  # Limit to first 20 functions
            ]
        
        return {
            "package": package_name,
            "total_functions": len(docs),
            "functions": functions if include_functions else [],
            "documentation_available": len(docs) > 0
        }
    
    async def _handle_r_vignettes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle R vignettes requests."""
        package_name = params.get("package_name")
        
        if not package_name:
            raise ValueError("package_name is required")
        
        # Get vignettes
        vignettes = self.indexer.extract_vignettes(package_name)
        
        vignette_info = []
        for vignette in vignettes:
            vignette_info.append({
                "title": vignette.metadata.get("title", "Unknown"),
                "name": vignette.metadata.get("name", "Unknown"),
                "content_preview": vignette.content[:300] + "..." if len(vignette.content) > 300 else vignette.content
            })
        
        return {
            "package": package_name,
            "total_vignettes": len(vignettes),
            "vignettes": vignette_info
        }


def create_mcp_server(config: Optional[ChatRConfig] = None) -> FastAPI:
    """Create and configure MCP server."""
    mcp_server = ChatRMCPServer(config)
    return mcp_server.app
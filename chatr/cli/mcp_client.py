"""MCP client for testing and integration with ChatR."""

import json
import requests
import typer
from typing import Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel

console = Console()


def test_mcp_tools(host: str = "http://localhost:8001"):
    """Test MCP endpoints and show available tools."""
    
    try:
        # Test health
        health_response = requests.get(f"{host}/mcp/health")
        if health_response.status_code == 200:
            console.print("✅ MCP Server is healthy", style="green")
        
        # Get available tools
        tools_response = requests.get(f"{host}/mcp/tools")
        if tools_response.status_code == 200:
            tools = tools_response.json()["tools"]
            
            console.print(f"\n📚 Available MCP Tools ({len(tools)}):", style="bold blue")
            
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Tool", width=15)
            table.add_column("Description", width=40)
            table.add_column("Parameters", width=30)
            
            for tool in tools:
                params = ", ".join(tool["parameters"].keys())
                table.add_row(
                    tool["name"],
                    tool["description"],
                    params
                )
            
            console.print(table)
            
        return True
        
    except requests.RequestException as e:
        console.print(f"❌ Failed to connect to MCP server: {e}", style="red")
        return False


def execute_mcp_tool(tool_name: str, parameters: Dict[str, Any], 
                    host: str = "http://localhost:8001") -> Optional[Dict[str, Any]]:
    """Execute an MCP tool with given parameters."""
    
    try:
        payload = {
            "tool": tool_name,
            "parameters": parameters
        }
        
        response = requests.post(f"{host}/mcp/execute", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                return result["result"]
            else:
                console.print(f"❌ Tool execution failed: {result.get('error')}", style="red")
        else:
            console.print(f"❌ HTTP Error: {response.status_code}", style="red")
            
    except requests.RequestException as e:
        console.print(f"❌ Request failed: {e}", style="red")
    
    return None


def demo_mcp_tools(host: str = "http://localhost:8001"):
    """Demonstrate MCP tools with examples."""
    
    console.print("🚀 ChatR MCP Tools Demo", style="bold green")
    console.print("=" * 50)
    
    if not test_mcp_tools(host):
        return
    
    # Demo 1: R Help
    console.print("\n🔍 Demo 1: R Help Tool", style="bold blue")
    help_result = execute_mcp_tool("r_help", {"function_name": "mean"}, host)
    if help_result:
        console.print(Panel(
            help_result.get("help_content", "No content")[:300] + "...",
            title=f"Help for {help_result.get('function')}",
            border_style="blue"
        ))
    
    # Demo 2: R Search
    console.print("\n🔎 Demo 2: R Search Tool", style="bold blue")
    search_result = execute_mcp_tool("r_search", {"query": "linear model", "limit": 3}, host)
    if search_result:
        console.print(f"Found {search_result.get('total_results', 0)} results:")
        for i, result in enumerate(search_result.get('results', [])[:2]):
            console.print(f"  {i+1}. {result['title']} ({result['package']})")
    
    # Demo 3: R Execute
    console.print("\n⚡ Demo 3: R Execute Tool", style="bold blue")
    code = "x <- c(1, 2, 3, 4, 5); mean(x)"
    exec_result = execute_mcp_tool("r_execute", {"code": code}, host)
    if exec_result:
        console.print(f"Code: {code}")
        console.print(f"Result: {exec_result.get('stdout', '').strip()}")
    
    # Demo 4: R Explain
    console.print("\n💡 Demo 4: R Explain Tool", style="bold blue") 
    explain_result = execute_mcp_tool("r_explain", {"query": "What is linear regression?"}, host)
    if explain_result:
        console.print(Panel(
            explain_result.get("explanation", "No explanation")[:200] + "...",
            title="ChatR Explanation",
            border_style="green"
        ))
    
    console.print("\n✅ MCP Demo Complete!", style="bold green")


def mcp_integration_guide():
    """Show integration guide for MCP tools."""
    
    guide_text = """
# ChatR MCP Integration Guide

## Available Endpoints

**Base URL**: http://localhost:8001/mcp/

### 1. List Tools
GET /mcp/tools
- Returns all available ChatR tools

### 2. Execute Tool  
POST /mcp/execute
{
  "tool": "r_help",
  "parameters": {"function_name": "mean"}
}

### 3. Health Check
GET /mcp/health

## Tools Available

1. **r_help** - Get R function documentation
2. **r_search** - Search R documentation  
3. **r_execute** - Execute R code safely
4. **r_explain** - AI explanations
5. **r_package_info** - Package information
6. **r_vignettes** - Package tutorials

## Integration Examples

### Cursor/VS Code
Add to your agent configuration:
```json
{
  "mcp_servers": {
    "chatr": {
      "url": "http://localhost:8001/mcp/",
      "tools": ["r_help", "r_search", "r_execute"]
    }
  }
}
```

### Custom Agent
```python
import requests

def get_r_help(function_name):
    response = requests.post(
        "http://localhost:8001/mcp/execute",
        json={"tool": "r_help", "parameters": {"function_name": function_name}}
    )
    return response.json()["result"]
```
"""
    
    console.print(Panel(
        guide_text,
        title="ChatR MCP Integration Guide",
        border_style="cyan",
        expand=False
    ))


if __name__ == "__main__":
    app = typer.Typer()
    
    @app.command()
    def test(host: str = "http://localhost:8001"):
        """Test MCP endpoints."""
        test_mcp_tools(host)
    
    @app.command() 
    def demo(host: str = "http://localhost:8001"):
        """Run MCP tools demo."""
        demo_mcp_tools(host)
    
    @app.command()
    def guide():
        """Show integration guide."""
        mcp_integration_guide()
    
    app()
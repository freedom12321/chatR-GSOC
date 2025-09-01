"""Main CLI interface for ChatR."""

import typer
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from pathlib import Path

from ..core.config import ChatRConfig
from ..core.assistant import ChatRAssistant

app = typer.Typer(
    name="chatr",
    help="ChatR: An intelligent, local assistant for R programmers\n\n"
         "Quick start:\n"
         "  chatr chat 'How do I create plots?'    # Ask a question\n"
         "  chatr chat --interactive              # Start interactive mode\n"
         "  chatr chat -i                         # Start interactive mode (short)\n"
         "  chatr init                            # First-time setup",
    rich_markup_mode="rich"
)
console = Console()


@app.command()
def chat(
    query: Optional[str] = typer.Argument(None, help="Your R-related question"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Start interactive chat mode. Type 'quit', 'exit', or 'q' to leave, or use Ctrl+C"),
    config_path: Optional[Path] = typer.Option(None, "--config", help="Path to config file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output")
):
    """Ask ChatR a question about R programming.
    
    Examples:
        chatr chat "How do I create a histogram in R?"
        chatr chat --interactive
        chatr chat -i
    """
    
    # Load configuration
    config = ChatRConfig.load_config(config_path)
    config.setup_directories()
    
    # Initialize assistant
    assistant = ChatRAssistant(config)
    
    if interactive or query is None:
        console.print(Panel(
            "[bold blue]ChatR Interactive Mode[/bold blue]\n\n"
            "Ask me anything about R programming!\n"
            "Type 'quit' or 'exit' to leave.",
            title="Welcome to ChatR"
        ))
        
        while True:
            try:
                console.print("\n[bold green]You[/bold green]: ", end="")
                user_input = input()
                if user_input.lower() in ["quit", "exit", "q"]:
                    console.print("[yellow]Goodbye![/yellow]")
                    break
                
                response = assistant.process_query(user_input)
                console.print(f"\n[bold blue]ChatR[/bold blue]:")
                console.print(Panel(Markdown(response), title="Response"))
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Goodbye![/yellow]")
                break
            except typer.Abort:
                console.print("\n[yellow]Goodbye![/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error processing query: {e}[/red]")
                if verbose:
                    console.print_exception()
    
    elif query:
        try:
            response = assistant.process_query(query)
            console.print(Panel(Markdown(response), title="ChatR Response"))
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            if verbose:
                console.print_exception()
            raise typer.Exit(1)


@app.command()
def init(
    force: bool = typer.Option(False, "--force", help="Force reinitialization")
):
    """Initialize ChatR (setup config, download initial data)."""
    
    config_path = Path.home() / ".chatr" / "config.json"
    
    if config_path.exists() and not force:
        console.print("[yellow]ChatR is already initialized. Use --force to reinitialize.[/yellow]")
        return
    
    console.print("[bold blue]Initializing ChatR...[/bold blue]")
    
    # Create default configuration
    config = ChatRConfig()
    config.setup_directories()
    config.save_config()
    
    console.print(f"[green]✓[/green] Configuration saved to: {config_path}")
    
    # Initialize assistant to trigger initial setup
    try:
        assistant = ChatRAssistant(config)
        assistant.initialize()
        console.print("[green]✓[/green] ChatR initialization complete!")
        
        console.print(Panel(
            "[bold green]ChatR is ready![/bold green]\n\n"
            "Try: [code]chatr chat 'How do I create a linear regression in R?'[/code]\n"
            "Or start interactive mode: [code]chatr chat --interactive[/code]",
            title="Success"
        ))
        
    except Exception as e:
        console.print(f"[red]Error during initialization: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def status():
    """Show ChatR status and configuration."""
    
    config = ChatRConfig.load_config()
    
    console.print(Panel(
        f"[bold]Configuration:[/bold]\n"
        f"Cache Dir: {config.cache_dir}\n"
        f"Index Dir: {config.index_dir}\n"
        f"Ollama Host: {config.ollama_host}\n"
        f"Model: {config.ollama_model}\n"
        f"Embedding Model: {config.embedding_model}",
        title="ChatR Status"
    ))


@app.command()
def serve(
    host: str = typer.Option("localhost", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
    reload: bool = typer.Option(False, help="Enable auto-reload for development")
):
    """Start ChatR API server for R package integration."""
    
    console.print(f"[bold blue]Starting ChatR API server...[/bold blue]")
    console.print(f"Host: {host}")
    console.print(f"Port: {port}")
    
    try:
        import uvicorn
        from ..api.server import app as api_app
        
        uvicorn.run(
            api_app,
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except ImportError:
        console.print("[red]Error: FastAPI/Uvicorn not installed. Install with: pip install fastapi uvicorn[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Server error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def mcp(
    host: str = typer.Option("localhost", help="Host to bind MCP server to"),
    port: int = typer.Option(8002, help="Port for MCP server (separate from main server)"),
    log_level: str = typer.Option("info", help="Log level")
):
    """Start ChatR MCP server for agentic framework integration.
    
    The MCP server exposes ChatR tools as REST endpoints that can be used by:
    - Cursor IDE
    - GitHub Copilot extensions  
    - Custom agents
    - Any HTTP client
    
    Runs on separate port (8002) to avoid conflicts with main ChatR server (8001).
    """
    
    console.print(f"[bold green]🚀 Starting ChatR MCP Server...[/bold green]")
    console.print(f"📡 Host: {host}")
    console.print(f"🔌 Port: {port}")
    console.print(f"📚 Endpoints: http://{host}:{port}/mcp/")
    console.print(f"[dim]ℹ️  Separate from main ChatR server on port 8001[/dim]")
    
    try:
        import uvicorn
        from ..mcp.server import create_mcp_server
        from ..core.config import ChatRConfig
        
        # Load ChatR config
        config = ChatRConfig.load_config()
        config.setup_directories()
        
        # Create MCP FastAPI app
        mcp_app = create_mcp_server(config)
        
        console.print("✅ MCP server configured successfully")
        console.print("\n📋 Available endpoints:")
        console.print(f"   • GET  http://{host}:{port}/mcp/tools")
        console.print(f"   • POST http://{host}:{port}/mcp/execute") 
        console.print(f"   • GET  http://{host}:{port}/mcp/health")
        console.print(f"\n🔗 Integration guide: chatr mcp --help")
        
        # Start server
        uvicorn.run(
            mcp_app,
            host=host,
            port=port,
            log_level=log_level.lower()
        )
        
    except ImportError:
        console.print("[red]Error: FastAPI/Uvicorn not installed. Install with: pip install fastapi uvicorn[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]MCP server error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
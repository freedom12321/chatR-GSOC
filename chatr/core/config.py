"""Configuration management for ChatR."""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import json


class ChatRConfig(BaseModel):
    """ChatR configuration settings."""
    
    # LLM settings
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama server host")
    ollama_model: str = Field(default="llama3.2:3b", description="Default Ollama model")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", description="Embedding model for RAG")
    
    # RAG settings
    max_retrieval_docs: int = Field(default=10, description="Max documents to retrieve")
    chunk_size: int = Field(default=1000, description="Document chunk size")
    chunk_overlap: int = Field(default=200, description="Chunk overlap size")
    similarity_threshold: float = Field(default=0.7, description="Minimum similarity for retrieval")
    
    # R execution settings
    r_timeout: int = Field(default=30, description="R execution timeout in seconds")
    max_output_lines: int = Field(default=100, description="Max lines of R output to capture")
    sandbox_enabled: bool = Field(default=True, description="Enable sandboxed R execution")
    
    # Cache settings
    cache_dir: Path = Field(default_factory=lambda: Path.home() / ".chatr" / "cache")
    index_dir: Path = Field(default_factory=lambda: Path.home() / ".chatr" / "index")
    max_cache_size_mb: int = Field(default=500, description="Max cache size in MB")
    
    # CRAN settings
    cran_mirror: str = Field(default="https://cran.r-project.org", description="CRAN mirror URL")
    r_universe_api: str = Field(default="https://r-universe.dev/api", description="R-universe API URL")
    update_interval_hours: int = Field(default=24, description="Package metadata update interval")
    
    # External data sources settings
    github_token: Optional[str] = Field(default=None, description="GitHub token for API access")
    enable_external_data: bool = Field(default=True, description="Enable external data sources")
    external_update_interval_hours: int = Field(default=6, description="External data update interval")
    max_external_docs_per_source: int = Field(default=50, description="Max documents per external source")
    
    class Config:
        env_prefix = "CHATR_"
        case_sensitive = False
    
    @classmethod
    def load_config(cls, config_path: Optional[Path] = None) -> "ChatRConfig":
        """Load configuration from file or environment."""
        if config_path is None:
            config_path = Path.home() / ".chatr" / "config.json"
        
        # Load from file if exists
        config_data = {}
        if config_path.exists():
            with open(config_path) as f:
                config_data = json.load(f)
        
        # Override with environment variables
        env_vars = {k.replace("CHATR_", "").lower(): v 
                   for k, v in os.environ.items() 
                   if k.startswith("CHATR_")}
        config_data.update(env_vars)
        
        return cls(**config_data)
    
    def save_config(self, config_path: Optional[Path] = None) -> None:
        """Save configuration to file."""
        if config_path is None:
            config_path = Path.home() / ".chatr" / "config.json"
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(self.model_dump(), f, indent=2, default=str)
    
    def setup_directories(self) -> None:
        """Create necessary directories."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)
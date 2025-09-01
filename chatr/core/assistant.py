"""Main ChatR assistant that coordinates all components."""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from .config import ChatRConfig
from ..rag.retriever import HybridRetriever, Document
from ..rag.indexer import RDocumentationIndexer
from ..rag.orchestrator import EnhancedRAGSystem
from ..llm.ollama_client import ChatRLLMClient
from ..r_integration.executor import SecureRExecutor
from ..data_analysis.data_inspector import SmartDataAnalysisAssistant

logger = logging.getLogger(__name__)


class ChatRAssistant:
    """Main ChatR assistant coordinating all components."""
    
    def __init__(self, config: ChatRConfig):
        self.config = config
        
        # Initialize Enhanced RAG System with external data support
        github_token = config.github_token if config.enable_external_data else None
        self.enhanced_rag = EnhancedRAGSystem(
            cache_dir=config.cache_dir,
            index_dir=config.index_dir,
            ollama_host=config.ollama_host,
            ollama_model=config.ollama_model,
            github_token=github_token
        )
        
        # Keep individual components for backward compatibility
        self.retriever = self.enhanced_rag.retriever
        self.indexer = self.enhanced_rag.indexer
        self.llm_client = self.enhanced_rag.llm_client
        
        self.r_executor = SecureRExecutor(
            timeout=config.r_timeout,
            max_output_lines=config.max_output_lines,
            sandbox_enabled=config.sandbox_enabled
        )
        
        # Initialize Smart Data Analysis Assistant
        self.data_assistant = SmartDataAnalysisAssistant(
            self.r_executor,
            self.llm_client
        )
        
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize the assistant (one-time setup)."""
        if self._initialized:
            return
            
        logger.info("Initializing ChatR Assistant with Enhanced RAG...")
        
        try:
            # Phase 1: Smart initialization with model warming
            self._initialize_phase1()
            
            # Initialize Enhanced RAG System
            self.enhanced_rag.initialize()
            
            self._initialized = True
            logger.info("ChatR Assistant with Enhanced RAG initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChatR Assistant: {e}")
            raise
    
    def _initialize_phase1(self) -> None:
        """Phase 1 initialization: Fast setup with essential coverage."""
        logger.info("Starting Phase 1 initialization...")
        
        # 1. Check if we have essential index cached
        essential_cache_file = self.config.index_dir / "essential_index.json"
        
        if not essential_cache_file.exists():
            logger.info("Building essential R index (one-time setup)...")
            self._build_essential_index()
        else:
            logger.info("Essential R index found, skipping build")
        
        # 2. Start model warming in background
        if not self.llm_client.is_model_warm():
            logger.info("Starting background model warming...")
            self.llm_client.warm_model(background=True)
        else:
            logger.info("Model is already warm")
    
    def _build_essential_index(self) -> None:
        """Build the essential R documentation index."""
        try:
            # Use the indexer to build essential documentation
            indexer = RDocumentationIndexer(self.config.cache_dir)
            documents = indexer.build_essential_index()
            
            # Save to cache for future use
            essential_cache_file = self.config.index_dir / "essential_index.json" 
            essential_cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(essential_cache_file, 'w') as f:
                import json
                import time
                json.dump({
                    'documents': len(documents),
                    'timestamp': time.time(),
                    'status': 'complete'
                }, f)
            
            logger.info(f"Essential index built: {len(documents)} functions indexed")
            
        except Exception as e:
            logger.error(f"Failed to build essential index: {e}")
            # Don't fail completely - continue with available data
    
    def process_query(self, user_query: str) -> str:
        """Process a user query and return a response."""
        
        if not self._initialized:
            self.initialize()
        
        logger.info(f"Processing query: {user_query[:100]}...")
        
        try:
            # Determine if query needs advanced processing
            use_advanced = self._should_use_advanced_processing(user_query)
            
            if use_advanced:
                # Use Enhanced RAG with multi-hop retrieval and orchestration
                logger.info("Using enhanced RAG processing")
                response = self.enhanced_rag.query(user_query, use_advanced_processing=True)
            else:
                # Use simple processing for basic queries
                logger.info("Using simple RAG processing")
                response = self.enhanced_rag.query(user_query, use_advanced_processing=False)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return f"I encountered an error processing your query: {e}"
    
    def process_code_analysis(self, code: str) -> Dict[str, Any]:
        """Analyze R code and provide insights."""
        return self.llm_client.analyze_r_code(code)
    
    def help_with_function(self, function_name: str, package: str = "") -> str:
        """Get help with a specific R function."""
        
        # Try to get help from R directly
        help_result = self.r_executor.execute_help(function_name)
        
        # Build query for additional context
        query = f"R function {function_name}"
        if package:
            query += f" from package {package}"
        
        # Get relevant documentation
        retrieved = self.retriever.retrieve(query, top_k=3)
        context_docs = [doc.content for doc, _ in retrieved]
        
        # Combine help result with LLM explanation
        help_prompt = f"""
The user wants help with the R function '{function_name}'.

R help output:
{help_result.stdout if help_result.success else "Help not available"}

Please provide a clear, practical explanation including:
1. What the function does
2. How to use it (with examples)
3. Common use cases
4. Related functions
        """
        
        return self.llm_client.generate_response(
            help_prompt, 
            context_docs=context_docs
        )
    
    def search_packages(self, query: str) -> List[Dict[str, Any]]:
        """Search for R packages."""
        return self.indexer.search_packages(query)
    
    def explain_error(self, error_message: str, code: str = "") -> str:
        """Explain an R error and suggest fixes."""
        
        error_prompt = f"""
The user encountered this R error:
{error_message}

{f"In this code:\n```r\n{code}\n```" if code else ""}

Please:
1. Explain what this error means
2. Identify the likely cause
3. Suggest how to fix it
4. Provide a corrected code example if possible
        """
        
        # Get relevant error documentation
        retrieved = self.retriever.retrieve(f"R error {error_message}", top_k=3)
        context_docs = [doc.content for doc, _ in retrieved]
        
        return self.llm_client.generate_response(
            error_prompt, 
            context_docs=context_docs,
            execute_code=True
        )
    
    def analyze_my_data(self, dataset_name: str = None, user_goal: str = "") -> str:
        """Analyze user's data and provide intelligent analysis plan."""
        if not self._initialized:
            self.initialize()
        
        return self.data_assistant.analyze_my_data(dataset_name, user_goal)
    
    def quick_data_summary(self, dataset_name: str) -> str:
        """Provide a quick summary of a dataset."""
        if not self._initialized:
            self.initialize()
        
        return self.data_assistant.quick_data_summary(dataset_name)
    
    def get_environment_data(self) -> Dict[str, Any]:
        """Get information about data objects in the R environment."""
        if not self._initialized:
            self.initialize()
        
        return self.data_assistant.data_inspector.get_environment_data()
    
    def _analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze query to determine processing strategy."""
        
        query_lower = query.lower()
        
        # Keywords that suggest documentation lookup is needed
        doc_keywords = ['function', 'package', 'how to', 'what is', 'documentation', 'help']
        needs_docs = any(keyword in query_lower for keyword in doc_keywords)
        
        # Keywords that suggest code execution might be helpful
        exec_keywords = ['example', 'show me', 'run', 'execute', 'output', 'result']
        execute_code = any(keyword in query_lower for keyword in exec_keywords)
        
        # Default to showing examples for most queries
        if not execute_code and ('?' in query or 'how' in query_lower):
            execute_code = True
        
        return {
            'needs_docs': needs_docs,
            'execute_code': execute_code,
            'query_type': self._classify_query_type(query)
        }
    
    def _classify_query_type(self, query: str) -> str:
        """Classify the type of query."""
        
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['error', 'wrong', 'broken', 'fail']):
            return 'error_help'
        elif any(word in query_lower for word in ['function', 'help', '?']):
            return 'function_help'
        elif any(word in query_lower for word in ['package', 'library', 'install']):
            return 'package_help'
        elif any(word in query_lower for word in ['how to', 'tutorial', 'example']):
            return 'tutorial'
        else:
            return 'general'
    
    def _should_use_advanced_processing(self, user_query: str) -> bool:
        """Determine if a query should use advanced multi-hop processing."""
        query_lower = user_query.lower()
        
        # Use advanced processing for complex queries
        advanced_indicators = [
            # Multi-step workflows
            'how do i' in query_lower and len(user_query.split()) > 6,
            'step by step' in query_lower,
            'workflow' in query_lower,
            'complete guide' in query_lower,
            'comprehensive' in query_lower,
            
            # Multiple concepts
            ' and ' in query_lower and any(concept in query_lower for concept in 
                ['regression', 'plot', 'analysis', 'model', 'test']),
            
            # Assumption checking (complex analytical workflows)
            'assumption' in query_lower,
            'check' in query_lower and any(word in query_lower for word in 
                ['assumption', 'diagnostic', 'validation']),
            
            # Complex statistical procedures
            'linear regression' in query_lower and any(word in query_lower for word in 
                ['assumption', 'diagnostic', 'check', 'validate']),
            
            # Package recommendations
            'what package' in query_lower,
            'which package' in query_lower,
            'recommend' in query_lower and 'package' in query_lower,
            
            # Comparison requests
            'compare' in query_lower,
            'difference between' in query_lower,
            'vs' in query_lower or 'versus' in query_lower,
        ]
        
        return any(advanced_indicators)
    
    def _has_existing_index(self) -> bool:
        """Check if we have an existing document index."""
        bm25_index = self.config.index_dir / "bm25_index.pkl"
        docs_file = self.config.index_dir / "documents.pkl"
        return bm25_index.exists() and docs_file.exists()
    
    def _build_initial_index(self) -> None:
        """Build initial documentation index."""
        
        logger.info("Building initial index with base R documentation...")
        
        # Start with base R functions
        base_docs = self.indexer.index_base_r()
        
        # Add some popular packages
        popular_packages = ['ggplot2', 'dplyr', 'tidyr', 'readr', 'stringr']
        package_docs = self.indexer.create_documents_from_packages(popular_packages)
        
        all_docs = base_docs + package_docs
        
        if all_docs:
            self.retriever.add_documents(all_docs)
            logger.info(f"Built initial index with {len(all_docs)} documents")
        else:
            logger.warning("No documents added to initial index")
    
    def update_index(self, packages: Optional[List[str]] = None) -> None:
        """Update the documentation index with new packages."""
        
        if packages:
            logger.info(f"Updating index with packages: {packages}")
            new_docs = self.indexer.create_documents_from_packages(packages)
            
            if new_docs:
                self.retriever.add_documents(new_docs)
                logger.info(f"Added {len(new_docs)} new documents to index")
    
    def generate_advanced_code(self, query: str, mode: str = "interactive", 
                              environment_context: str = "") -> Dict[str, Any]:
        """Generate advanced R code with full context awareness."""
        
        logger.info(f"Advanced code generation request: {query[:100]}... (mode: {mode})")
        
        # Get relevant documentation
        retrieved = self.retriever.retrieve(query, top_k=5)
        context_docs = [doc.content for doc, _ in retrieved]
        
        # Build comprehensive prompt based on mode
        if mode == "script":
            code_prompt = self._build_script_generation_prompt(query, environment_context, context_docs)
        else:
            code_prompt = self._build_interactive_code_prompt(query, environment_context, context_docs)
        
        try:
            # Generate the response
            response = self.llm_client.generate_response(
                code_prompt,
                context_docs=context_docs,
                execute_code=False  # We handle execution separately
            )
            
            # Extract code blocks from response
            generated_code = self._extract_code_blocks(response)
            
            return {
                'response': response,
                'code': generated_code,
                'explanation': self._extract_explanation(response),
                'mode': mode
            }
            
        except Exception as e:
            logger.error(f"Error in advanced code generation: {e}")
            return {
                'response': f"Sorry, I encountered an error generating code: {e}",
                'code': None,
                'explanation': None,
                'mode': mode
            }
    
    def _build_interactive_code_prompt(self, query: str, env_context: str, context_docs: List[str]) -> str:
        """Build prompt for interactive code generation."""
        
        return f"""
You are an expert R programmer helping a user write R code interactively. The user has asked:

"{query}"

Current R Environment:
{env_context if env_context else "No objects in environment"}

Please provide:

1. **Complete, runnable R code** that accomplishes exactly what they asked for
2. **Clear explanation** of what each part does  
3. **Practical tips** and best practices
4. **Expected output** description

Requirements:
- Write production-quality R code with proper error handling
- Include comments explaining key steps
- Use appropriate packages (check if they need to be loaded)
- Consider the user's current environment and data
- Make code that can be copied and run immediately

Format your response with clear sections:
- Explanation of approach
- Complete R code in ```r code blocks
- Expected results
- Additional tips

Be specific about the actual data and objects the user has available.
"""

    def _build_script_generation_prompt(self, query: str, env_context: str, context_docs: List[str]) -> str:
        """Build prompt for complete script generation."""
        
        return f"""
You are an expert R programmer tasked with creating a complete, professional R analysis script.

Task: {query}

Current R Environment:
{env_context if env_context else "Starting with clean environment"}

Create a comprehensive R script that:

1. **Loads all necessary packages** with proper installation checks
2. **Includes data loading/preparation** sections
3. **Has complete analysis workflow** from start to finish  
4. **Includes proper error handling** and validation
5. **Generates meaningful outputs** (plots, tables, results)
6. **Has professional documentation** and comments
7. **Follows R best practices** and style guidelines

Structure the script with clear sections:
- Setup and package loading
- Data import and preparation  
- Exploratory data analysis
- Main analysis
- Results and visualization
- Export/save results

Make this a script someone could run from start to finish to accomplish the full analysis task.
Include detailed comments explaining each section and decision.

Provide the complete script in ```r code blocks with clear section headers.
"""

    def _extract_code_blocks(self, response: str) -> str:
        """Extract R code blocks from LLM response."""
        
        import re
        
        # Find all R code blocks
        code_pattern = r'```r\n(.*?)\n```'
        matches = re.findall(code_pattern, response, re.DOTALL)
        
        if matches:
            # Combine all code blocks
            return '\n\n'.join(matches)
        
        # Fallback: look for any code blocks
        general_pattern = r'```\n(.*?)\n```'
        matches = re.findall(general_pattern, response, re.DOTALL)
        
        if matches:
            return '\n\n'.join(matches)
        
        return None
    
    def _extract_explanation(self, response: str) -> str:
        """Extract explanation text (non-code) from response."""
        
        import re
        
        # Remove code blocks to get just explanation
        explanation = re.sub(r'```r.*?```', '', response, flags=re.DOTALL)
        explanation = re.sub(r'```.*?```', '', explanation, flags=re.DOTALL)
        
        # Clean up extra whitespace
        explanation = re.sub(r'\n\s*\n\s*\n', '\n\n', explanation.strip())
        
        return explanation if explanation else None

    def get_status(self) -> Dict[str, Any]:
        """Get assistant status information."""
        
        return {
            'initialized': self._initialized,
            'config': {
                'ollama_host': self.config.ollama_host,
                'model': self.config.ollama_model,
                'cache_dir': str(self.config.cache_dir),
                'index_dir': str(self.config.index_dir)
            },
            'documents_indexed': len(self.retriever.documents),
            'r_available': True  # We check this in executor init
        }
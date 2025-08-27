"""Advanced RAG orchestration with query decomposition and multi-hop retrieval."""

import json
import logging
import os
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Fix tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from .retriever import HybridRetriever, Document
from .indexer import RDocumentationIndexer
from .external_sources import ExternalDataManager
from ..llm.ollama_client import ChatRLLMClient

logger = logging.getLogger(__name__)


class QueryDecomposer:
    """Decomposes complex queries into sub-questions for multi-hop retrieval."""
    
    def __init__(self, llm_client: ChatRLLMClient):
        self.llm_client = llm_client
    
    def decompose_query(self, user_query: str) -> List[Dict[str, Any]]:
        """Break down a complex query into specific sub-questions."""
        
        decomposition_prompt = f"""
You are a query analysis expert for R programming assistance. Break down this user question into specific sub-questions that need to be answered to provide a complete response.

User Question: "{user_query}"

For each sub-question, provide:
1. The specific question to research
2. The type of information needed (package, function, concept, example, etc.)
3. The priority (1=critical, 2=important, 3=helpful)

Format your response as a JSON array of objects with keys: "question", "type", "priority"

Example:
[
  {{"question": "What packages are available for linear regression?", "type": "package", "priority": 1}},
  {{"question": "How to use lm() function?", "type": "function", "priority": 1}},
  {{"question": "How to check linear regression assumptions?", "type": "concept", "priority": 2}}
]

Sub-questions:
"""
        
        try:
            response = self.llm_client.generate_response(
                decomposition_prompt, 
                execute_code=False
            )
            
            # Extract JSON from response
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                sub_questions = json.loads(json_str)
                
                # Sort by priority
                sub_questions.sort(key=lambda x: x.get('priority', 3))
                
                return sub_questions
            else:
                # Fallback: create basic decomposition
                return self._fallback_decomposition(user_query)
                
        except Exception as e:
            logger.error(f"Error decomposing query: {e}")
            return self._fallback_decomposition(user_query)
    
    def _fallback_decomposition(self, user_query: str) -> List[Dict[str, Any]]:
        """Fallback decomposition based on keywords."""
        query_lower = user_query.lower()
        sub_questions = []
        
        # Basic decomposition rules
        if 'linear regression' in query_lower or 'lm(' in query_lower:
            sub_questions.extend([
                {"question": "How to perform linear regression in R?", "type": "function", "priority": 1},
                {"question": "What packages are needed for linear regression?", "type": "package", "priority": 2},
                {"question": "How to check linear regression assumptions?", "type": "concept", "priority": 2}
            ])
        
        if 'plot' in query_lower or 'visualization' in query_lower:
            sub_questions.extend([
                {"question": "How to create plots in R?", "type": "function", "priority": 1},
                {"question": "What visualization packages are available?", "type": "package", "priority": 2}
            ])
        
        if 'data' in query_lower and any(word in query_lower for word in ['import', 'read', 'load']):
            sub_questions.extend([
                {"question": "How to read data in R?", "type": "function", "priority": 1},
                {"question": "What data import packages are available?", "type": "package", "priority": 2}
            ])
        
        # If no specific patterns, create a general question
        if not sub_questions:
            sub_questions.append({
                "question": user_query,
                "type": "general",
                "priority": 1
            })
        
        return sub_questions


class MultiHopRetriever:
    """Performs multi-hop retrieval based on decomposed queries."""
    
    def __init__(self, retriever: HybridRetriever, llm_client: ChatRLLMClient):
        self.retriever = retriever
        self.llm_client = llm_client
    
    def multi_hop_retrieve(
        self, 
        sub_questions: List[Dict[str, Any]], 
        max_docs_per_question: int = 5
    ) -> Dict[str, List[Tuple[Document, float]]]:
        """Perform multi-hop retrieval for sub-questions."""
        
        retrieval_results = {}
        context_from_previous = []
        
        for i, sub_q in enumerate(sub_questions):
            question = sub_q['question']
            question_type = sub_q['type']
            
            logger.info(f"Multi-hop retrieval {i+1}/{len(sub_questions)}: {question}")
            
            # Enhance query with context from previous retrievals
            enhanced_query = self._enhance_query_with_context(
                question, 
                context_from_previous,
                question_type
            )
            
            # Perform targeted retrieval
            results = self._targeted_retrieve(
                enhanced_query, 
                question_type, 
                max_docs_per_question
            )
            
            retrieval_results[question] = results
            
            # Extract key information for next queries
            if results:
                context_info = self._extract_context_info(results)
                context_from_previous.extend(context_info)
        
        return retrieval_results
    
    def _enhance_query_with_context(
        self, 
        question: str, 
        context: List[str], 
        question_type: str
    ) -> str:
        """Enhance query with context from previous retrievals."""
        
        if not context:
            return question
        
        # Select relevant context based on question type
        relevant_context = []
        for ctx in context[-3:]:  # Use last 3 pieces of context
            if question_type == 'package' and any(word in ctx.lower() for word in ['package', 'library']):
                relevant_context.append(ctx)
            elif question_type == 'function' and any(word in ctx.lower() for word in ['function', 'method']):
                relevant_context.append(ctx)
            elif question_type == 'concept':
                relevant_context.append(ctx)
        
        if relevant_context:
            enhanced_query = f"{question} (considering: {', '.join(relevant_context)})"
            return enhanced_query
        
        return question
    
    def _targeted_retrieve(
        self, 
        query: str, 
        question_type: str, 
        max_docs: int
    ) -> List[Tuple[Document, float]]:
        """Perform targeted retrieval based on question type."""
        
        # Retrieve documents
        results = self.retriever.retrieve(query, top_k=max_docs * 2)
        
        # Filter and re-rank based on question type
        filtered_results = []
        
        for doc, score in results:
            doc_type = doc.metadata.get('type', '')
            doc_task = doc.metadata.get('task', '')
            
            # Type-based filtering
            type_bonus = 0
            if question_type == 'package' and doc_type in ['package_description', 'task_view']:
                type_bonus = 0.2
            elif question_type == 'function' and doc_type in ['man_page', 'function']:
                type_bonus = 0.2
            elif question_type == 'concept' and doc_type in ['vignette', 'r_extensions']:
                type_bonus = 0.15
            elif question_type == 'example' and doc_type in ['vignette', 'man_page']:
                type_bonus = 0.1
            
            # Task relevance bonus
            if question_type in ['function', 'concept'] and doc_task in ['statistical_modeling', 'data_visualization']:
                type_bonus += 0.1
            
            adjusted_score = score + type_bonus
            filtered_results.append((doc, adjusted_score))
        
        # Re-sort by adjusted score and return top results
        filtered_results.sort(key=lambda x: x[1], reverse=True)
        return filtered_results[:max_docs]
    
    def _extract_context_info(self, results: List[Tuple[Document, float]]) -> List[str]:
        """Extract key information from retrieval results for context."""
        context_info = []
        
        for doc, score in results[:2]:  # Use top 2 results
            # Extract package names
            if 'package' in doc.metadata:
                package_name = doc.metadata['package']
                context_info.append(f"package:{package_name}")
            
            # Extract function names
            if 'function' in doc.metadata:
                function_name = doc.metadata['function']
                context_info.append(f"function:{function_name}")
            
            # Extract task categories
            if 'task' in doc.metadata:
                task = doc.metadata['task']
                context_info.append(f"task:{task}")
        
        return context_info


class WorkflowOrchestrator:
    """Orchestrates the complete RAG workflow with multi-step reasoning."""
    
    def __init__(
        self, 
        retriever: HybridRetriever, 
        indexer: RDocumentationIndexer,
        llm_client: ChatRLLMClient,
        external_data: Optional[ExternalDataManager] = None
    ):
        self.retriever = retriever
        self.indexer = indexer
        self.llm_client = llm_client
        self.external_data = external_data
        self.query_decomposer = QueryDecomposer(llm_client)
        self.multi_hop_retriever = MultiHopRetriever(retriever, llm_client)
    
    def process_complex_query(self, user_query: str) -> str:
        """Process a complex query with multi-hop reasoning and workflow generation."""
        
        logger.info(f"Processing complex query: {user_query}")
        
        # Step 1: Query decomposition
        sub_questions = self.query_decomposer.decompose_query(user_query)
        logger.info(f"Decomposed into {len(sub_questions)} sub-questions")
        
        # Step 2: Multi-hop retrieval
        retrieval_results = self.multi_hop_retriever.multi_hop_retrieve(sub_questions)
        
        # Step 3: Workflow generation and synthesis
        final_response = self._synthesize_workflow(
            user_query, 
            sub_questions, 
            retrieval_results
        )
        
        # Step 4: Validation (optional)
        validated_response = self._validate_workflow(final_response)
        
        return validated_response
    
    def _synthesize_workflow(
        self, 
        user_query: str, 
        sub_questions: List[Dict[str, Any]], 
        retrieval_results: Dict[str, List[Tuple[Document, float]]]
    ) -> str:
        """Synthesize retrieved information into a complete workflow."""
        
        # Prepare context from all retrievals
        all_context = []
        for question, results in retrieval_results.items():
            for doc, score in results[:3]:  # Top 3 per question
                all_context.append(doc.content)
        
        # Create synthesis prompt
        synthesis_prompt = f"""
You are an expert R programming assistant. Based on the retrieved documentation, create a comprehensive, step-by-step workflow to answer the user's question.

Original Question: "{user_query}"

Sub-questions analyzed:
{self._format_sub_questions(sub_questions)}

Retrieved Information:
{chr(10).join(all_context[:10])}  # Limit context length

Instructions:
1. Identify multiple potential solutions (e.g., base R vs. tidyverse approaches)
2. Sequence the necessary packages and functions in logical order
3. Provide clear explanations for why each step is required
4. Include working code examples with expected outputs
5. Mention any important assumptions or prerequisites
6. Structure your response as a complete, actionable workflow

Your response should be practical, accurate, and include executable R code.
"""
        
        return self.llm_client.generate_response(
            synthesis_prompt,
            context_docs=all_context[:5],  # Provide top context
            execute_code=True
        )
    
    def _validate_workflow(self, workflow_response: str) -> str:
        """Validate the generated workflow by checking code executability."""
        
        # Extract R code blocks from the response
        import re
        code_blocks = re.findall(r'```r\n(.*?)\n```', workflow_response, re.DOTALL)
        
        validation_notes = []
        
        for i, code_block in enumerate(code_blocks):
            # Skip very simple code blocks
            if len(code_block.strip().split('\n')) < 2:
                continue
            
            # Try to validate the code structure
            validation_result = self._validate_code_block(code_block)
            if validation_result:
                validation_notes.append(f"Code block {i+1}: {validation_result}")
        
        # Append validation notes if any issues found
        if validation_notes:
            workflow_response += "\n\n**Validation Notes:**\n" + "\n".join(validation_notes)
        
        return workflow_response
    
    def _validate_code_block(self, code: str) -> Optional[str]:
        """Validate a code block for common issues."""
        
        code_lower = code.lower()
        
        # Check for common issues
        if 'library(' in code_lower and 'install.packages(' not in code_lower:
            # Check if packages are commonly available
            uncommon_packages = ['obscurepackage', 'rarepkg']
            for pkg in uncommon_packages:
                if pkg in code_lower:
                    return f"Package '{pkg}' may not be widely available"
        
        # Check for potentially dangerous operations
        dangerous_patterns = ['system(', 'unlink(', 'file.remove(']
        for pattern in dangerous_patterns:
            if pattern in code_lower:
                return f"Contains potentially dangerous operation: {pattern}"
        
        return None
    
    def _format_sub_questions(self, sub_questions: List[Dict[str, Any]]) -> str:
        """Format sub-questions for display."""
        formatted = []
        for i, sq in enumerate(sub_questions, 1):
            formatted.append(f"{i}. {sq['question']} (type: {sq['type']}, priority: {sq['priority']})")
        return "\n".join(formatted)


class EnhancedRAGSystem:
    """Complete enhanced RAG system with all advanced features."""
    
    def __init__(
        self, 
        cache_dir: Path, 
        index_dir: Path,
        ollama_host: str = "http://localhost:11434",
        ollama_model: str = "llama3.2:3b",
        github_token: Optional[str] = None
    ):
        # Initialize components
        self.indexer = RDocumentationIndexer(cache_dir)
        self.retriever = HybridRetriever(index_dir)
        self.llm_client = ChatRLLMClient(ollama_host, ollama_model)
        
        # Initialize external data manager
        self.external_data = ExternalDataManager(
            cache_dir / "external", 
            github_token=github_token
        )
        
        # Initialize orchestrator
        self.orchestrator = WorkflowOrchestrator(
            self.retriever, 
            self.indexer, 
            self.llm_client,
            self.external_data
        )
        
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize the enhanced RAG system."""
        if self._initialized:
            return
        
        logger.info("Initializing Enhanced RAG System...")
        
        # Initialize retriever
        self.retriever.initialize()
        
        # Check if we need to build comprehensive index
        if not self._has_comprehensive_index():
            self._build_comprehensive_index()
        
        # Initialize external data sources
        self._initialize_external_data()
        
        # Start scheduled updates for external data
        if self.external_data:
            self.external_data.schedule_updates()
        
        self._initialized = True
        logger.info("Enhanced RAG System with external data sources initialized successfully")
    
    def _has_comprehensive_index(self) -> bool:
        """Check if we have a comprehensive index with all documentation types."""
        # Check for existence of different documentation caches
        required_caches = [
            self.indexer.man_pages_cache,
            self.indexer.vignettes_cache,
            self.indexer.task_views_cache
        ]
        
        return all(cache_dir.exists() and any(cache_dir.iterdir()) for cache_dir in required_caches)
    
    def _build_comprehensive_index(self) -> None:
        """Build a comprehensive index with all documentation types."""
        logger.info("Building comprehensive documentation index...")
        
        all_documents = []
        successful_extractions = 0
        total_attempts = 0
        
        # 1. Extract man pages for key packages (with graceful degradation)
        key_packages = ['stats', 'graphics', 'utils']  # Start with essential packages only
        for package in key_packages:
            total_attempts += 1
            try:
                man_docs = self.indexer.extract_man_pages(package)
                if man_docs:
                    all_documents.extend(man_docs)
                    successful_extractions += 1
                    logger.info(f"Added {len(man_docs)} man pages for {package}")
                else:
                    logger.info(f"No man pages extracted for {package} (package may not be available)")
            except Exception as e:
                logger.warning(f"Failed to extract man pages for {package}: {e}")
        
        # 2. Skip vignettes for now if they cause issues
        # Can be enabled later when extraction is more stable
        logger.info("Skipping vignette extraction for stability")
        
        # 3. Skip CRAN task views for now
        logger.info("Skipping CRAN task views extraction for stability")
        
        # 4. Skip R Extensions guide for now  
        logger.info("Skipping R Extensions guide extraction for stability")
        
        # 5. Always add base R documentation (this should work)
        try:
            base_docs = self.indexer.index_base_r()
            all_documents.extend(base_docs)
            logger.info(f"Added {len(base_docs)} base R function documents")
        except Exception as e:
            logger.warning(f"Failed to add base R documentation: {e}")
        
        # Add all documents to retriever
        if all_documents:
            try:
                self.retriever.add_documents(all_documents)
                logger.info(f"Built comprehensive index with {len(all_documents)} documents ({successful_extractions}/{total_attempts} package extractions successful)")
            except Exception as e:
                logger.error(f"Failed to add documents to retriever: {e}")
                # Create minimal index with just base docs
                if base_docs:
                    try:
                        self.retriever.add_documents(base_docs)
                        logger.info(f"Created minimal index with {len(base_docs)} base documents")
                    except Exception as e2:
                        logger.error(f"Failed to create even minimal index: {e2}")
        else:
            logger.warning("No documents were successfully extracted - using minimal base documentation")
            # Create some basic documents manually
            self._create_minimal_index()
    
    def _create_minimal_index(self) -> None:
        """Create a minimal index with essential R documentation when extraction fails."""
        logger.info("Creating minimal fallback index...")
        
        # Create basic documents for essential R functions
        essential_docs = [
            {
                'title': 'Linear Models - lm() function',
                'content': '''
lm() - Fitting Linear Models

Description:
lm is used to fit linear models. It can be used to carry out regression, 
single stratum analysis of variance and analysis of covariance.

Usage:
lm(formula, data, subset, weights, na.action, method = "qr", 
   model = TRUE, x = FALSE, y = FALSE, qr = TRUE, singular.ok = TRUE, 
   contrasts = NULL, offset, ...)

Arguments:
formula: an object of class "formula" (or one that can be coerced to that class)
data: an optional data frame, list or environment containing the variables in the model
subset: an optional vector specifying a subset of observations to be used
weights: an optional vector of weights to be used in the fitting process

Examples:
# Simple linear regression
model <- lm(mpg ~ wt, data = mtcars)
summary(model)

# Multiple regression
model <- lm(mpg ~ wt + hp + cyl, data = mtcars)
''',
                'metadata': {
                    'type': 'function',
                    'package': 'stats',
                    'function': 'lm',
                    'task': 'statistical_modeling',
                    'concept': 'regression, linear, model'
                }
            },
            {
                'title': 'Data Visualization - plot() function',
                'content': '''
plot() - Generic Plotting Function

Description:
Generic function for plotting of R objects. For more details about 
the graphical parameter arguments, see par.

Usage:
plot(x, y, ...)

Arguments:
x, y: the coordinates of points in the plot

Examples:
# Simple scatter plot
plot(mtcars$wt, mtcars$mpg)

# With labels
plot(mtcars$wt, mtcars$mpg, 
     xlab = "Weight", ylab = "MPG", 
     main = "Weight vs MPG")
''',
                'metadata': {
                    'type': 'function',
                    'package': 'graphics',
                    'function': 'plot',
                    'task': 'data_visualization',
                    'concept': 'plot, visualization, scatter'
                }
            },
            {
                'title': 'Linear Regression Assumptions and Diagnostics',
                'content': '''
Checking Linear Regression Assumptions

Linear regression relies on several key assumptions:

1. Linearity: The relationship between predictors and response is linear
2. Independence: Observations are independent
3. Homoscedasticity: Constant variance of residuals
4. Normality: Residuals are normally distributed

Diagnostic Methods:

# Residual plots
model <- lm(y ~ x, data = mydata)
plot(model)  # Produces 4 diagnostic plots

# Individual diagnostics
residuals <- residuals(model)
fitted_values <- fitted(model)

# Residuals vs Fitted plot
plot(fitted_values, residuals)
abline(h = 0)

# Q-Q plot for normality
qqnorm(residuals)
qqline(residuals)

# Histogram of residuals
hist(residuals)

# Statistical tests
shapiro.test(residuals)  # Normality test
''',
                'metadata': {
                    'type': 'concept',
                    'package': 'stats',
                    'function': 'diagnostics',
                    'task': 'statistical_modeling',
                    'concept': 'regression, assumptions, diagnostics'
                }
            }
        ]
        
        documents = []
        for i, doc_info in enumerate(essential_docs):
            doc = Document(
                content=doc_info['content'],
                metadata=doc_info['metadata'],
                doc_id=f"minimal_{i}"
            )
            documents.append(doc)
        
        try:
            self.retriever.add_documents(documents)
            logger.info(f"Created minimal index with {len(documents)} essential documents")
        except Exception as e:
            logger.error(f"Failed to create minimal index: {e}")
    
    def query(self, user_query: str, use_advanced_processing: bool = True) -> str:
        """Process a user query with optional advanced processing."""
        if not self._initialized:
            self.initialize()
        
        if use_advanced_processing:
            return self.orchestrator.process_complex_query(user_query)
        else:
            # Fallback to simple retrieval
            retrieved = self.retriever.retrieve(user_query, top_k=10)
            context_docs = [doc.content for doc, score in retrieved]
            return self.llm_client.generate_response(
                user_query, 
                context_docs=context_docs, 
                execute_code=True
            )
    
    def _initialize_external_data(self) -> None:
        """Initialize external data sources with initial data."""
        if not self.external_data:
            logger.info("External data manager not available - skipping external data initialization")
            return
        
        logger.info("Initializing external data sources...")
        
        try:
            # Fetch initial CRAN Task Views
            task_view_docs = self.external_data.fetch_cran_task_views_updates()
            if task_view_docs:
                self.retriever.add_documents(task_view_docs)
                logger.info(f"Added {len(task_view_docs)} CRAN Task View documents")
            
            # Fetch initial R Universe data for key organizations
            r_universe_docs = self.external_data.fetch_r_universe_updates()
            if r_universe_docs:
                self.retriever.add_documents(r_universe_docs)
                logger.info(f"Added {len(r_universe_docs)} R Universe package documents")
            
            # Fetch initial community RSS feeds
            community_docs = self.external_data.fetch_community_rss_feeds()
            if community_docs:
                self.retriever.add_documents(community_docs)
                logger.info(f"Added {len(community_docs)} community blog post documents")
            
            # Fetch initial scholarly papers
            scholarly_docs = self.external_data.fetch_scholarly_feeds(
                topics=['R programming', 'data science', 'statistics']
            )
            if scholarly_docs:
                self.retriever.add_documents(scholarly_docs)
                logger.info(f"Added {len(scholarly_docs)} scholarly paper documents")
        
        except Exception as e:
            logger.warning(f"Failed to initialize some external data sources: {e}")
    
    def update_external_data(self) -> Dict[str, int]:
        """Manually trigger updates for all external data sources."""
        if not self.external_data:
            return {"error": "External data manager not available"}
        
        logger.info("Manually updating external data sources...")
        update_counts = {}
        
        try:
            # Update CRAN Task Views
            task_view_docs = self.external_data.fetch_cran_task_views_updates()
            if task_view_docs:
                self.retriever.add_documents(task_view_docs)
                update_counts['cran_task_views'] = len(task_view_docs)
            
            # Update R Universe packages
            r_universe_docs = self.external_data.fetch_r_universe_updates()
            if r_universe_docs:
                self.retriever.add_documents(r_universe_docs)
                update_counts['r_universe'] = len(r_universe_docs)
            
            # Update community feeds
            community_docs = self.external_data.fetch_community_rss_feeds()
            if community_docs:
                self.retriever.add_documents(community_docs)
                update_counts['community_posts'] = len(community_docs)
            
            # Update scholarly papers
            scholarly_docs = self.external_data.fetch_scholarly_feeds()
            if scholarly_docs:
                self.retriever.add_documents(scholarly_docs)
                update_counts['scholarly_papers'] = len(scholarly_docs)
        
        except Exception as e:
            logger.error(f"Error updating external data: {e}")
            update_counts['error'] = str(e)
        
        return update_counts
    
    def search_external_code(self, query: str, language: str = 'r') -> List[Document]:
        """Search for code examples from external sources."""
        if not self.external_data:
            logger.warning("External data manager not available for code search")
            return []
        
        # Search GitHub for code examples
        github_docs = self.external_data.search_github_code(query, language)
        
        # Add to retriever for future queries
        if github_docs:
            self.retriever.add_documents(github_docs)
            logger.info(f"Added {len(github_docs)} GitHub code examples for '{query}'")
        
        return github_docs
    
    def fetch_package_docs_on_demand(self, package_name: str) -> List[Document]:
        """Fetch package documentation on-demand from external sources."""
        if not self.external_data:
            logger.warning("External data manager not available for on-demand package docs")
            return []
        
        # Fetch pkgdown documentation
        pkgdown_docs = self.external_data.fetch_pkgdown_on_demand(package_name)
        
        # Add to retriever
        if pkgdown_docs:
            self.retriever.add_documents(pkgdown_docs)
            logger.info(f"Added {len(pkgdown_docs)} pkgdown documents for {package_name}")
        
        return pkgdown_docs
"""Ollama client for local LLM inference."""

import json
import logging
from typing import Dict, Any, List, Optional, Iterator, Generator
import requests
import ollama
from ollama import Client

from ..r_integration.executor import SecureRExecutor, RExecutionResult

logger = logging.getLogger(__name__)


class ChatRLLMClient:
    """ChatR LLM client with R-specific capabilities."""
    
    def __init__(self, 
                 host: str = "http://localhost:11434",
                 model: str = "llama3.2:3b-instruct"):
        
        self.host = host
        self.model = model
        self.client = Client(host=host)
        self.r_executor = SecureRExecutor()
        
        # Check if Ollama is running
        self._check_ollama_connection()
        
        # Model warming state
        self._model_warmed = False
        self._warming_in_progress = False
        
        # System prompt for R assistance
        self.system_prompt = """You are ChatR, an expert R programming assistant. You help users with:

1. R programming questions and code examples
2. Package recommendations and usage
3. Data analysis workflows
4. Statistical analysis guidance
5. Debugging R code issues

When providing R code:
- Always include clear explanations
- Show expected outputs when relevant
- Mention required packages
- Provide working examples
- Consider edge cases and error handling

You can execute R code to verify results and provide live outputs. Always format R code in ```r code blocks.

Be concise but thorough. Focus on practical, working solutions."""
    
    def _check_ollama_connection(self) -> None:
        """Check if Ollama server is accessible."""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            response.raise_for_status()
            logger.info("Ollama server is accessible")
        except Exception as e:
            raise ConnectionError(f"Cannot connect to Ollama at {self.host}: {e}")
    
    def ensure_model_available(self) -> None:
        """Ensure the specified model is available."""
        try:
            # List available models
            models_response = self.client.list()
            
            # Extract model names properly
            if 'models' in models_response:
                model_names = [model.get('name', '') for model in models_response['models']]
            else:
                model_names = []
            
            if self.model not in model_names:
                logger.info(f"Model {self.model} not found. Attempting to pull...")
                self.client.pull(self.model)
                logger.info(f"Successfully pulled model: {self.model}")
            else:
                logger.info(f"Model {self.model} is available")
                
        except Exception as e:
            logger.error(f"Error checking/pulling model: {e}")
            raise
    
    def warm_model(self, background: bool = False) -> None:
        """Pre-warm the model to reduce first-query latency.
        
        Args:
            background: If True, warm in background thread
        """
        if self._model_warmed or self._warming_in_progress:
            return
            
        if background:
            import asyncio
            import threading
            
            def _warm_background():
                self._warming_in_progress = True
                try:
                    self._perform_warming()
                finally:
                    self._warming_in_progress = False
                    
            thread = threading.Thread(target=_warm_background, daemon=True)
            thread.start()
            logger.info("Model warming started in background")
        else:
            self._perform_warming()
    
    def _perform_warming(self) -> None:
        """Perform the actual model warming."""
        try:
            logger.info(f"Warming model {self.model}...")
            
            # Send a simple query to load model into memory
            warm_query = "Hello, this is a warm-up query."
            
            response = self.client.chat(
                model=self.model,
                messages=[{
                    'role': 'user', 
                    'content': warm_query
                }],
                options={'num_predict': 10}  # Short response for warming
            )
            
            if response and 'message' in response:
                self._model_warmed = True
                logger.info("Model warming completed successfully")
            else:
                logger.warning("Model warming completed but response unclear")
                
        except Exception as e:
            logger.error(f"Model warming failed: {e}")
            
    def is_model_warm(self) -> bool:
        """Check if model is currently warm (loaded in memory)."""
        try:
            # Quick check - if we can get model info quickly, it's likely warm
            import requests
            response = requests.get(f"{self.host}/api/ps", timeout=2)
            
            if response.status_code == 200:
                running_models = response.json()
                model_running = any(
                    model.get('name') == self.model 
                    for model in running_models.get('models', [])
                )
                self._model_warmed = model_running
                return model_running
            return self._model_warmed
            
        except Exception:
            return self._model_warmed
    
    def generate_response(self, 
                         user_query: str, 
                         context_docs: Optional[List[str]] = None,
                         execute_code: bool = True) -> str:
        """Generate a response to user query with optional context."""
        
        # Build the prompt
        prompt_parts = [self.system_prompt]
        
        # Add context from retrieved documents
        if context_docs:
            context_text = "\n\n".join(context_docs)
            prompt_parts.append(f"\nRelevant R documentation:\n{context_text}\n")
        
        # Add user query
        prompt_parts.append(f"\nUser Question: {user_query}")
        
        full_prompt = "\n".join(prompt_parts)
        
        try:
            # Generate response
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "user", "content": full_prompt}
                ],
                stream=False
            )
            
            generated_text = response['message']['content']
            
            # Extract and execute R code if requested
            if execute_code:
                generated_text = self._process_r_code_blocks(generated_text)
            
            return generated_text
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Sorry, I encountered an error: {e}"
    
    def stream_response(self, 
                       user_query: str, 
                       context_docs: Optional[List[str]] = None) -> Generator[str, None, None]:
        """Stream response generation."""
        
        prompt_parts = [self.system_prompt]
        
        if context_docs:
            context_text = "\n\n".join(context_docs)
            prompt_parts.append(f"\nRelevant R documentation:\n{context_text}\n")
        
        prompt_parts.append(f"\nUser Question: {user_query}")
        full_prompt = "\n".join(prompt_parts)
        
        try:
            stream = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "user", "content": full_prompt}
                ],
                stream=True
            )
            
            for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    yield chunk['message']['content']
                    
        except Exception as e:
            yield f"Error: {e}"
    
    def _process_r_code_blocks(self, text: str) -> str:
        """Find R code blocks and execute them, adding results."""
        
        import re
        
        # Find all R code blocks
        r_code_pattern = r'```r\n(.*?)\n```'
        matches = re.finditer(r_code_pattern, text, re.DOTALL)
        
        processed_text = text
        offset = 0
        
        for match in matches:
            r_code = match.group(1)
            start, end = match.span()
            
            # Execute the R code
            result = self.r_executor.execute_code(r_code)
            
            # Create replacement text with execution results
            execution_info = self._format_execution_result(result)
            replacement = f"```r\n{r_code}\n```\n{execution_info}"
            
            # Replace in the text
            processed_text = (processed_text[:start + offset] + 
                            replacement + 
                            processed_text[end + offset:])
            
            # Update offset for next replacement
            offset += len(replacement) - (end - start)
        
        return processed_text
    
    def _format_execution_result(self, result: RExecutionResult) -> str:
        """Format R execution result for display."""
        
        if result.success:
            output_parts = []
            
            if result.stdout.strip():
                output_parts.append(f"**Output:**\n```\n{result.stdout.strip()}\n```")
            
            # Only show stderr if it contains warnings, not errors
            if result.stderr.strip():
                stderr_content = result.stderr.strip()
                # Filter out common non-error messages
                if not any(pattern in stderr_content.lower() for pattern in ['error', 'fatal', 'abort']):
                    output_parts.append(f"**Messages:**\n```\n{stderr_content}\n```")
            
            if not output_parts:
                output_parts.append("*Code executed successfully (no output)*")
            
            return "\n\n".join(output_parts)
        
        else:
            # For errors, provide cleaner formatting
            error_message = result.error_message or 'Code execution failed'
            
            # Clean up common error patterns
            if result.stderr:
                stderr_lines = result.stderr.strip().split('\n')
                # Find the actual error line, skip R infrastructure messages
                actual_error = None
                for line in stderr_lines:
                    if ('Error' in line and 'contrib.url' not in line) or 'trying to use CRAN' in line:
                        actual_error = line.strip()
                        break
                
                if actual_error and 'trying to use CRAN without setting a mirror' in actual_error:
                    return "**Note:** This code requires package installation. ChatR has automatically configured CRAN access."
                elif actual_error:
                    return f"**Error:** {actual_error}"
            
            return f"**Error:** {error_message}"
    
    def analyze_r_code(self, code: str) -> Dict[str, Any]:
        """Analyze R code and provide insights."""
        
        analysis_prompt = f"""
Analyze this R code and provide insights:

```r
{code}
```

Please provide:
1. What this code does (summary)
2. Packages/libraries required
3. Potential issues or improvements
4. Expected output type
5. Suggestions for better practices

Be concise but thorough.
        """
        
        response = self.generate_response(analysis_prompt, execute_code=False)
        
        return {
            'analysis': response,
            'code': code
        }
    
    def suggest_improvements(self, code: str, error_message: str = "") -> str:
        """Suggest improvements for R code that has issues."""
        
        improvement_prompt = f"""
This R code has issues:

```r
{code}
```

{f"Error message: {error_message}" if error_message else ""}

Please provide:
1. What's wrong with the code
2. Corrected version
3. Explanation of the fix
4. Best practices to avoid similar issues

Provide the corrected code in a ```r code block.
        """
        
        return self.generate_response(improvement_prompt, execute_code=True)
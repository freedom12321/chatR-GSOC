"""Secure R code execution system."""

import subprocess
import tempfile
import os
import signal
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)


class RExecutionResult:
    """Result of R code execution."""
    
    def __init__(self, 
                 success: bool, 
                 stdout: str, 
                 stderr: str, 
                 execution_time: float,
                 exit_code: int = 0,
                 error_message: Optional[str] = None):
        self.success = success
        self.stdout = stdout
        self.stderr = stderr
        self.execution_time = execution_time
        self.exit_code = exit_code
        self.error_message = error_message
    
    def __str__(self):
        return f"RExecutionResult(success={self.success}, time={self.execution_time:.2f}s)"


class SecureRExecutor:
    """Secure R code executor with sandboxing and timeouts."""
    
    def __init__(self, 
                 timeout: int = 30,
                 max_output_lines: int = 100,
                 sandbox_enabled: bool = True,
                 temp_dir: Optional[Path] = None):
        
        self.timeout = timeout
        self.max_output_lines = max_output_lines
        self.sandbox_enabled = sandbox_enabled
        self.temp_dir = temp_dir or Path(tempfile.gettempdir()) / "chatr_r_exec"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Session state management
        self.session_workspace = self.temp_dir / "session_workspace.RData"
        self.session_history = []
        
        # Check R availability
        self._check_r_installation()
    
    def _check_r_installation(self) -> None:
        """Check if R is available on the system."""
        try:
            result = subprocess.run(['R', '--version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            if result.returncode == 0:
                logger.info(f"R found: {result.stdout.split()[2]}")
            else:
                raise RuntimeError("R installation check failed")
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
            raise RuntimeError(f"R not found or not working: {e}")
    
    def execute_code(self, 
                    r_code: str, 
                    working_dir: Optional[Path] = None) -> RExecutionResult:
        """Execute R code securely with timeout and sandboxing."""
        
        start_time = time.time()
        
        # Validate code for obvious security issues
        if self.sandbox_enabled and not self._validate_code_safety(r_code):
            return RExecutionResult(
                success=False,
                stdout="",
                stderr="",
                execution_time=0,
                error_message="Code rejected by security validation"
            )
        
        # Prepend setup code to ensure CRAN mirror and basic config
        setup_code = '''
# Set CRAN mirror to avoid "trying to use CRAN without setting a mirror" error
options(repos = c(CRAN = "https://cran.r-project.org"))

# Suppress startup messages
options(warn = -1)

'''
        
        # Add session restoration code if workspace exists
        if self.session_workspace.exists():
            setup_code += f'''
# Load previous session state
tryCatch({{
    load("{self.session_workspace}")
}}, error = function(e) {{
    # If loading fails, continue with fresh environment
}})

'''
        
        # Combine setup with user code and session save
        save_code = f'''

# Save session state for next execution
tryCatch({{
    save.image("{self.session_workspace}")
}}, error = function(e) {{
    # If saving fails, continue
}})
'''
        
        full_code = setup_code + r_code + save_code
        
        # Create temporary script file
        with tempfile.NamedTemporaryFile(mode='w', 
                                       suffix='.R', 
                                       delete=False,
                                       dir=self.temp_dir) as script_file:
            script_file.write(full_code)
            script_path = script_file.name
        
        try:
            # Set up execution environment
            env = os.environ.copy()
            if working_dir:
                env['R_STARTUP_DIR'] = str(working_dir)
            
            # Build R command
            cmd = ['Rscript', '--vanilla', script_path]
            
            # Execute with timeout
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=working_dir,
                    env=env,
                    preexec_fn=os.setsid if os.name == 'posix' else None
                )
                
                # Wait for completion with timeout
                try:
                    stdout, stderr = process.communicate(timeout=self.timeout)
                    exit_code = process.returncode
                    
                except subprocess.TimeoutExpired:
                    # Kill the process group to handle child processes
                    if os.name == 'posix':
                        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    else:
                        process.terminate()
                    
                    try:
                        stdout, stderr = process.communicate(timeout=2)
                    except subprocess.TimeoutExpired:
                        if os.name == 'posix':
                            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                        else:
                            process.kill()
                        stdout, stderr = process.communicate()
                    
                    execution_time = time.time() - start_time
                    return RExecutionResult(
                        success=False,
                        stdout=stdout or "",
                        stderr=stderr or "",
                        execution_time=execution_time,
                        exit_code=-1,
                        error_message=f"Execution timed out after {self.timeout} seconds"
                    )
                
            except Exception as e:
                execution_time = time.time() - start_time
                return RExecutionResult(
                    success=False,
                    stdout="",
                    stderr="",
                    execution_time=execution_time,
                    error_message=f"Execution failed: {e}"
                )
            
            execution_time = time.time() - start_time
            
            # Truncate output if too long
            stdout = self._truncate_output(stdout)
            stderr = self._truncate_output(stderr)
            
            # Determine success
            success = (exit_code == 0)
            
            return RExecutionResult(
                success=success,
                stdout=stdout,
                stderr=stderr,
                execution_time=execution_time,
                exit_code=exit_code
            )
            
        finally:
            # Clean up temporary script
            try:
                os.unlink(script_path)
            except:
                pass
    
    def execute_help(self, topic: str) -> RExecutionResult:
        """Get help for an R topic."""
        help_code = f"""
tryCatch({{
    help_content <- capture.output(help("{topic}"))
    if (length(help_content) == 0) {{
        help_content <- capture.output(help.search("{topic}"))
    }}
    cat(paste(help_content, collapse="\\n"))
}}, error = function(e) {{
    cat("Help not found for:", "{topic}")
}})
        """
        
        return self.execute_code(help_code)
    
    def execute_example(self, function_name: str) -> RExecutionResult:
        """Run examples for an R function."""
        example_code = f"""
tryCatch({{
    example("{function_name}")
}}, error = function(e) {{
    cat("No examples available for:", "{function_name}")
}})
        """
        
        return self.execute_code(example_code)
    
    def check_package(self, package_name: str) -> RExecutionResult:
        """Check if a package is available and get basic info."""
        check_code = f"""
# Check if package is installed
if ("{package_name}" %in% installed.packages()[,"Package"]) {{
    cat("Package '{package_name}' is installed\\n")
    
    # Try to load it
    tryCatch({{
        library("{package_name}", character.only = TRUE)
        cat("Package '{package_name}' loaded successfully\\n")
        
        # Get package info
        desc <- packageDescription("{package_name}")
        cat("Version:", desc$Version, "\\n")
        cat("Title:", desc$Title, "\\n")
        
    }}, error = function(e) {{
        cat("Error loading package:", e$message, "\\n")
    }})
    
}} else {{
    cat("Package '{package_name}' is not installed\\n")
    cat("You can install it with: install.packages('{package_name}')\\n")
}}
        """
        
        return self.execute_code(check_code)
    
    def clear_session(self) -> None:
        """Clear the R session state."""
        try:
            if self.session_workspace.exists():
                self.session_workspace.unlink()
            self.session_history = []
            logger.info("R session state cleared")
        except Exception as e:
            logger.warning(f"Failed to clear session state: {e}")
    
    def _validate_code_safety(self, code: str) -> bool:
        """Basic validation to prevent obviously dangerous operations."""
        
        dangerous_patterns = [
            # System operations
            r'system\s*\(',
            r'shell\s*\(',
            r'Sys\.setenv',
            
            # File operations that could be dangerous
            r'unlink\s*\(',
            r'file\.remove\s*\(',
            r'file\.create\s*\(',
            
            # Network operations
            r'download\.file\s*\(',
            r'url\s*\(',
            
            # Process operations (but allow quit in controlled contexts)
            # r'q\s*\(\)',
            # r'quit\s*\(\)',
            
            # Dangerous eval
            r'eval\s*\(',
        ]
        
        import re
        
        for pattern in dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                logger.warning(f"Code rejected due to pattern: {pattern}")
                return False
        
        return True
    
    def _truncate_output(self, output: str) -> str:
        """Truncate output to max lines."""
        if not output:
            return output
        
        lines = output.split('\n')
        if len(lines) <= self.max_output_lines:
            return output
        
        truncated = lines[:self.max_output_lines]
        truncated.append(f"... (output truncated, {len(lines) - self.max_output_lines} more lines)")
        return '\n'.join(truncated)
"""Enhanced R documentation indexer for building the RAG knowledge base."""

import re
import json
import gzip
import tempfile
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator
import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from .retriever import Document
from ..r_integration.executor import SecureRExecutor

logger = logging.getLogger(__name__)


class RDocumentationIndexer:
    """Indexes R documentation from CRAN and other sources."""
    
    def __init__(self, cache_dir: Path, cran_mirror: str = "https://cran.r-project.org"):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cran_mirror = cran_mirror
        
        # Enhanced cache structure
        self.packages_cache = self.cache_dir / "packages.json"
        self.docs_cache = self.cache_dir / "docs"
        self.man_pages_cache = self.cache_dir / "man_pages"
        self.vignettes_cache = self.cache_dir / "vignettes"
        self.task_views_cache = self.cache_dir / "task_views"
        self.r_extensions_cache = self.cache_dir / "r_extensions"
        
        # Create cache directories
        for cache_dir in [self.docs_cache, self.man_pages_cache, 
                         self.vignettes_cache, self.task_views_cache,
                         self.r_extensions_cache]:
            cache_dir.mkdir(exist_ok=True)
        
        # Initialize R executor for man page extraction
        self.r_executor = SecureRExecutor()
        
        # Essential R packages for Phase 1 - covers 80% of common use cases
        self.essential_packages = [
            # Base R packages (always available)
            'base', 'stats', 'graphics', 'grDevices', 'utils', 'datasets', 'methods', 
            'grid', 'splines', 'stats4', 'tools',
            
            # Popular installed packages (check availability)
            'ggplot2', 'dplyr', 'tidyr', 'readr', 'stringr', 'lubridate',
            'data.table', 'shiny', 'plotly', 'knitr', 'rmarkdown'
        ]
    
    def build_essential_index(self) -> List[Document]:
        """Build essential R documentation index - Phase 1 implementation.
        
        Returns:
            List of Document objects covering essential R functions
        """
        logger.info("Building essential R documentation index...")
        
        all_documents = []
        successful_packages = 0
        
        # Check which packages are actually available
        available_packages = self._get_available_packages()
        
        for package_name in self.essential_packages:
            if package_name not in available_packages:
                logger.warning(f"Package '{package_name}' not available, skipping")
                continue
                
            try:
                logger.info(f"Indexing essential package: {package_name}")
                documents = self.extract_man_pages(package_name)
                
                if documents:
                    all_documents.extend(documents)
                    successful_packages += 1
                    logger.info(f"Successfully indexed {package_name}: {len(documents)} functions")
                else:
                    logger.warning(f"No documentation found for {package_name}")
                    
            except Exception as e:
                logger.error(f"Failed to index {package_name}: {e}")
                continue
        
        logger.info(f"Essential index complete: {len(all_documents)} functions from {successful_packages} packages")
        return all_documents
    
    def _get_available_packages(self) -> set:
        """Get list of packages that are actually installed and available."""
        try:
            r_code = '''
            installed_packages <- rownames(installed.packages())
            cat(paste(installed_packages, collapse = "\\n"))
            '''
            result = self.r_executor.execute_code(r_code)
            
            if result.success:
                packages = set(result.stdout.strip().split('\n'))
                logger.info(f"Found {len(packages)} installed packages")
                return packages
            else:
                logger.warning("Could not get installed packages list, using defaults")
                return {'base', 'stats', 'graphics', 'grDevices', 'utils', 'datasets', 'methods'}
                
        except Exception as e:
            logger.error(f"Error getting available packages: {e}")
            return {'base', 'stats', 'graphics', 'grDevices', 'utils', 'datasets', 'methods'}
    
    def get_cran_packages(self, force_update: bool = False) -> List[Dict[str, Any]]:
        """Get list of CRAN packages with metadata."""
        
        if not force_update and self.packages_cache.exists():
            logger.info("Loading packages from cache...")
            with open(self.packages_cache) as f:
                return json.load(f)
        
        logger.info("Fetching CRAN packages list...")
        
        try:
            # Get packages from CRAN
            packages_url = f"{self.cran_mirror}/web/packages/packages.rds"
            
            # Download and parse the RDS file (simplified approach)
            # In practice, you might want to use rpy2 to read RDS files properly
            
            # For now, use the web API or text version
            packages_txt_url = f"{self.cran_mirror}/web/packages/available_packages_by_date.html"
            
            response = requests.get(packages_txt_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            packages = []
            table = soup.find('table')
            
            if table:
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        date = cols[0].text.strip()
                        package_link = cols[1].find('a')
                        if package_link:
                            package_name = package_link.text.strip()
                            title = cols[2].text.strip()
                            
                            packages.append({
                                'name': package_name,
                                'title': title,
                                'date': date,
                                'url': f"{self.cran_mirror}/web/packages/{package_name}/index.html"
                            })
            
            # Save to cache
            with open(self.packages_cache, 'w') as f:
                json.dump(packages, f, indent=2)
            
            logger.info(f"Found {len(packages)} CRAN packages")
            return packages
            
        except Exception as e:
            logger.error(f"Failed to fetch CRAN packages: {e}")
            return []
    
    def search_packages(self, query: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Search packages by name or title."""
        packages = self.get_cran_packages()
        
        query_lower = query.lower()
        matches = []
        
        for pkg in packages:
            name_match = query_lower in pkg['name'].lower()
            title_match = query_lower in pkg['title'].lower()
            
            if name_match or title_match:
                score = 2 if name_match else 1  # Prefer name matches
                matches.append((pkg, score))
        
        # Sort by score and return top results
        matches.sort(key=lambda x: x[1], reverse=True)
        return [match[0] for match in matches[:max_results]]
    
    def download_package_docs(self, package_name: str) -> Optional[Dict[str, Any]]:
        """Download documentation for a specific package."""
        
        package_cache = self.docs_cache / f"{package_name}.json"
        
        # Check cache first
        if package_cache.exists():
            with open(package_cache) as f:
                return json.load(f)
        
        logger.info(f"Downloading docs for package: {package_name}")
        
        try:
            # Download package manual (PDF would be ideal, but HTML is easier to parse)
            manual_url = f"{self.cran_mirror}/web/packages/{package_name}/{package_name}.pdf"
            
            # For now, let's get the package webpage and reference manual
            pkg_url = f"{self.cran_mirror}/web/packages/{package_name}/index.html"
            
            response = requests.get(pkg_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract package information
            pkg_info = {
                'name': package_name,
                'description': '',
                'version': '',
                'maintainer': '',
                'functions': []
            }
            
            # Parse package page
            table = soup.find('table')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        key = cells[0].text.strip().rstrip(':')
                        value = cells[1].text.strip()
                        
                        if key == 'Version':
                            pkg_info['version'] = value
                        elif key == 'Maintainer':
                            pkg_info['maintainer'] = value
                        elif key == 'Description':
                            pkg_info['description'] = value
            
            # Try to get function reference
            ref_url = f"{self.cran_mirror}/web/packages/{package_name}/vignettes/"
            try:
                ref_response = requests.get(ref_url, timeout=15)
                if ref_response.status_code == 200:
                    ref_soup = BeautifulSoup(ref_response.content, 'html.parser')
                    # Parse vignettes and function docs
                    # This is a simplified version
                    pass
            except:
                pass
            
            # Save to cache
            with open(package_cache, 'w') as f:
                json.dump(pkg_info, f, indent=2)
            
            return pkg_info
            
        except Exception as e:
            logger.error(f"Failed to download docs for {package_name}: {e}")
            return None
    
    def create_documents_from_packages(self, packages: List[str]) -> List[Document]:
        """Create Document objects from package documentation."""
        
        documents = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit download tasks
            future_to_package = {
                executor.submit(self.download_package_docs, pkg): pkg 
                for pkg in packages
            }
            
            for future in as_completed(future_to_package):
                package_name = future_to_package[future]
                try:
                    pkg_info = future.result()
                    if pkg_info:
                        docs = self._package_info_to_documents(pkg_info)
                        documents.extend(docs)
                        
                except Exception as e:
                    logger.error(f"Error processing {package_name}: {e}")
        
        return documents
    
    def _package_info_to_documents(self, pkg_info: Dict[str, Any]) -> List[Document]:
        """Convert package info to Document objects."""
        
        documents = []
        package_name = pkg_info['name']
        
        # Main package description document
        main_content = f"""
Package: {package_name}
Version: {pkg_info.get('version', '')}
Maintainer: {pkg_info.get('maintainer', '')}

Description:
{pkg_info.get('description', '')}
        """.strip()
        
        main_doc = Document(
            content=main_content,
            metadata={
                'type': 'package_description',
                'package': package_name,
                'title': f"{package_name} - Package Description"
            },
            doc_id=f"{package_name}_description"
        )
        documents.append(main_doc)
        
        # Function documentation (if available)
        for func_info in pkg_info.get('functions', []):
            func_content = f"""
Function: {func_info.get('name', '')}
Package: {package_name}

{func_info.get('description', '')}

Usage:
{func_info.get('usage', '')}

Arguments:
{func_info.get('arguments', '')}

Examples:
{func_info.get('examples', '')}
            """.strip()
            
            func_doc = Document(
                content=func_content,
                metadata={
                    'type': 'function',
                    'package': package_name,
                    'function': func_info.get('name', ''),
                    'title': f"{package_name}::{func_info.get('name', '')}"
                },
                doc_id=f"{package_name}_{func_info.get('name', '')}"
            )
            documents.append(func_doc)
        
        return documents
    
    def index_base_r(self) -> List[Document]:
        """Index base R documentation."""
        
        logger.info("Indexing base R documentation...")
        
        # This would ideally parse R's built-in help system
        # For now, create some basic documents for core functions
        
        base_functions = [
            {
                'name': 'lm',
                'description': 'Fitting Linear Models',
                'usage': 'lm(formula, data, subset, weights, na.action, method = "qr", model = TRUE, x = FALSE, y = FALSE, qr = TRUE, singular.ok = TRUE, contrasts = NULL, offset, ...)',
                'details': 'lm is used to fit linear models. It can be used to carry out regression, single stratum analysis of variance and analysis of covariance.',
                'package': 'stats'
            },
            {
                'name': 'ggplot',
                'description': 'Create a new ggplot',
                'usage': 'ggplot(data = NULL, mapping = aes(), ..., environment = parent.frame())',
                'details': 'ggplot() initializes a ggplot object. It can be used to declare the input data frame for a graphic and to specify the set of plot aesthetics intended to be common throughout all subsequent layers unless specifically overridden.',
                'package': 'ggplot2'
            },
            # Add more core functions...
        ]
        
        documents = []
        
        for func in base_functions:
            content = f"""
Function: {func['name']}
Package: {func['package']}

Description:
{func['description']}

Usage:
{func['usage']}

Details:
{func['details']}
            """.strip()
            
            doc = Document(
                content=content,
                metadata={
                    'type': 'function',
                    'package': func['package'],
                    'function': func['name'],
                    'title': f"{func['package']}::{func['name']}"
                },
                doc_id=f"{func['package']}_{func['name']}"
            )
            documents.append(doc)
        
        return documents
    
    def extract_man_pages(self, package_name: str) -> List[Document]:
        """Extract man pages (.Rd files) from an installed R package."""
        
        man_cache_file = self.man_pages_cache / f"{package_name}_man.json"
        
        # Check cache first
        if man_cache_file.exists():
            with open(man_cache_file) as f:
                man_data = json.load(f)
                return self._man_data_to_documents(man_data)
        
        logger.info(f"Extracting man pages for package: {package_name}")
        
        try:
            # Super simple approach that works reliably
            r_code = f'''
# Simple approach using help() to avoid null bytes
tryCatch({{
    # Check if package is available (including base packages)
    pkg_available <- "{package_name}" %in% c("base", "stats", "utils", "methods", "graphics", "grDevices", "datasets") ||
                     requireNamespace("{package_name}", quietly = TRUE)
    
    if (!pkg_available) {{
        cat("CHATR_ERROR: Package {package_name} not available\\n")
        quit()
    }}
    
    # Get available functions in the package
    pkg_functions <- try(ls("package:{package_name}"), silent=TRUE)
    if (inherits(pkg_functions, "try-error") || length(pkg_functions) == 0) {{
        cat("CHATR_ERROR: No functions found\\n")
        quit()
    }}
    
    # Increase limit for better coverage - get more functions
    pkg_functions <- head(pkg_functions, 30)  # Reduced for testing
    
    cat("CHATR_START_JSON\\n")
    cat("{{\\n")
    
    valid_count <- 0
    for (i in seq_along(pkg_functions)) {{
        func_name <- pkg_functions[i]
        
        tryCatch({{
            # Use help() to verify function exists, then create enhanced description
            help_result <- help(func_name, package = "{package_name}")
            
            if (length(help_result) > 0) {{
                # Try to get function information using R's internal tools
                func_info <- tryCatch({{
                    # Get function if possible
                    func_obj <- get(func_name, envir = asNamespace("{package_name}"))
                    if (is.function(func_obj)) {{
                        args_list <- names(formals(func_obj))
                        if (length(args_list) > 0) {{
                            args_str <- paste(head(args_list, 5), collapse = ", ")
                            paste("Function", func_name, "with arguments:", args_str)
                        }} else {{
                            paste("Function", func_name, "from package {package_name}")
                        }}
                    }} else {{
                        paste("Object", func_name, "from package {package_name}")
                    }}
                }}, error = function(e) {{
                    paste("Function", func_name, "from package {package_name}. R Documentation available via help()")
                }})
                
                # Enhanced content with package context
                content_safe <- paste(func_info, ". Use help('", func_name, "', package='{package_name}') for full documentation.", sep='')
                content_safe <- gsub('"', "'", content_safe)
                content_safe <- trimws(content_safe)
                
                if (valid_count > 0) cat(",\\n")
                cat('  \\"', func_name, '\\": {{', sep='')
                cat('\\"name\\": \\"', func_name, '\\", ', sep='')
                cat('\\"package\\": \\"{package_name}\\", ', sep='')
                cat('\\"content\\": \\"', content_safe, '\\"', sep='')
                cat('}}')
                valid_count <- valid_count + 1
            }}
        }}, error = function(e) {{
            # Skip functions with errors
        }})
    }}
    
    cat("\\n}}\\n")
    cat("CHATR_END_JSON\\n")
    
}}, error = function(e) {{
    cat("CHATR_ERROR:", toString(e), "\\n")
}})
'''
            
            result = self.r_executor.execute_code(r_code)
            
            if result.success and result.stdout.strip():
                # Check for errors
                if "CHATR_ERROR:" in result.stdout:
                    logger.warning(f"R error for {package_name}: {result.stdout}")
                    return []
                
                try:
                    # Extract JSON between markers
                    stdout = result.stdout
                    if "CHATR_START_JSON" in stdout and "CHATR_END_JSON" in stdout:
                        start_idx = stdout.find("CHATR_START_JSON") + len("CHATR_START_JSON")
                        end_idx = stdout.find("CHATR_END_JSON")
                        json_str = stdout[start_idx:end_idx].strip()
                        
                        if json_str:
                            man_data = json.loads(json_str)
                        else:
                            logger.info(f"Empty JSON for {package_name}, using fallback")
                            return self._fallback_man_pages_extraction(package_name)
                    else:
                        logger.info(f"No JSON markers found for {package_name}, using fallback")
                        return self._fallback_man_pages_extraction(package_name)
                    
                    # Save to cache
                    with open(man_cache_file, 'w') as f:
                        json.dump(man_data, f, indent=2)
                    
                    return self._man_data_to_documents(man_data)
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse man page JSON for {package_name}: {e}")
                    # Use fallback approach
                    return self._fallback_man_pages_extraction(package_name)
            else:
                logger.warning(f"Failed to extract man pages for {package_name}: {result.stderr}")
                return []
                
        except Exception as e:
            logger.error(f"Error extracting man pages for {package_name}: {e}")
            return []
    
    def _man_data_to_documents(self, man_data: Dict[str, Any]) -> List[Document]:
        """Convert man page data to Document objects."""
        documents = []
        
        for func_name, func_info in man_data.items():
            if isinstance(func_info, dict):
                content = func_info.get('content', '')
                package_name = func_info.get('package', '')
                
                doc = Document(
                    content=content,
                    metadata={
                        'type': 'man_page',
                        'package': package_name,
                        'function': func_name,
                        'title': f"{package_name}::{func_name} - Manual Page",
                        'task': self._infer_task_from_function(func_name, content),
                        'concept': ', '.join(self._extract_concepts(content))
                    },
                    doc_id=f"man_{package_name}_{func_name}"
                )
                documents.append(doc)
        
        return documents
    
    def extract_vignettes(self, package_name: str) -> List[Document]:
        """Extract vignettes (tutorials) from an R package."""
        
        vignette_cache_file = self.vignettes_cache / f"{package_name}_vignettes.json"
        
        # Check cache first
        if vignette_cache_file.exists():
            with open(vignette_cache_file) as f:
                vignette_data = json.load(f)
                return self._vignette_data_to_documents(vignette_data)
        
        logger.info(f"Extracting vignettes for package: {package_name}")
        
        try:
            r_code = f'''
if (!requireNamespace("{package_name}", quietly = TRUE)) {{
    cat("Package {package_name} not installed\\n")
    quit()
}}

# Get vignettes for the package
vignettes <- vignette(package = "{package_name}")$results

if (nrow(vignettes) == 0) {{
    cat("[]")
    quit()
}}

vignette_data <- list()

for (i in 1:nrow(vignettes)) {{
    vign_name <- vignettes[i, "Item"]
    vign_title <- vignettes[i, "Title"]
    
    tryCatch({{
        # Get vignette content
        vign <- vignette(vign_name, package = "{package_name}")
        vign_file <- vign$file
        
        if (file.exists(vign_file)) {{
            if (grepl("\\\\.pdf$", vign_file)) {{
                # PDF vignette - would need PDF extraction
                content <- paste("PDF Vignette:", vign_title)
            }} else if (grepl("\\\\.html$", vign_file)) {{
                # HTML vignette
                content <- paste(readLines(vign_file), collapse = "\\n")
            }} else if (grepl("\\\\.Rmd$", vign_file)) {{
                # R Markdown vignette
                content <- paste(readLines(vign_file), collapse = "\\n")
            }} else {{
                content <- paste("Vignette:", vign_title)
            }}
            
            vignette_data[[vign_name]] <- list(
                name = vign_name,
                title = vign_title,
                package = "{package_name}",
                content = content
            )
        }}
    }}, error = function(e) {{
        # Skip vignettes with errors
    }})
}}

cat(jsonlite::toJSON(vignette_data, auto_unbox = TRUE, pretty = TRUE))
'''
            
            result = self.r_executor.execute_code(r_code)
            
            if result.success and result.stdout.strip():
                try:
                    # Clean the JSON output
                    json_output = self._clean_r_json_output(result.stdout)
                    vignette_data = json.loads(json_output)
                    
                    # Handle case where vignette_data might be a list instead of dict
                    if isinstance(vignette_data, list):
                        if len(vignette_data) == 0:
                            logger.info(f"No vignettes found for {package_name}")
                            return []
                        # Convert list to dict format
                        vignette_data = {f"vignette_{i}": item for i, item in enumerate(vignette_data)}
                    
                    # Save to cache
                    with open(vignette_cache_file, 'w') as f:
                        json.dump(vignette_data, f, indent=2)
                    
                    return self._vignette_data_to_documents(vignette_data)
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse vignette JSON for {package_name}: {e}")
                    return []
            else:
                logger.warning(f"No vignettes found for {package_name}")
                return []
                
        except Exception as e:
            logger.error(f"Error extracting vignettes for {package_name}: {e}")
            return []
    
    def _vignette_data_to_documents(self, vignette_data: Dict[str, Any]) -> List[Document]:
        """Convert vignette data to Document objects."""
        documents = []
        
        for vign_name, vign_info in vignette_data.items():
            if isinstance(vign_info, dict):
                content = vign_info.get('content', '')
                title = vign_info.get('title', '')
                package_name = vign_info.get('package', '')
                
                doc = Document(
                    content=content,
                    metadata={
                        'type': 'vignette',
                        'package': package_name,
                        'vignette': vign_name,
                        'title': title,
                        'task': self._infer_task_from_content(content),
                        'concept': ', '.join(self._extract_concepts(content))
                    },
                    doc_id=f"vignette_{package_name}_{vign_name}"
                )
                documents.append(doc)
        
        return documents
    
    def extract_cran_task_views(self) -> List[Document]:
        """Extract CRAN Task Views (curated package lists by topic)."""
        
        task_views_cache_file = self.task_views_cache / "task_views.json"
        
        # Check cache first
        if task_views_cache_file.exists():
            with open(task_views_cache_file) as f:
                task_views_data = json.load(f)
                return self._task_views_to_documents(task_views_data)
        
        logger.info("Extracting CRAN Task Views...")
        
        try:
            # Get task views from CRAN
            task_views_url = f"{self.cran_mirror}/web/views/"
            response = requests.get(task_views_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            task_views = {}
            
            # Find all task view links
            for link in soup.find_all('a', href=re.compile(r'.*\.html$')):
                parent = link.get_parent()
                if parent and 'Task View:' in parent.get_text():
                    view_name = link.get('href').replace('.html', '')
                    view_title = link.text.strip()
                    view_url = f"{self.cran_mirror}/web/views/{link.get('href')}"
                    
                    # Download the task view page
                    try:
                        view_response = requests.get(view_url, timeout=15)
                        view_response.raise_for_status()
                        
                        view_soup = BeautifulSoup(view_response.content, 'html.parser')
                        
                        # Extract task view content
                        content_div = view_soup.find('body')
                        if content_div:
                            content = content_div.get_text(strip=True)
                            
                            task_views[view_name] = {
                                'name': view_name,
                                'title': view_title,
                                'content': content,
                                'url': view_url
                            }
                    
                    except Exception as e:
                        logger.warning(f"Failed to extract task view {view_name}: {e}")
            
            # Save to cache
            with open(task_views_cache_file, 'w') as f:
                json.dump(task_views, f, indent=2)
            
            return self._task_views_to_documents(task_views)
            
        except Exception as e:
            logger.error(f"Error extracting CRAN task views: {e}")
            return []
    
    def _task_views_to_documents(self, task_views_data: Dict[str, Any]) -> List[Document]:
        """Convert task views data to Document objects."""
        documents = []
        
        for view_name, view_info in task_views_data.items():
            content = view_info.get('content', '')
            title = view_info.get('title', '')
            
            doc = Document(
                content=content,
                metadata={
                    'type': 'task_view',
                    'task_view': view_name,
                    'title': title,
                    'task': view_name.lower().replace('_', ' '),
                    'concept': ', '.join(self._extract_concepts(content))
                },
                doc_id=f"task_view_{view_name}"
            )
            documents.append(doc)
        
        return documents
    
    def extract_r_extensions_guide(self) -> List[Document]:
        """Extract Writing R Extensions guide for package development."""
        
        r_ext_cache_file = self.r_extensions_cache / "r_extensions.json"
        
        # Check cache first
        if r_ext_cache_file.exists():
            with open(r_ext_cache_file) as f:
                r_ext_data = json.load(f)
                return self._r_extensions_to_documents(r_ext_data)
        
        logger.info("Extracting Writing R Extensions guide...")
        
        try:
            # Get R Extensions guide from CRAN
            r_ext_url = f"{self.cran_mirror}/doc/manuals/r-release/R-exts.html"
            response = requests.get(r_ext_url, timeout=60)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract sections
            sections = {}
            current_section = None
            
            for element in soup.find_all(['h1', 'h2', 'h3', 'p', 'pre']):
                if element.name in ['h1', 'h2', 'h3']:
                    current_section = element.get_text(strip=True)
                    if current_section not in sections:
                        sections[current_section] = []
                elif current_section and element.name in ['p', 'pre']:
                    sections[current_section].append(element.get_text(strip=True))
            
            # Convert to structured format
            r_ext_data = {}
            for section_name, section_content in sections.items():
                if section_content:  # Only include sections with content
                    r_ext_data[section_name] = {
                        'title': section_name,
                        'content': '\n'.join(section_content)
                    }
            
            # Save to cache
            with open(r_ext_cache_file, 'w') as f:
                json.dump(r_ext_data, f, indent=2)
            
            return self._r_extensions_to_documents(r_ext_data)
            
        except Exception as e:
            logger.error(f"Error extracting R Extensions guide: {e}")
            return []
    
    def _r_extensions_to_documents(self, r_ext_data: Dict[str, Any]) -> List[Document]:
        """Convert R Extensions data to Document objects."""
        documents = []
        
        for section_name, section_info in r_ext_data.items():
            content = section_info.get('content', '')
            
            doc = Document(
                content=content,
                metadata={
                    'type': 'r_extensions',
                    'section': section_name,
                    'title': f"Writing R Extensions: {section_name}",
                    'task': 'package_development',
                    'concept': ', '.join(self._extract_concepts(content))
                },
                doc_id=f"r_ext_{section_name.lower().replace(' ', '_')}"
            )
            documents.append(doc)
        
        return documents
    
    def _infer_task_from_function(self, func_name: str, content: str) -> str:
        """Infer the task category from function name and content."""
        func_lower = func_name.lower()
        content_lower = content.lower()
        
        # Task inference rules
        if any(keyword in func_lower for keyword in ['plot', 'ggplot', 'graph', 'chart']):
            return 'data_visualization'
        elif any(keyword in func_lower for keyword in ['lm', 'glm', 'model', 'predict']):
            return 'statistical_modeling'
        elif any(keyword in func_lower for keyword in ['read', 'write', 'import', 'export']):
            return 'data_io'
        elif any(keyword in func_lower for keyword in ['filter', 'select', 'mutate', 'group']):
            return 'data_manipulation'
        elif any(keyword in content_lower for keyword in ['test', 'hypothesis', 'p-value']):
            return 'statistical_testing'
        else:
            return 'general'
    
    def _infer_task_from_content(self, content: str) -> str:
        """Infer the task category from content."""
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ['visualization', 'plot', 'graph', 'chart']):
            return 'data_visualization'
        elif any(keyword in content_lower for keyword in ['regression', 'model', 'predict', 'machine learning']):
            return 'statistical_modeling'
        elif any(keyword in content_lower for keyword in ['import', 'export', 'read', 'write']):
            return 'data_io'
        elif any(keyword in content_lower for keyword in ['clean', 'transform', 'manipulate']):
            return 'data_manipulation'
        else:
            return 'general'
    
    def _extract_concepts(self, content: str) -> List[str]:
        """Extract key concepts from content."""
        content_lower = content.lower()
        concepts = []
        
        # Statistical concepts
        stat_concepts = ['regression', 'correlation', 'anova', 'hypothesis', 'distribution', 
                        'variance', 'mean', 'median', 'significance', 'p-value']
        
        # Data concepts
        data_concepts = ['dataframe', 'tibble', 'matrix', 'vector', 'factor', 'variable']
        
        # Visualization concepts
        viz_concepts = ['scatter', 'histogram', 'boxplot', 'density', 'bar chart', 'line plot']
        
        all_concepts = stat_concepts + data_concepts + viz_concepts
        
        for concept in all_concepts:
            if concept in content_lower:
                concepts.append(concept)
        
        return concepts[:5]  # Limit to top 5 concepts
    
    def _clean_r_json_output(self, raw_output: str) -> str:
        """Clean R JSON output to make it valid JSON."""
        import re
        
        lines = raw_output.strip().split('\n')
        
        # Find the start and end of JSON
        json_start = -1
        json_end = -1
        brace_count = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('{') or stripped.startswith('['):
                json_start = i
                break
        
        if json_start == -1:
            return "{}"  # Return empty JSON if no start found
        
        # Find matching end brace/bracket
        for i in range(json_start, len(lines)):
            line = lines[i].strip()
            brace_count += line.count('{') - line.count('}')
            brace_count += line.count('[') - line.count(']')
            
            if brace_count == 0 and (line.endswith('}') or line.endswith(']')):
                json_end = i
                break
        
        if json_end == -1:
            json_end = len(lines) - 1
        
        # Extract JSON part
        json_lines = lines[json_start:json_end + 1]
        json_text = '\n'.join(json_lines)
        
        # Clean problematic characters and patterns
        # Remove control characters except newlines and tabs
        json_text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', json_text)
        
        # Fix common R JSON issues
        json_text = re.sub(r'(?<!\\)"([^"]*?)(?<!\\)"(?=\s*[,\]\}])', r'"\1"', json_text)
        json_text = re.sub(r':\s*"([^"]*?)\n([^"]*?)"', r': "\1\\n\2"', json_text)
        
        # Fix trailing commas
        json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
        
        # Ensure proper escaping
        json_text = json_text.replace('\\n', '\\\\n').replace('\\t', '\\\\t')
        
        return json_text
    
    def _fallback_man_pages_extraction(self, package_name: str) -> List[Document]:
        """Fallback method for extracting man pages when JSON parsing fails."""
        logger.info(f"Using fallback extraction for {package_name} man pages")
        
        try:
            # Simple approach: get basic help for key functions
            r_code = f'''
if (!requireNamespace("{package_name}", quietly = TRUE)) {{
    cat("Package not available")
    quit()
}}

library("{package_name}")

# Get function list
funcs <- ls("package:{package_name}")
# Increase to more functions for better coverage  
funcs <- head(funcs, 50)

for (func in funcs) {{
    tryCatch({{
        cat("FUNCTION_START:", func, "\\n")
        help_text <- capture.output(help(func, package = "{package_name}"))
        cat(paste(help_text, collapse = "\\n"))
        cat("\\nFUNCTION_END\\n")
    }}, error = function(e) {{
        # Skip problematic functions
    }})
}}
'''
            
            result = self.r_executor.execute_code(r_code)
            
            if result.success and result.stdout.strip():
                return self._parse_fallback_help_output(result.stdout, package_name)
            else:
                return []
                
        except Exception as e:
            logger.error(f"Fallback extraction failed for {package_name}: {e}")
            return []
    
    def _parse_fallback_help_output(self, output: str, package_name: str) -> List[Document]:
        """Parse the fallback help output into documents."""
        documents = []
        
        # Split by function markers
        sections = output.split('FUNCTION_START:')
        
        for section in sections[1:]:  # Skip first empty section
            try:
                lines = section.split('\n')
                func_name = lines[0].strip()
                
                # Find the end marker
                content_lines = []
                for line in lines[1:]:
                    if line.strip() == 'FUNCTION_END':
                        break
                    content_lines.append(line)
                
                content = '\n'.join(content_lines).strip()
                
                if content and func_name:
                    doc = Document(
                        content=f"Function: {func_name}\nPackage: {package_name}\n\n{content}",
                        metadata={
                            'type': 'man_page',
                            'package': package_name,
                            'function': func_name,
                            'title': f"{package_name}::{func_name} - Manual Page",
                            'task': self._infer_task_from_function(func_name, content),
                            'concept': ', '.join(self._extract_concepts(content))
                        },
                        doc_id=f"man_{package_name}_{func_name}"
                    )
                    documents.append(doc)
            
            except Exception as e:
                logger.warning(f"Failed to parse fallback section for {package_name}: {e}")
                continue
        
        return documents
"""External data sources for live updates in the RAG system."""

import json
import requests
import sqlite3
import time
import hashlib
import schedule
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from bs4 import BeautifulSoup
import logging
import feedparser
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from .retriever import Document

logger = logging.getLogger(__name__)


class ExternalDataManager:
    """Manages external data sources for live updates."""
    
    def __init__(self, cache_dir: Path, github_token: Optional[str] = None):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # External data cache directories
        self.cran_cache = self.cache_dir / "cran_live"
        self.r_universe_cache = self.cache_dir / "r_universe"
        self.pkgdown_cache = self.cache_dir / "pkgdown"
        self.scholarly_cache = self.cache_dir / "scholarly"
        self.community_cache = self.cache_dir / "community"
        self.github_cache = self.cache_dir / "github_code"
        
        for cache_dir in [self.cran_cache, self.r_universe_cache, self.pkgdown_cache,
                         self.scholarly_cache, self.community_cache, self.github_cache]:
            cache_dir.mkdir(exist_ok=True)
        
        # Initialize SQLite database for structured data
        self.db_path = self.cache_dir / "external_data.db"
        self.init_database()
        
        self.github_token = github_token
        self.session = requests.Session()
        if github_token:
            self.session.headers.update({'Authorization': f'token {github_token}'})
        
        # Rate limiting
        self.github_rate_limit = {
            'remaining': 5000,
            'reset_time': time.time() + 3600,
            'last_check': time.time()
        }
    
    def init_database(self):
        """Initialize SQLite database for caching external data."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # CRAN Task Views with change tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cran_task_views (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE,
                    title TEXT,
                    content_hash TEXT,
                    last_updated TIMESTAMP,
                    content TEXT,
                    url TEXT
                )
            ''')
            
            # R Universe packages
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS r_universe_packages (
                    id INTEGER PRIMARY KEY,
                    org TEXT,
                    package TEXT,
                    version TEXT,
                    title TEXT,
                    description TEXT,
                    readme_content TEXT,
                    last_updated TIMESTAMP,
                    url TEXT,
                    UNIQUE(org, package)
                )
            ''')
            
            # Scholarly papers
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scholarly_papers (
                    id INTEGER PRIMARY KEY,
                    source TEXT,
                    paper_id TEXT,
                    title TEXT,
                    abstract TEXT,
                    authors TEXT,
                    published_date TEXT,
                    url TEXT,
                    keywords TEXT,
                    UNIQUE(source, paper_id)
                )
            ''')
            
            # Community RSS feeds
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS community_posts (
                    id INTEGER PRIMARY KEY,
                    source TEXT,
                    title TEXT,
                    content TEXT,
                    author TEXT,
                    published_date TEXT,
                    url TEXT,
                    tags TEXT,
                    content_hash TEXT UNIQUE
                )
            ''')
            
            # GitHub code snippets
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS github_code (
                    id INTEGER PRIMARY KEY,
                    repository TEXT,
                    file_path TEXT,
                    language TEXT,
                    content TEXT,
                    query_term TEXT,
                    last_updated TIMESTAMP,
                    url TEXT,
                    UNIQUE(repository, file_path, query_term)
                )
            ''')
            
            conn.commit()
    
    def fetch_cran_task_views_updates(self) -> List[Document]:
        """Fetch CRAN Task Views and detect changes."""
        logger.info("Fetching CRAN Task Views updates...")
        
        documents = []
        
        try:
            # Fetch task views index
            task_views_url = "https://cran.r-project.org/web/views/"
            response = requests.get(task_views_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Find all task view links
                for link in soup.find_all('a', href=lambda x: x and x.endswith('.html')):
                    parent = link.parent
                    if parent and 'Task View:' in parent.get_text():
                        view_name = link.get('href').replace('.html', '')
                        view_title = link.text.strip()
                        view_url = f"https://cran.r-project.org/web/views/{link.get('href')}"
                        
                        # Check if we need to update this task view
                        cursor.execute(
                            'SELECT content_hash, last_updated FROM cran_task_views WHERE name = ?',
                            (view_name,)
                        )
                        existing = cursor.fetchone()
                        
                        # Fetch task view content
                        try:
                            view_response = requests.get(view_url, timeout=15)
                            view_response.raise_for_status()
                            
                            view_soup = BeautifulSoup(view_response.content, 'html.parser')
                            content = view_soup.get_text(strip=True)
                            content_hash = hashlib.md5(content.encode()).hexdigest()
                            
                            # Check if content has changed
                            if not existing or existing[0] != content_hash:
                                # Update database
                                cursor.execute('''
                                    INSERT OR REPLACE INTO cran_task_views 
                                    (name, title, content_hash, last_updated, content, url)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                ''', (view_name, view_title, content_hash, datetime.now(), content, view_url))
                                
                                # Create document
                                doc = Document(
                                    content=content,
                                    metadata={
                                        'type': 'cran_task_view',
                                        'source': 'external_cran',
                                        'task_view': view_name,
                                        'title': view_title,
                                        'url': view_url,
                                        'last_updated': datetime.now().isoformat(),
                                        'task': view_name.lower().replace('_', ' '),
                                        'concept': self._extract_r_concepts(content)
                                    },
                                    doc_id=f"external_cran_task_view_{view_name}"
                                )
                                documents.append(doc)
                                
                                logger.info(f"Updated CRAN Task View: {view_name}")
                        
                        except Exception as e:
                            logger.warning(f"Failed to fetch task view {view_name}: {e}")
                
                conn.commit()
        
        except Exception as e:
            logger.error(f"Error fetching CRAN task views: {e}")
        
        return documents
    
    def fetch_r_universe_updates(self, orgs: List[str] = None) -> List[Document]:
        """Fetch R Universe package metadata and READMEs."""
        if orgs is None:
            # Use only verified R-universe orgs
            orgs = ['ropensci', 'r-lib', 'tidyverse', 'rstudio']
        
        logger.info(f"Fetching R Universe updates for orgs: {orgs}")
        documents = []
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for org in orgs:
                try:
                    # Try different R Universe API endpoints
                    api_urls = [
                        f"https://{org}.r-universe.dev/api/packages",
                        f"https://{org}.r-universe.dev/packages",
                        f"https://r-universe.dev/{org}/packages"
                    ]
                    
                    response = None
                    for packages_url in api_urls:
                        try:
                            response = requests.get(packages_url, timeout=15)
                            if response.status_code == 200 and response.text.strip():
                                break
                        except:
                            continue
                    
                    if not response or response.status_code != 200:
                        logger.warning(f"No working R Universe endpoint found for {org}")
                        continue
                    
                    # Check if response has content
                    if not response.text.strip():
                        logger.warning(f"Empty response from R Universe for {org}")
                        continue
                    
                    try:
                        packages_data = response.json()
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON response from R Universe for {org}")
                        continue
                    
                    # Ensure packages_data is a list
                    if not isinstance(packages_data, list):
                        logger.warning(f"Unexpected response format from R Universe for {org}")
                        continue
                    
                    for package_info in packages_data:
                        package_name = package_info.get('Package', '')
                        version = package_info.get('Version', '')
                        title = package_info.get('Title', '')
                        description = package_info.get('Description', '')
                        
                        if not package_name:
                            continue
                        
                        # Check if we need to update this package
                        cursor.execute('''
                            SELECT version FROM r_universe_packages 
                            WHERE org = ? AND package = ?
                        ''', (org, package_name))
                        existing = cursor.fetchone()
                        
                        if not existing or existing[0] != version:
                            # Fetch README
                            readme_content = self._fetch_package_readme(org, package_name)
                            
                            # Update database
                            cursor.execute('''
                                INSERT OR REPLACE INTO r_universe_packages 
                                (org, package, version, title, description, readme_content, last_updated, url)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (org, package_name, version, title, description, readme_content,
                                  datetime.now(), f"https://{org}.r-universe.dev/packages/{package_name}"))
                            
                            # Create document
                            content = f"Package: {package_name}\\nTitle: {title}\\nDescription: {description}"
                            if readme_content:
                                content += f"\\n\\nREADME:\\n{readme_content}"
                            
                            doc = Document(
                                content=content,
                                metadata={
                                    'type': 'r_universe_package',
                                    'source': 'external_r_universe',
                                    'org': org,
                                    'package': package_name,
                                    'version': version,
                                    'title': title,
                                    'last_updated': datetime.now().isoformat(),
                                    'url': f"https://{org}.r-universe.dev/packages/{package_name}",
                                    'concept': self._extract_r_concepts(content)
                                },
                                doc_id=f"external_r_universe_{org}_{package_name}"
                            )
                            documents.append(doc)
                            
                            logger.info(f"Updated R Universe package: {org}/{package_name}")
                
                except Exception as e:
                    logger.warning(f"Failed to fetch R Universe data for {org}: {e}")
            
            conn.commit()
        
        return documents
    
    def fetch_pkgdown_on_demand(self, package_name: str) -> List[Document]:
        """Fetch pkgdown site content for a specific package on-demand."""
        logger.info(f"Fetching pkgdown content for {package_name}")
        
        documents = []
        
        # Common pkgdown site patterns
        pkgdown_urls = [
            f"https://{package_name.lower()}.tidyverse.org",
            f"https://ropensci.github.io/{package_name}",
            f"https://r-lib.github.io/{package_name}",
            f"https://{package_name.lower()}.r-lib.org"
        ]
        
        for base_url in pkgdown_urls:
            try:
                # Check if site exists
                response = requests.head(base_url, timeout=10)
                if response.status_code == 200:
                    # Fetch reference pages
                    ref_url = f"{base_url}/reference/"
                    ref_response = requests.get(ref_url, timeout=15)
                    
                    if ref_response.status_code == 200:
                        soup = BeautifulSoup(ref_response.content, 'html.parser')
                        
                        # Extract function documentation
                        for link in soup.find_all('a', href=lambda x: x and x.endswith('.html')):
                            func_url = f"{base_url}/reference/{link.get('href')}"
                            func_content = self._fetch_pkgdown_page(func_url)
                            
                            if func_content:
                                doc = Document(
                                    content=func_content,
                                    metadata={
                                        'type': 'pkgdown_reference',
                                        'source': 'external_pkgdown',
                                        'package': package_name,
                                        'url': func_url,
                                        'last_updated': datetime.now().isoformat(),
                                        'concept': self._extract_r_concepts(func_content)
                                    },
                                    doc_id=f"external_pkgdown_{package_name}_{link.text.strip()}"
                                )
                                documents.append(doc)
                    
                    break  # Found working pkgdown site
                    
            except Exception as e:
                logger.debug(f"Pkgdown site not found at {base_url}: {e}")
                continue
        
        return documents
    
    def fetch_scholarly_feeds(self, topics: List[str] = None) -> List[Document]:
        """Fetch scholarly papers from arXiv, Crossref, PubMed."""
        if topics is None:
            topics = ['rstats', 'data science', 'statistics', 'machine learning']
        
        logger.info(f"Fetching scholarly feeds for topics: {topics}")
        documents = []
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for topic in topics:
                # ArXiv
                documents.extend(self._fetch_arxiv_papers(topic, cursor))
                
                # PubMed (using E-utilities)
                documents.extend(self._fetch_pubmed_papers(topic, cursor))
            
            conn.commit()
        
        return documents
    
    def fetch_community_rss_feeds(self) -> List[Document]:
        """Fetch community RSS feeds from R-bloggers, R Weekly, etc."""
        logger.info("Fetching community RSS feeds...")
        
        rss_feeds = {
            'r-bloggers': 'https://www.r-bloggers.com/feed/',
            'r-weekly': 'https://rweekly.org/atom.xml',
            'rstudio-blog': 'https://blog.rstudio.com/index.xml',
            'revolutionanalytics': 'https://blog.revolutionanalytics.com/atom.xml'
        }
        
        documents = []
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for source, feed_url in rss_feeds.items():
                try:
                    feed = feedparser.parse(feed_url)
                    
                    for entry in feed.entries[:10]:  # Latest 10 posts
                        content = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                        content_hash = hashlib.md5(f"{entry.title}{content}".encode()).hexdigest()
                        
                        # Check if we already have this post
                        cursor.execute(
                            'SELECT id FROM community_posts WHERE content_hash = ?',
                            (content_hash,)
                        )
                        
                        if not cursor.fetchone():
                            # New post
                            published_date = getattr(entry, 'published', '')
                            author = getattr(entry, 'author', '')
                            
                            cursor.execute('''
                                INSERT INTO community_posts 
                                (source, title, content, author, published_date, url, content_hash)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''', (source, entry.title, content, author, published_date, 
                                  entry.link, content_hash))
                            
                            # Create document
                            doc_content = f"Title: {entry.title}\\nAuthor: {author}\\nPublished: {published_date}\\n\\n{content}"
                            
                            doc = Document(
                                content=doc_content,
                                metadata={
                                    'type': 'community_post',
                                    'source': f'external_rss_{source}',
                                    'title': entry.title,
                                    'author': author,
                                    'published_date': published_date,
                                    'url': entry.link,
                                    'last_updated': datetime.now().isoformat(),
                                    'concept': self._extract_r_concepts(doc_content)
                                },
                                doc_id=f"external_rss_{source}_{content_hash[:8]}"
                            )
                            documents.append(doc)
                            
                            logger.info(f"Added new post from {source}: {entry.title}")
                
                except Exception as e:
                    logger.warning(f"Failed to fetch RSS feed {source}: {e}")
            
            conn.commit()
        
        return documents
    
    def search_github_code(self, query: str, language: str = 'r') -> List[Document]:
        """Search GitHub for code examples with rate limiting."""
        if not self._check_github_rate_limit():
            logger.warning("GitHub rate limit exceeded, skipping code search")
            return []
        
        logger.info(f"Searching GitHub for '{query}' in {language}")
        documents = []
        
        try:
            search_url = "https://api.github.com/search/code"
            params = {
                'q': f"{query} language:{language}",
                'sort': 'indexed',
                'order': 'desc',
                'per_page': 10
            }
            
            response = self.session.get(search_url, params=params, timeout=15)
            
            # Update rate limit info
            self.github_rate_limit['remaining'] = int(response.headers.get('x-ratelimit-remaining', 0))
            self.github_rate_limit['reset_time'] = int(response.headers.get('x-ratelimit-reset', time.time()))
            
            response.raise_for_status()
            search_results = response.json()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for item in search_results.get('items', []):
                    repo = item.get('repository', {}).get('full_name', '')
                    file_path = item.get('path', '')
                    download_url = item.get('download_url', '')
                    
                    # Check if we already have this code
                    cursor.execute('''
                        SELECT id FROM github_code 
                        WHERE repository = ? AND file_path = ? AND query_term = ?
                    ''', (repo, file_path, query))
                    
                    if not cursor.fetchone() and download_url:
                        # Fetch file content
                        try:
                            file_response = requests.get(download_url, timeout=10)
                            file_response.raise_for_status()
                            
                            content = file_response.text
                            
                            cursor.execute('''
                                INSERT INTO github_code 
                                (repository, file_path, language, content, query_term, last_updated, url)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''', (repo, file_path, language, content, query, datetime.now(), item.get('html_url', '')))
                            
                            # Create document
                            doc_content = f"Repository: {repo}\\nFile: {file_path}\\nQuery: {query}\\n\\n{content}"
                            
                            doc = Document(
                                content=doc_content,
                                metadata={
                                    'type': 'github_code',
                                    'source': 'external_github',
                                    'repository': repo,
                                    'file_path': file_path,
                                    'language': language,
                                    'query_term': query,
                                    'url': item.get('html_url', ''),
                                    'last_updated': datetime.now().isoformat(),
                                    'concept': self._extract_r_concepts(content)
                                },
                                doc_id=f"external_github_{hashlib.md5(f'{repo}{file_path}{query}'.encode()).hexdigest()[:8]}"
                            )
                            documents.append(doc)
                            
                            logger.info(f"Added GitHub code: {repo}/{file_path}")
                        
                        except Exception as e:
                            logger.warning(f"Failed to fetch GitHub file {repo}/{file_path}: {e}")
                
                conn.commit()
        
        except Exception as e:
            logger.error(f"GitHub code search failed: {e}")
        
        return documents
    
    # Helper methods
    
    def _fetch_package_readme(self, org: str, package: str) -> str:
        """Fetch README content for an R Universe package."""
        try:
            readme_url = f"https://{org}.r-universe.dev/packages/{package}"
            response = requests.get(readme_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            readme_div = soup.find('div', {'id': 'readme'})
            
            if readme_div:
                return readme_div.get_text(strip=True)
        except Exception as e:
            logger.debug(f"Failed to fetch README for {org}/{package}: {e}")
        
        return ""
    
    def _fetch_pkgdown_page(self, url: str) -> str:
        """Fetch content from a pkgdown page."""
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract main content (varies by pkgdown theme)
            content_selectors = [
                '.contents',
                '.page-header + div',
                'main',
                '.col-md-9'
            ]
            
            for selector in content_selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    return content_div.get_text(strip=True)
            
            # Fallback: get body text
            return soup.get_text(strip=True)
        
        except Exception as e:
            logger.debug(f"Failed to fetch pkgdown page {url}: {e}")
            return ""
    
    def _fetch_arxiv_papers(self, topic: str, cursor) -> List[Document]:
        """Fetch papers from arXiv."""
        documents = []
        
        try:
            # arXiv API search
            arxiv_url = "http://export.arxiv.org/api/query"
            params = {
                'search_query': f'all:{topic}',
                'start': 0,
                'max_results': 10,
                'sortBy': 'submittedDate',
                'sortOrder': 'descending'
            }
            
            response = requests.get(arxiv_url, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse XML response
            soup = BeautifulSoup(response.content, 'xml')
            
            for entry in soup.find_all('entry'):
                # Safe text extraction with fallback
                def safe_get_text(element):
                    if element is None:
                        return ''
                    if hasattr(element, 'get_text'):
                        return element.get_text()
                    return str(element).strip()
                
                paper_id = safe_get_text(entry.id).split('/')[-1] if entry.id else 'unknown'
                title = safe_get_text(entry.title).strip() if entry.title else 'No title'
                abstract = safe_get_text(entry.summary).strip() if entry.summary else 'No abstract'
                
                # Safe author extraction
                authors = []
                for author in entry.find_all('author'):
                    author_name = author.find('name')
                    if author_name:
                        authors.append(safe_get_text(author_name))
                
                published = safe_get_text(entry.published) if entry.published else ''
                url = safe_get_text(entry.id) if entry.id else ''
                
                # Check if we already have this paper
                cursor.execute(
                    'SELECT id FROM scholarly_papers WHERE source = ? AND paper_id = ?',
                    ('arxiv', paper_id)
                )
                
                if not cursor.fetchone():
                    cursor.execute('''
                        INSERT INTO scholarly_papers 
                        (source, paper_id, title, abstract, authors, published_date, url, keywords)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', ('arxiv', paper_id, title, abstract, ', '.join(authors), published, url, topic))
                    
                    # Create document
                    content = f"Title: {title}\\nAuthors: {', '.join(authors)}\\nPublished: {published}\\n\\nAbstract: {abstract}"
                    
                    doc = Document(
                        content=content,
                        metadata={
                            'type': 'scholarly_paper',
                            'source': 'external_arxiv',
                            'paper_id': paper_id,
                            'title': title,
                            'authors': ', '.join(authors),
                            'published_date': published,
                            'url': url,
                            'keywords': topic,
                            'last_updated': datetime.now().isoformat(),
                            'concept': self._extract_r_concepts(content)
                        },
                        doc_id=f"external_arxiv_{paper_id}"
                    )
                    documents.append(doc)
        
        except Exception as e:
            logger.warning(f"Failed to fetch arXiv papers for {topic}: {e}")
        
        return documents
    
    def _fetch_pubmed_papers(self, topic: str, cursor) -> List[Document]:
        """Fetch papers from PubMed E-utilities."""
        documents = []
        
        try:
            # PubMed search
            search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            search_params = {
                'db': 'pubmed',
                'term': topic,
                'retmax': 10,
                'sort': 'date',
                'retmode': 'json'
            }
            
            search_response = requests.get(search_url, params=search_params, timeout=30)
            search_response.raise_for_status()
            search_data = search_response.json()
            
            if 'esearchresult' in search_data and 'idlist' in search_data['esearchresult']:
                pmids = search_data['esearchresult']['idlist']
                
                if pmids:
                    # Fetch details
                    fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
                    fetch_params = {
                        'db': 'pubmed',
                        'id': ','.join(pmids),
                        'retmode': 'xml'
                    }
                    
                    fetch_response = requests.get(fetch_url, params=fetch_params, timeout=30)
                    fetch_response.raise_for_status()
                    
                    soup = BeautifulSoup(fetch_response.content, 'xml')
                    
                    for article in soup.find_all('PubmedArticle'):
                        pmid = article.find('PMID').text
                        title_elem = article.find('ArticleTitle')
                        abstract_elem = article.find('AbstractText')
                        
                        if title_elem and abstract_elem:
                            title = title_elem.text
                            abstract = abstract_elem.text
                            
                            # Extract authors
                            authors = []
                            for author in article.find_all('Author'):
                                last_name = author.find('LastName')
                                first_name = author.find('ForeName')
                                if last_name and first_name:
                                    authors.append(f"{first_name.text} {last_name.text}")
                            
                            # Check if we already have this paper
                            cursor.execute(
                                'SELECT id FROM scholarly_papers WHERE source = ? AND paper_id = ?',
                                ('pubmed', pmid)
                            )
                            
                            if not cursor.fetchone():
                                cursor.execute('''
                                    INSERT INTO scholarly_papers 
                                    (source, paper_id, title, abstract, authors, published_date, url, keywords)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                ''', ('pubmed', pmid, title, abstract, ', '.join(authors), 
                                      '', f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/", topic))
                                
                                # Create document
                                content = f"Title: {title}\\nAuthors: {', '.join(authors)}\\n\\nAbstract: {abstract}"
                                
                                doc = Document(
                                    content=content,
                                    metadata={
                                        'type': 'scholarly_paper',
                                        'source': 'external_pubmed',
                                        'paper_id': pmid,
                                        'title': title,
                                        'authors': ', '.join(authors),
                                        'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                                        'keywords': topic,
                                        'last_updated': datetime.now().isoformat(),
                                        'concept': self._extract_r_concepts(content)
                                    },
                                    doc_id=f"external_pubmed_{pmid}"
                                )
                                documents.append(doc)
        
        except Exception as e:
            logger.warning(f"Failed to fetch PubMed papers for {topic}: {e}")
        
        return documents
    
    def _check_github_rate_limit(self) -> bool:
        """Check if we can make GitHub API requests."""
        current_time = time.time()
        
        if current_time > self.github_rate_limit['reset_time']:
            # Reset time has passed, reset limit
            self.github_rate_limit['remaining'] = 5000
            self.github_rate_limit['reset_time'] = current_time + 3600
        
        return self.github_rate_limit['remaining'] > 10  # Keep some buffer
    
    def _extract_r_concepts(self, content: str) -> str:
        """Extract R-related concepts from content."""
        r_concepts = []
        
        # Common R concepts and patterns
        r_patterns = [
            r'\\b(ggplot2?|dplyr|tidyr|purrr|readr|stringr|forcats|lubridate)\\b',
            r'\\b(data\\.frame|tibble|list|vector|matrix)\\b',
            r'\\b(function|if|else|for|while|repeat)\\b',
            r'\\b(lm|glm|aov|t\\.test|chisq\\.test)\\b',
            r'\\b(plot|ggplot|hist|boxplot|barplot)\\b',
            r'\\b(install\\.packages|library|require)\\b',
        ]
        
        import re
        for pattern in r_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            r_concepts.extend(matches)
        
        return ', '.join(set(r_concepts))
    
    def schedule_updates(self):
        """Schedule regular updates for external data sources."""
        logger.info("Scheduling external data source updates...")
        
        # Schedule CRAN Task Views updates (daily)
        schedule.every().day.at("02:00").do(self.fetch_cran_task_views_updates)
        
        # Schedule R Universe updates (daily)
        schedule.every().day.at("03:00").do(self.fetch_r_universe_updates)
        
        # Schedule scholarly feeds (weekly)
        schedule.every().week.do(self.fetch_scholarly_feeds)
        
        # Schedule community RSS (every 6 hours)
        schedule.every(6).hours.do(self.fetch_community_rss_feeds)
        
        # Start scheduler in background thread
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        logger.info("External data source scheduler started")
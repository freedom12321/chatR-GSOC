"""Hybrid retrieval system using BM25 + dense embeddings."""

import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import logging

logger = logging.getLogger(__name__)


class Document:
    """Represents a document in the retrieval system."""
    
    def __init__(self, content: str, metadata: Dict[str, Any], doc_id: str):
        self.content = content
        self.metadata = metadata
        self.id = doc_id
    
    def __str__(self):
        return f"Document(id={self.id}, content='{self.content[:100]}...')"


class HybridRetriever:
    """Hybrid retrieval system combining BM25 and dense embeddings."""
    
    def __init__(self, index_dir: Path, embedding_model: str = "all-MiniLM-L6-v2"):
        self.index_dir = index_dir
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.bm25: Optional[BM25Okapi] = None
        self.documents: List[Document] = []
        self.embedding_model_name = embedding_model
        self.embedding_model: Optional[SentenceTransformer] = None
        
        # ChromaDB for vector storage
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.index_dir / "chroma"),
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection_name = "r_docs"
        
    def initialize(self) -> None:
        """Initialize the retriever components."""
        logger.info("Initializing hybrid retriever...")
        
        # Load embedding model with fallbacks
        try:
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            logger.info(f"Loaded embedding model: {self.embedding_model_name}")
        except Exception as e:
            logger.warning(f"Failed to load embedding model '{self.embedding_model_name}': {e}")
            # Try fallback models
            fallback_models = ["all-MiniLM-L6-v2", "all-mpnet-base-v2", "distilbert-base-nli-mean-tokens"]
            for fallback in fallback_models:
                try:
                    logger.info(f"Trying fallback model: {fallback}")
                    self.embedding_model = SentenceTransformer(fallback)
                    logger.info(f"Successfully loaded fallback model: {fallback}")
                    break
                except Exception as fallback_e:
                    logger.warning(f"Fallback model '{fallback}' also failed: {fallback_e}")
                    continue
            
            if not self.embedding_model:
                logger.error("All embedding models failed to load. RAG functionality will be limited.")
                # Set a flag to indicate we're running in basic mode
                self.basic_mode = True
            else:
                self.basic_mode = False
        
        # Try to load existing index
        self._load_index()
        
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the retrieval index."""
        logger.info(f"Adding {len(documents)} documents to index...")
        
        self.documents.extend(documents)
        
        # Prepare texts for BM25
        texts = [doc.content for doc in self.documents]
        tokenized_texts = [text.split() for text in texts]
        
        # Build BM25 index
        self.bm25 = BM25Okapi(tokenized_texts)
        
        # Add to vector database
        self._add_to_vector_db(documents)
        
        # Save index
        self._save_index()
        
    def _add_to_vector_db(self, documents: List[Document]) -> None:
        """Add documents to the vector database."""
        if not self.embedding_model:
            raise ValueError("Embedding model not initialized")
            
        # Get or create collection
        try:
            collection = self.chroma_client.get_collection(self.collection_name)
        except:
            collection = self.chroma_client.create_collection(self.collection_name)
        
        # Prepare data for insertion
        contents = [doc.content for doc in documents]
        embeddings = self.embedding_model.encode(contents).tolist()
        
        ids = [doc.id for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        
        # Add to collection
        collection.add(
            embeddings=embeddings,
            documents=contents,
            metadatas=metadatas,
            ids=ids
        )
        
    def retrieve(self, query: str, top_k: int = 10, bm25_weight: float = 0.3) -> List[Tuple[Document, float]]:
        """Retrieve relevant documents using hybrid approach."""
        if not self.bm25 or not self.embedding_model:
            logger.warning("Retriever not properly initialized")
            return []
        
        # BM25 retrieval
        bm25_scores = self._bm25_retrieve(query, top_k * 2)  # Get more candidates
        
        # Dense retrieval
        dense_results = self._dense_retrieve(query, top_k * 2)
        
        # Combine and rerank
        return self._hybrid_rerank(query, bm25_scores, dense_results, top_k, bm25_weight)
        
    def _bm25_retrieve(self, query: str, top_k: int) -> List[Tuple[int, float]]:
        """Retrieve using BM25."""
        query_tokens = query.split()
        scores = self.bm25.get_scores(query_tokens)
        
        # Get top k indices and scores
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [(idx, scores[idx]) for idx in top_indices]
    
    def _dense_retrieve(self, query: str, top_k: int) -> List[Tuple[str, float]]:
        """Retrieve using dense embeddings."""
        collection = self.chroma_client.get_collection(self.collection_name)
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query]).tolist()[0]
        
        # Search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # Return document IDs and distances (convert to similarities)
        doc_results = []
        if results['ids'] and results['distances']:
            for doc_id, distance in zip(results['ids'][0], results['distances'][0]):
                similarity = 1 / (1 + distance)  # Convert distance to similarity
                doc_results.append((doc_id, similarity))
        
        return doc_results
    
    def _hybrid_rerank(
        self, 
        query: str, 
        bm25_results: List[Tuple[int, float]], 
        dense_results: List[Tuple[str, float]], 
        top_k: int, 
        bm25_weight: float
    ) -> List[Tuple[Document, float]]:
        """Combine and rerank BM25 and dense results."""
        
        # Normalize scores
        if bm25_results:
            max_bm25 = max(score for _, score in bm25_results)
            bm25_results = [(idx, score / max_bm25 if max_bm25 > 0 else 0) 
                           for idx, score in bm25_results]
        
        if dense_results:
            max_dense = max(score for _, score in dense_results)
            dense_results = [(doc_id, score / max_dense if max_dense > 0 else 0) 
                            for doc_id, score in dense_results]
        
        # Create document ID to score mappings
        bm25_scores = {}
        for idx, score in bm25_results:
            if idx < len(self.documents):
                doc_id = self.documents[idx].id
                bm25_scores[doc_id] = score
        
        dense_scores = dict(dense_results)
        
        # Combine scores
        combined_scores = {}
        all_doc_ids = set(bm25_scores.keys()) | set(dense_scores.keys())
        
        for doc_id in all_doc_ids:
            bm25_score = bm25_scores.get(doc_id, 0)
            dense_score = dense_scores.get(doc_id, 0)
            
            combined_score = bm25_weight * bm25_score + (1 - bm25_weight) * dense_score
            combined_scores[doc_id] = combined_score
        
        # Sort and get top k
        sorted_docs = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        # Return documents with scores
        results = []
        doc_lookup = {doc.id: doc for doc in self.documents}
        
        for doc_id, score in sorted_docs:
            if doc_id in doc_lookup:
                results.append((doc_lookup[doc_id], score))
        
        return results
    
    def _save_index(self) -> None:
        """Save the BM25 index and document metadata."""
        index_file = self.index_dir / "bm25_index.pkl"
        docs_file = self.index_dir / "documents.pkl"
        
        with open(index_file, 'wb') as f:
            pickle.dump(self.bm25, f)
            
        with open(docs_file, 'wb') as f:
            pickle.dump(self.documents, f)
            
        logger.info(f"Index saved to {self.index_dir}")
    
    def _load_index(self) -> None:
        """Load existing BM25 index and documents."""
        index_file = self.index_dir / "bm25_index.pkl"
        docs_file = self.index_dir / "documents.pkl"
        
        if index_file.exists() and docs_file.exists():
            try:
                with open(index_file, 'rb') as f:
                    self.bm25 = pickle.load(f)
                    
                with open(docs_file, 'rb') as f:
                    self.documents = pickle.load(f)
                    
                logger.info(f"Loaded index with {len(self.documents)} documents")
            except Exception as e:
                logger.error(f"Failed to load existing index: {e}")
                self.bm25 = None
                self.documents = []
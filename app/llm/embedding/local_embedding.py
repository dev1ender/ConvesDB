"""
Local embedding implementation for the RAG-POC application using sentence-transformers.
"""

from typing import List, Dict, Any, Optional
from app.interfaces.llm import EmbeddingClient
from app.logging_setup import get_logger

# Setup module logger
logger = get_logger(__name__)

class LocalEmbedding(EmbeddingClient):
    """Local implementation of the embedding client using sentence-transformers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the local embedding client.
        
        Args:
            model_name: Sentence transformer model name
        """
        self.model_name = model_name
        self.model = None
        self._initialize_model()
        
    def _initialize_model(self) -> None:
        """Initialize the sentence transformer model."""
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"Initializing local embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Local embedding model initialized")
            
        except ImportError:
            logger.error("sentence-transformers package not installed")
            raise ImportError("sentence-transformers package not installed. Install with 'pip install sentence-transformers'")
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of text strings.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
            
        logger.debug(f"Generating embeddings for {len(texts)} texts with model: {self.model_name}")
        
        try:
            # Generate embeddings
            embeddings = self.model.encode(texts)
            
            # Convert numpy arrays to lists
            embedding_lists = embeddings.tolist()
            logger.debug(f"Generated {len(embedding_lists)} embeddings")
            
            return embedding_lists
        
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """Generate an embedding for a single text string.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        logger.debug(f"Generating embedding for text: '{text[:50]}...' with model: {self.model_name}")
        
        try:
            # Generate embedding
            embedding = self.model.encode(text)
            
            # Convert numpy array to list
            embedding_list = embedding.tolist()
            logger.debug(f"Generated embedding with dimension: {len(embedding_list)}")
            
            return embedding_list
        
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise 
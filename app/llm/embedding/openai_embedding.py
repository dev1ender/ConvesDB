"""
OpenAI embedding implementation for the RAG-POC application.
"""

import os
from typing import List, Dict, Any, Optional
from app.interfaces.llm import EmbeddingClient
from app.logging_setup import get_logger

# Setup module logger
logger = get_logger(__name__)

class OpenAIEmbedding(EmbeddingClient):
    """OpenAI implementation of the embedding client."""
    
    def __init__(self, model_name: str = "text-embedding-3-small"):
        """Initialize the OpenAI embedding client.
        
        Args:
            model_name: OpenAI embedding model name
        """
        self.model_name = model_name
        self.client = None
        self._initialize_client()
        
    def _initialize_client(self) -> None:
        """Initialize the OpenAI client."""
        try:
            from openai import OpenAI
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.error("OPENAI_API_KEY environment variable not set")
                raise ValueError("OPENAI_API_KEY environment variable not set")
                
            logger.info(f"Initializing OpenAI embedding client with model: {self.model_name}")
            self.client = OpenAI(api_key=api_key)
            
        except ImportError:
            logger.error("openai package not installed")
            raise ImportError("openai package not installed. Install with 'pip install openai'")
    
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
            response = self.client.embeddings.create(
                model=self.model_name,
                input=texts
            )
            
            # Extract embeddings from response
            embeddings = [data.embedding for data in response.data]
            logger.debug(f"Generated {len(embeddings)} embeddings")
            
            return embeddings
        
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
        
        embeddings = self.embed_texts([text])
        if embeddings:
            return embeddings[0]
        else:
            logger.error("Failed to generate embedding")
            return [] 
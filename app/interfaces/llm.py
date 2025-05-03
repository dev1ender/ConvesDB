"""
LLM service interfaces for the RAG-POC application.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class LLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a response from the LLM.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            The generated response from the LLM
        """
        pass
    
    
class EmbeddingClient(ABC):
    """Abstract base class for embedding generation clients."""
    
    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of text strings.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (as lists of floats)
        """
        pass
    
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generate an embedding for a single text string.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector (as list of floats)
        """
        pass 
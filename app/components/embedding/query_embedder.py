"""
Query embedder component.
"""

import logging
from typing import Any, Dict, List, Optional

from app.components.base_component import BaseComponent
from app.core.exceptions import ComponentRegistryError
from app.llm.factory import LLMFactory


class QueryEmbedder(BaseComponent):
    """
    Query embedding component.
    
    This component generates embeddings for search queries using a configured
    embedding model and stores them in the context for later use in retrieval.
    """
    
    def __init__(self, component_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the query embedder.
        
        Args:
            component_id: Unique identifier for the component
            config: Configuration parameters for the component
        """
        super().__init__(component_id, config)
        
        # Configuration options with defaults
        self.embedding_model = self.get_config_value("embedding_model", "text-embedding-3-small")
        self.embedding_provider = self.get_config_value("embedding_provider", "openai")
        self.include_history = self.get_config_value("include_history", False)
        self.history_weight = self.get_config_value("history_weight", 0.3)
        
        # Initialize the embedding client
        self._embedding_client = None
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the component to generate query embeddings.
        
        Args:
            context: Execution context containing query to embed
            
        Returns:
            Dict[str, Any]: Updated context with query embedding
            
        Raises:
            ComponentRegistryError: If embedding generation fails
        """
        self.logger.debug("Generating query embedding")
        
        # Get query from context
        query = context.get("query", "")
        
        if not query:
            self.logger.warning("No query found in context")
            return {"query_embedding": [], "error": "No query provided"}
        
        # Initialize embedding client if needed
        if not self._embedding_client:
            try:
                self._initialize_embedding_client()
            except Exception as e:
                error_msg = f"Failed to initialize embedding client: {str(e)}"
                self.logger.error(error_msg)
                raise ComponentRegistryError(error_msg)
        
        try:
            # Get query history if enabled
            query_text = query
            if self.include_history:
                history = context.get("query_history", [])
                if history:
                    # Add weighted history to query
                    history_text = " ".join(history[-3:])  # Use last 3 queries
                    query_text = f"{query} {self.history_weight * ' '} {history_text}"
                    self.logger.debug("Including query history in embedding")
            
            # Generate embedding
            query_embedding = self._embedding_client.embed_text(query_text)
            
            self.logger.debug(f"Generated query embedding with {len(query_embedding)} dimensions")
            
            # Add query embedding to context
            return {
                "query_embedding": query_embedding,
                "query_embedder": self.component_id
            }
        
        except Exception as e:
            error_msg = f"Error generating query embedding: {str(e)}"
            self.logger.error(error_msg)
            raise ComponentRegistryError(error_msg)
    
    def _initialize_embedding_client(self) -> None:
        """
        Initialize the embedding client using the LLM factory.
        
        Raises:
            ComponentRegistryError: If client initialization fails
        """
        try:
            factory = LLMFactory()
            self._embedding_client = factory.get_embedding_client(
                provider=self.embedding_provider,
                model_name=self.embedding_model
            )
            
            self.logger.debug(f"Initialized embedding client: {self.embedding_provider}/{self.embedding_model}")
        
        except Exception as e:
            raise ComponentRegistryError(f"Failed to initialize embedding client: {str(e)}")
    
    def validate_config(self) -> bool:
        """
        Validate the component configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        # Validate history_weight if history is included
        if self.include_history:
            history_weight = self.get_config_value("history_weight", 0.3)
            if not isinstance(history_weight, (int, float)) or history_weight < 0 or history_weight > 1:
                self.logger.warning("history_weight must be a number between 0 and 1")
                return False
        
        return True 
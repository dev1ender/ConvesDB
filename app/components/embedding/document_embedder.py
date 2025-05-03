"""
Document embedder component.
"""

import logging
from typing import Any, Dict, List, Optional

from app.components.base_component import BaseComponent
from app.core.exceptions import ComponentRegistryError
from app.llm.factory import LLMFactory


class DocumentEmbedder(BaseComponent):
    """
    Document embedding component.
    
    This component generates embeddings for documents using a configured
    embedding model and stores them in the context for later use.
    """
    
    def __init__(self, component_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the document embedder.
        
        Args:
            component_id: Unique identifier for the component
            config: Configuration parameters for the component
        """
        super().__init__(component_id, config)
        
        # Configuration options with defaults
        self.embedding_model = self.get_config_value("embedding_model", "text-embedding-3-small")
        self.embedding_provider = self.get_config_value("embedding_provider", "openai")
        self.batch_size = self.get_config_value("batch_size", 16)
        self.max_tokens = self.get_config_value("max_tokens", 8192)
        
        # Initialize the embedding client
        self._embedding_client = None
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the component to generate document embeddings.
        
        Args:
            context: Execution context containing documents to embed
            
        Returns:
            Dict[str, Any]: Updated context with document embeddings
            
        Raises:
            ComponentRegistryError: If embedding generation fails
        """
        self.logger.debug("Generating document embeddings")
        
        # Get documents from context
        documents = context.get("documents", [])
        
        if not documents:
            self.logger.warning("No documents found in context")
            return {"document_embeddings": [], "error": "No documents provided"}
        
        # Initialize embedding client if needed
        if not self._embedding_client:
            try:
                self._initialize_embedding_client()
            except Exception as e:
                error_msg = f"Failed to initialize embedding client: {str(e)}"
                self.logger.error(error_msg)
                raise ComponentRegistryError(error_msg)
        
        try:
            # Extract document texts
            document_texts = []
            for doc in documents:
                if isinstance(doc, str):
                    document_texts.append(doc)
                elif isinstance(doc, dict) and "content" in doc:
                    document_texts.append(doc["content"])
                else:
                    self.logger.warning(f"Skipping invalid document format: {type(doc)}")
            
            self.logger.debug(f"Embedding {len(document_texts)} documents")
            
            # Process in batches to avoid tokenization limits
            document_embeddings = []
            for i in range(0, len(document_texts), self.batch_size):
                batch = document_texts[i:i+self.batch_size]
                batch_embeddings = self._embedding_client.embed_texts(batch)
                document_embeddings.extend(batch_embeddings)
                self.logger.debug(f"Processed batch {i//self.batch_size + 1}/{(len(document_texts)-1)//self.batch_size + 1}")
            
            self.logger.debug(f"Generated {len(document_embeddings)} document embeddings")
            
            # Add document embeddings to context
            return {
                "document_embeddings": document_embeddings,
                "document_embedder": self.component_id
            }
        
        except Exception as e:
            error_msg = f"Error generating document embeddings: {str(e)}"
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
        # Validate batch_size
        batch_size = self.get_config_value("batch_size", 16)
        if not isinstance(batch_size, int) or batch_size <= 0:
            self.logger.warning("batch_size must be a positive integer")
            return False
        
        # Validate max_tokens
        max_tokens = self.get_config_value("max_tokens", 8192)
        if not isinstance(max_tokens, int) or max_tokens <= 0:
            self.logger.warning("max_tokens must be a positive integer")
            return False
        
        return True

    @classmethod
    def verify_embeddings(cls, config=None):
        """
        Verify that the embedding model can be initialized and used.
        Args:
            config: Optional config dict to override defaults
        Returns:
            bool: True if verification succeeds, False otherwise
        """
        print("\nVerifying DocumentEmbedder embedding model...")
        
        # Delegate to LLMFactory for actual verification
        return LLMFactory.verify_embeddings(config) 
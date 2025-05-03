"""
Copyright (c) 2024 dev1ender

This file is part of conversDB.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.

Factory for creating LLM and embedding clients.
"""

import logging
import os
from typing import Dict, Any, Optional

from app.interfaces.llm import LLMClient, EmbeddingClient
from app.core.exceptions import InitializationError
from app.llm.providers.openai_client import OpenAIClient, OpenAIEmbeddingClient
from app.llm.providers.ollama_client import OllamaClient, OllamaEmbeddingClient
from app.llm.providers.huggingface_client import HuggingFaceClient, HuggingFaceEmbeddingClient

logger = logging.getLogger("app.llm.factory")

class LLMFactory:
    """
    Factory for creating LLM and embedding clients.
    
    This class manages the creation and configuration of LLM and embedding
    clients based on provider type and configuration.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the factory with configuration.
        
        Args:
            config: Configuration dictionary for LLM providers
        """
        # Default empty config
        self.config = config or {}
    
    def get_llm_client(self, provider: str, model_name: Optional[str] = None, 
                       config_override: Optional[Dict[str, Any]] = None) -> LLMClient:
        """
        Get an LLM client for the specified provider.
        
        Args:
            provider: Provider name (openai, ollama, huggingface, local_huggingface)
            model_name: Name of the model to use
            config_override: Override configuration for this client
            
        Returns:
            LLMClient: Configured LLM client
            
        Raises:
            InitializationError: If client creation fails
        """
        provider = provider.lower()
        
        # Merge config with override
        effective_config = {
            **(self.config.get(provider, {}) if self.config else {}),
            **(config_override or {})
        }
        
        # Set model name if provided
        if model_name:
            effective_config["model"] = model_name
        
        try:
            if provider == "openai":
                api_key = effective_config.get("api_key") or os.environ.get("OPENAI_API_KEY")
                return OpenAIClient(
                    model=effective_config.get("model", "gpt-3.5-turbo"),
                    api_key=api_key,
                    temperature=effective_config.get("temperature", 0.0),
                    max_tokens=effective_config.get("max_tokens", 1000)
                )
            
            elif provider == "ollama":
                return OllamaClient(
                    model=effective_config.get("model", "llama3.2:3b"),
                    host=effective_config.get("host", "http://localhost:11434"),
                    temperature=effective_config.get("temperature", 0.0)
                )
            
            elif provider == "huggingface":
                api_key = effective_config.get("api_key") or os.environ.get("HUGGINGFACE_API_KEY")
                return HuggingFaceClient(
                    model=effective_config.get("model", "meta-llama/Llama-3.2-3B"),
                    api_key=api_key,
                    temperature=effective_config.get("temperature", 0.0),
                    local=False
                )
            
            elif provider == "local_huggingface":
                return HuggingFaceClient(
                    model=effective_config.get("model", "meta-llama/Llama-3.2-3B"),
                    temperature=effective_config.get("temperature", 0.0),
                    local=True,
                    max_tokens=effective_config.get("max_tokens", 1024)
                )
            
            else:
                raise InitializationError(f"Unsupported LLM provider: {provider}")
                
        except Exception as e:
            logger.error(f"Failed to create LLM client for provider {provider}: {str(e)}")
            raise InitializationError(f"Failed to create LLM client: {str(e)}")
    
    def get_embedding_client(self, provider: str, model_name: Optional[str] = None,
                            config_override: Optional[Dict[str, Any]] = None) -> EmbeddingClient:
        """
        Get an embedding client for the specified provider.
        
        Args:
            provider: Provider name (openai, ollama, huggingface, local_huggingface, local)
            model_name: Name of the model to use
            config_override: Override configuration for this client
            
        Returns:
            EmbeddingClient: Configured embedding client
            
        Raises:
            InitializationError: If client creation fails
        """
        provider = provider.lower()
        
        # Merge config with override
        effective_config = {
            **(self.config.get(provider, {}) if self.config else {}),
            **(config_override or {})
        }
        
        # Set model name if provided
        if model_name:
            effective_config["model"] = model_name
        
        try:
            if provider == "openai":
                api_key = effective_config.get("api_key") or os.environ.get("OPENAI_API_KEY")
                return OpenAIEmbeddingClient(
                    model=effective_config.get("model", "text-embedding-3-small"),
                    api_key=api_key
                )
            
            elif provider == "ollama":
                return OllamaEmbeddingClient(
                    model=effective_config.get("model", "llama3.2:3b"),
                    host=effective_config.get("host", "http://localhost:11434")
                )
            
            elif provider == "huggingface":
                api_key = effective_config.get("api_key") or os.environ.get("HUGGINGFACE_API_KEY")
                return HuggingFaceEmbeddingClient(
                    model=effective_config.get("model", "sentence-transformers/all-MiniLM-L6-v2"),
                    api_key=api_key
                )
            
            elif provider == "local_huggingface" or provider == "local":
                # For local embeddings, pass the model name without the local flag
                return HuggingFaceEmbeddingClient(
                    model=effective_config.get("model", "sentence-transformers/all-MiniLM-L6-v2"),
                    encode_kwargs=effective_config.get("encode_kwargs", {})
                )
            
            else:
                raise InitializationError(f"Unsupported embedding provider: {provider}")
                
        except Exception as e:
            logger.error(f"Failed to create embedding client for provider {provider}: {str(e)}")
            raise InitializationError(f"Failed to create embedding client: {str(e)}")

    @classmethod
    def verify_embeddings(cls, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Verify that the embedding model can be initialized and used.
        
        Args:
            config: Configuration for the embedding model including provider and model_name
                
        Returns:
            bool: True if verification succeeds, False otherwise
        """
        logger.info("Verifying embedding model...")
        
        # Use default config if not provided
        if config is None:
            config = {
                "embedding_provider": "local_huggingface",
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
            }
        
        try:
            # Extract provider and model name from config
            provider = config.get("embedding_provider", "local_huggingface")
            model = config.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
            logger.info(f"Testing {provider} provider with {model} model")
            
            # Create factory and client
            factory = cls()
            client = factory.get_embedding_client(provider, model_name=model)
            
            # Test if client responds
            test_text = "This is a test sentence for embedding verification."
            embedding = client.embed_text(test_text)
            
            if embedding and len(embedding) > 0:
                logger.info(f"✅ {provider} embeddings working with {len(embedding)} dimensions")
                return True
            else:
                logger.error(f"❌ {provider} embeddings failed: Empty embedding returned")
                return False
                
        except Exception as e:
            logger.error(f"❌ Embedding verification failed: {str(e)}")
            return False

    @classmethod
    def create_and_verify_test_embedding(cls, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create an actual test embedding and verify it has proper dimensions.
        
        Args:
            config: Configuration for the embedding model
                
        Returns:
            Dict[str, Any]: Result dictionary with success status and details
        """
        logger.info("Creating test embedding...")
        
        # Use default config if not provided
        if config is None:
            config = {
                "embedding_provider": "local_huggingface",
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
            }
        
        try:
            # Extract provider and model name from config
            provider = config.get("embedding_provider", "local_huggingface")
            model = config.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
            
            # Create factory and client
            factory = cls()
            client = factory.get_embedding_client(provider, model_name=model)
            
            # Test document
            test_text = "This is a test document for embedding creation verification."
            
            # Generate embedding
            embedding = client.embed_text(test_text)
            
            if embedding and len(embedding) > 0:
                logger.info(f"✅ Successfully created embedding with {len(embedding)} dimensions")
                return {
                    "success": True,
                    "dimensions": len(embedding),
                    "provider": provider,
                    "model": model
                }
            else:
                logger.error("❌ Failed to create embeddings: Empty embedding returned")
                return {
                    "success": False,
                    "error": "Empty embedding returned",
                    "provider": provider,
                    "model": model
                }
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Error creating test embedding: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "provider": config.get("embedding_provider", "unknown"),
                "model": config.get("embedding_model", "unknown")
            } 
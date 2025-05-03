"""
Factory for creating LLM and embedding clients.
"""

import os
import importlib
from typing import Dict, Any, Optional, Type

from app.interfaces.llm import LLMClient, EmbeddingClient
from app.interfaces.config import ConfigManagerInterface
from app.logging_setup import get_logger

# Setup module logger
logger = get_logger(__name__)

class LLMFactory:
    """Factory for creating LLM clients."""
    
    @staticmethod
    def create_llm_client(config_manager: ConfigManagerInterface) -> LLMClient:
        """Create an LLM client based on configuration.
        
        Args:
            config_manager: Configuration manager instance
            
        Returns:
            LLM client instance
        """
        provider = config_manager.get_llm_provider()
        logger.info(f"Creating LLM client for provider: {provider}")
        
        # Import the appropriate client dynamically
        if provider == "openai":
            from extensions.llm_providers import OpenAIClient
            
            # Get OpenAI configuration
            config = config_manager.get("llm.openai", {})
            model_name = config.get("model", "gpt-3.5-turbo")
            temperature = config.get("temperature", 0.0)
            max_tokens = config.get("max_tokens", 500)
            
            logger.info(f"Initializing OpenAI with model: {model_name}, temperature: {temperature}")
            return OpenAIClient(model_name=model_name, temperature=temperature, max_tokens=max_tokens)
            
        elif provider == "ollama":
            from extensions.llm_providers import OllamaClient
            
            # Get Ollama configuration
            config = config_manager.get("llm.ollama", {})
            model_name = config.get("model", "llama3:3b")
            temperature = config.get("temperature", 0.0)
            host = config.get("host", "http://localhost:11434")
            
            logger.info(f"Initializing Ollama with model: {model_name}, temperature: {temperature}")
            return OllamaClient(model_name=model_name, temperature=temperature, host=host)
            
        else:
            # Try to dynamically import a custom provider
            try:
                logger.info(f"Attempting to load custom LLM provider: {provider}")
                module_path = f"extensions.llm_providers"
                module = importlib.import_module(module_path)
                
                # Construct the expected class name (e.g., "CustomClient")
                class_name = f"{provider.capitalize()}Client"
                client_class = getattr(module, class_name)
                
                # Get configuration for this provider
                config = config_manager.get(f"llm.{provider}", {})
                logger.info(f"Initializing custom LLM provider: {provider}")
                return client_class(**config)
                
            except (ImportError, AttributeError) as e:
                error_msg = f"Failed to load LLM provider '{provider}': {str(e)}"
                logger.error(error_msg)
                raise ValueError(error_msg)
    
    @staticmethod
    def create_embedding_client(model_name: str, config: Dict[str, Any]) -> EmbeddingClient:
        """Create an embedding client based on configuration.
        
        Args:
            model_name: Name of the embedding model to use
            config: Configuration for the embedding model
            
        Returns:
            Embedding client instance
        """
        logger.info(f"Creating embedding client for model: {model_name}")
        
        # Import the appropriate client based on model name
        if model_name.lower() in ["openai", "ada", "text-embedding-ada"]:
            # Import dynamically to avoid hard dependencies
            try:
                from app.llm.embedding.openai_embedding import OpenAIEmbedding
                logger.info(f"Initializing OpenAI embedding model")
                return OpenAIEmbedding()
            except ImportError:
                logger.error("Failed to import OpenAI embedding module")
                raise
                
        elif model_name.lower() in ["local", "huggingface", "sentence-transformers"]:
            # Import dynamically to avoid hard dependencies
            try:
                from app.llm.embedding.local_embedding import LocalEmbedding
                logger.info(f"Initializing local embedding model")
                return LocalEmbedding(config.get("model_name", "all-MiniLM-L6-v2"))
            except ImportError:
                logger.error("Failed to import local embedding module")
                raise
                
        else:
            # Try to dynamically import a custom embedding provider
            try:
                logger.info(f"Attempting to load custom embedding model: {model_name}")
                module_path = f"extensions.embedding_providers"
                module = importlib.import_module(module_path)
                
                # Construct the expected class name
                class_name = f"{model_name.capitalize()}Embedding"
                embedding_class = getattr(module, class_name)
                
                logger.info(f"Initializing custom embedding model: {model_name}")
                return embedding_class(**config)
                
            except (ImportError, AttributeError) as e:
                error_msg = f"Failed to load embedding model '{model_name}': {str(e)}"
                logger.error(error_msg)
                raise ValueError(error_msg) 
"""
Copyright (c) 2024 dev1ender

This file is part of conversDB.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.

Ollama LLM client implementation.
"""

import logging
from typing import List, Dict, Any, Optional, Union

from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage

from app.interfaces.llm import LLMClient, EmbeddingClient
from app.core.exceptions import InitializationError

logger = logging.getLogger("app.llm.providers.ollama")

class OllamaClient(LLMClient):
    """
    Ollama LLM client implementation.
    
    This client uses the langchain_community package to interact with
    locally hosted Ollama models for text generation.
    """
    
    def __init__(self, 
                model: str = "llama3.2:3b", 
                host: str = "http://localhost:11434",
                temperature: float = 0.0,
                **kwargs):
        """
        Initialize the Ollama client.
        
        Args:
            model: The model to use
            host: URL to the Ollama server
            temperature: Sampling temperature (0.0 to 1.0)
            **kwargs: Additional parameters for the Ollama API
        """
        self.model_name = model
        self.host = host
        self.temperature = temperature
        self.client_kwargs = kwargs
        
        try:
            # Initialize LangChain client
            self.client = ChatOllama(
                model=self.model_name,
                base_url=self.host,
                temperature=self.temperature,
                **self.client_kwargs
            )
            logger.debug(f"Initialized Ollama client with model: {model}")
        
        except Exception as e:
            logger.error(f"Failed to initialize Ollama client: {str(e)}")
            raise InitializationError(f"Failed to initialize Ollama client: {str(e)}")
    
    def generate(self, prompt: str) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            str: The generated response
        """
        try:
            messages = [HumanMessage(content=prompt)]
            response = self.client.invoke(messages)
            
            # Extract content from response
            return response.content
        
        except Exception as e:
            logger.error(f"Error generating response from Ollama: {str(e)}")
            return f"Error: {str(e)}"
    
    def generate_with_system_prompt(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generate a response using a system prompt and user prompt.
        
        Args:
            system_prompt: The system prompt to set context
            user_prompt: The user prompt to send to the LLM
            
        Returns:
            str: The generated response
        """
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            response = self.client.invoke(messages)
            
            # Extract content from response
            return response.content
        
        except Exception as e:
            logger.error(f"Error generating response from Ollama: {str(e)}")
            return f"Error: {str(e)}"


class OllamaEmbeddingClient(EmbeddingClient):
    """
    Ollama embedding client implementation.
    
    This client uses the langchain_community package to interact with
    locally hosted Ollama models for embedding generation.
    """
    
    def __init__(self, 
                model: str = "llama3.2:3b", 
                host: str = "http://localhost:11434",
                **kwargs):
        """
        Initialize the Ollama embedding client.
        
        Args:
            model: The embedding model to use
            host: URL to the Ollama server
            **kwargs: Additional parameters for the Ollama API
        """
        self.model_name = model
        self.host = host
        self.client_kwargs = kwargs
        
        try:
            # Initialize LangChain embeddings client
            self.client = OllamaEmbeddings(
                model=self.model_name,
                base_url=self.host,
                **self.client_kwargs
            )
            logger.debug(f"Initialized Ollama embedding client with model: {model}")
        
        except Exception as e:
            logger.error(f"Failed to initialize Ollama embedding client: {str(e)}")
            raise InitializationError(f"Failed to initialize Ollama embedding client: {str(e)}")
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate an embedding for a single text string.
        
        Args:
            text: Text to embed
            
        Returns:
            List[float]: Embedding vector
        """
        try:
            return self.client.embed_query(text)
        
        except Exception as e:
            logger.error(f"Error generating embedding from Ollama: {str(e)}")
            raise Exception(f"Error generating embedding: {str(e)}")
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of text strings.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List[List[float]]: List of embedding vectors
        """
        try:
            return self.client.embed_documents(texts)
        
        except Exception as e:
            logger.error(f"Error generating embeddings from Ollama: {str(e)}")
            raise Exception(f"Error generating embeddings: {str(e)}") 
"""
Copyright (c) 2024 dev1ender

This file is part of conversDB.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.

OpenAI LLM client implementation.
"""

import logging
import os
from typing import List, Dict, Any, Optional, Union

from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage

from app.interfaces.llm import LLMClient, EmbeddingClient
from app.core.exceptions import InitializationError

logger = logging.getLogger("app.llm.providers.openai")

class OpenAIClient(LLMClient):
    """
    OpenAI LLM client implementation.
    
    This client uses the langchain_openai package to interact with
    OpenAI's API for text generation.
    """
    
    def __init__(self, 
                model: str = "gpt-3.5-turbo", 
                api_key: Optional[str] = None,
                temperature: float = 0.0,
                max_tokens: int = 1000,
                **kwargs):
        """
        Initialize the OpenAI client.
        
        Args:
            model: The model to use
            api_key: OpenAI API key
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for the OpenAI API
        """
        self.model_name = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        
        if not self.api_key:
            raise InitializationError("OpenAI API key is required")
        
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client_kwargs = kwargs
        
        try:
            # Initialize LangChain client
            self.client = ChatOpenAI(
                model=self.model_name,
                api_key=self.api_key,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **self.client_kwargs
            )
            logger.debug(f"Initialized OpenAI client with model: {model}")
        
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            raise InitializationError(f"Failed to initialize OpenAI client: {str(e)}")
    
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
            logger.error(f"Error generating response from OpenAI: {str(e)}")
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
            logger.error(f"Error generating response from OpenAI: {str(e)}")
            return f"Error: {str(e)}"


class OpenAIEmbeddingClient(EmbeddingClient):
    """
    OpenAI embedding client implementation.
    
    This client uses the langchain_openai package to interact with
    OpenAI's embedding API.
    """
    
    def __init__(self, 
                model: str = "text-embedding-3-small", 
                api_key: Optional[str] = None,
                **kwargs):
        """
        Initialize the OpenAI embedding client.
        
        Args:
            model: The embedding model to use
            api_key: OpenAI API key
            **kwargs: Additional parameters for the OpenAI API
        """
        self.model_name = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        
        if not self.api_key:
            raise InitializationError("OpenAI API key is required")
        
        self.client_kwargs = kwargs
        
        try:
            # Initialize LangChain embeddings client
            self.client = OpenAIEmbeddings(
                model=self.model_name,
                openai_api_key=self.api_key,
                **self.client_kwargs
            )
            logger.debug(f"Initialized OpenAI embedding client with model: {model}")
        
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI embedding client: {str(e)}")
            raise InitializationError(f"Failed to initialize OpenAI embedding client: {str(e)}")
    
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
            logger.error(f"Error generating embedding from OpenAI: {str(e)}")
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
            logger.error(f"Error generating embeddings from OpenAI: {str(e)}")
            raise Exception(f"Error generating embeddings: {str(e)}") 
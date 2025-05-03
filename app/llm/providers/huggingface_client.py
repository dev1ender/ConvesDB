"""
Copyright (c) 2024 dev1ender

This file is part of conversDB.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.

Local LLM client implementation using HuggingFace transformers library.
"""

import logging
import os
from typing import List, Dict, Any, Optional, Union
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from langchain_community.embeddings import HuggingFaceEmbeddings

from app.interfaces.llm import LLMClient, EmbeddingClient
from app.core.exceptions import InitializationError

logger = logging.getLogger("app.llm.providers.local_llm")

class HuggingFaceClient(LLMClient):
    """
    Local HuggingFace implementation of LLMClient using transformers pipeline.
    """
    
    def __init__(self, 
                 model: str = "meta-llama/Llama-3.2-3B", 
                 temperature: float = 0.7,
                 max_tokens: int = 256,
                 **kwargs):
        """
        Initialize the local HuggingFace client using transformers pipeline.
        
        Args:
            model: The model to use
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for the model
        """
        self.model_name = model
        self.temperature = temperature
        self.max_new_tokens = max_tokens
        
        # Filter out unsupported parameters to avoid errors
        self.client_kwargs = {k: v for k, v in kwargs.items() if k not in ['local']}
        
        # Set do_sample based on temperature
        self.do_sample = True
        if self.temperature <= 0.0:
            # For temperature 0, use greedy decoding
            self.temperature = 0.1  # small but positive value
            self.do_sample = False
        
        try:
            logger.info(f"Initializing local HuggingFace LLM client with model: {self.model_name}, temperature: {self.temperature}, do_sample: {self.do_sample}")
            self._init_pipeline()
            logger.debug(f"Initialized local LLM client with model: {model}")
        
        except Exception as e:
            logger.error(f"Failed to initialize local LLM client: {str(e)}")
            raise InitializationError(f"Failed to initialize local LLM client: {str(e)}")
    
    def _init_pipeline(self):
        """
        Initialize a local transformers pipeline for inference.
        
        If the model doesn't exist locally, it will be downloaded automatically.
        """
        try:
            # Set device to GPU if available
            device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
            logger.debug(f"Using device: {device} for local model")
            print(f"Device set to use {device}")
            
            # Load tokenizer
            logger.debug(f"Loading tokenizer for {self.model_name}...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # Load model
            logger.debug(f"Loading model {self.model_name}...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32
            )
            
            # Create the pipeline
            self.pipe = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if device == "cuda" else device,
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize local transformers pipeline: {str(e)}")
            raise InitializationError(f"Failed to initialize local transformers pipeline: {str(e)}")
    
    def generate(self, prompt: str) -> str:
        """
        Generate a response from the local HuggingFace model using transformers pipeline.
        
        Args:
            prompt: The input prompt string
            
        Returns:
            str: The generated response
        """
        try:
            logger.info(f"Generating response from local HuggingFace model (prompt length: {len(prompt)} chars)")
            outputs = self.pipe(
                prompt,
                max_new_tokens=self.max_new_tokens,
                temperature=self.temperature,
                do_sample=self.do_sample,
                pad_token_id=self.tokenizer.eos_token_id,
            )
            
            # Get the raw generated text after the prompt
            raw_output = outputs[0]["generated_text"][len(prompt):].strip()
            
            # Clean up the output - remove common prefixes like "Expected Answer:" or "SQL:"
            common_prefixes = ["Expected Answer:", "SQL:", "Answer:", "Query:"]
            cleaned_output = raw_output
            for prefix in common_prefixes:
                if cleaned_output.startswith(prefix):
                    cleaned_output = cleaned_output[len(prefix):].strip()
                    logger.debug(f"Removed prefix '{prefix}' from model output")
                    break
            
            return cleaned_output
        
        except Exception as e:
            logger.error(f"Error generating response from local LLM: {str(e)}")
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
            # Format prompt following Llama 3.2 conventions
            prompt = f"<s>[INST] {system_prompt}\n\n{user_prompt} [/INST]"
            
            logger.info(f"Generating response with system prompt from local HuggingFace model")
            outputs = self.pipe(
                prompt,
                max_new_tokens=self.max_new_tokens,
                temperature=self.temperature,
                do_sample=self.do_sample,
                pad_token_id=self.tokenizer.eos_token_id,
            )
            
            # Get the raw generated text after the prompt
            raw_output = outputs[0]["generated_text"][len(prompt):].strip()
            
            # Clean up the output
            common_prefixes = ["Expected Answer:", "SQL:", "Answer:", "Query:"]
            cleaned_output = raw_output
            for prefix in common_prefixes:
                if cleaned_output.startswith(prefix):
                    cleaned_output = cleaned_output[len(prefix):].strip()
                    logger.debug(f"Removed prefix '{prefix}' from model output")
                    break
            
            return cleaned_output
        
        except Exception as e:
            logger.error(f"Error generating response from local LLM: {str(e)}")
            return f"Error: {str(e)}"


class HuggingFaceEmbeddingClient(EmbeddingClient):
    """
    Local embedding client implementation using HuggingFace models.
    
    This client uses the transformers library to run embedding models locally.
    """
    
    def __init__(self, 
                 model: str = "sentence-transformers/all-MiniLM-L6-v2", 
                 **kwargs):
        """
        Initialize the local embedding client.
        
        Args:
            model: The embedding model to use
            **kwargs: Additional parameters for the embedding model
        """
        self.model_name = model
        
        # Filter out parameters that aren't supported by HuggingFaceEmbeddings
        unsupported_params = ['local', 'provider', 'embedding_provider']
        self.client_kwargs = {k: v for k, v in kwargs.items() if k not in unsupported_params}
        
        try:
            # Set device to CUDA if available
            device = "cuda" if self._is_cuda_available() else "cpu"
            logger.debug(f"Using device: {device} for embedding model")
            
            # Create embedding settings with proper parameters
            model_kwargs = {"device": device}
            
            # Initialize embedding model with fixed parameters
            self.client = HuggingFaceEmbeddings(
                model_name=self.model_name,
                model_kwargs=model_kwargs,
                encode_kwargs=self.client_kwargs.get('encode_kwargs', {})
            )
            logger.debug(f"✅ Successfully initialized embedding client with model: {model}")
        
        except Exception as e:
            logger.error(f"Failed to initialize local embedding client: {str(e)}")
            raise InitializationError(f"Failed to initialize local embedding client: {str(e)}")
    
    def _is_cuda_available(self):
        """Check if CUDA is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
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
            logger.error(f"Error generating embedding: {str(e)}")
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
            logger.error(f"Error generating embeddings: {str(e)}")
            raise Exception(f"Error generating embeddings: {str(e)}") 
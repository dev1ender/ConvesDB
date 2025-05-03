import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from app.query_generator import LLMClient
from app.logging_setup import get_logger

# Setup module logger
logger = get_logger(__name__)

# Load environment variables from .env file
load_dotenv()

class OpenAIClient(LLMClient):
    """OpenAI implementation of LLMClient."""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", temperature: float = 0.0, max_tokens: int = 500):
        try:
            from langchain_openai import ChatOpenAI
            self.api_key = os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                logger.error("OPENAI_API_KEY environment variable not set")
                raise ValueError("OPENAI_API_KEY environment variable not set")
            
            logger.info(f"Initializing OpenAI LLM client with model: {model_name}, temperature: {temperature}")
            logger.debug(f"OpenAI configuration: max_tokens={max_tokens}")
                
            self.llm = ChatOpenAI(
                model=model_name,
                temperature=temperature,
                api_key=self.api_key,
                max_tokens=max_tokens
            )
            logger.info("OpenAI LLM client initialized successfully")
        except ImportError:
            logger.error("langchain_openai package not installed")
            raise ImportError("langchain_openai package not installed. Install with 'pip install langchain-openai'")
    
    def generate(self, prompt: str) -> str:
        """Generate a response from OpenAI."""
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            
            # Extract the instruction part (before the user question)
            parts = prompt.split("User Question:", 1)
            
            prompt_length = len(prompt)
            logger.info(f"Generating response from OpenAI (prompt length: {prompt_length} chars)")
            logger.debug(f"Prompt first 100 chars: {prompt[:100]}...")
            
            if len(parts) == 2:
                logger.debug("Prompt contains system/user message split")
                system_content = parts[0].strip()
                user_content = "User Question: " + parts[1].strip()
                
                messages = [
                    SystemMessage(content=system_content),
                    HumanMessage(content=user_content)
                ]
                logger.debug(f"Using structured messages: system ({len(system_content)} chars) + user ({len(user_content)} chars)")
            else:
                # If no "User Question:" marker, use the entire prompt as user message
                logger.debug("Using entire prompt as user message (no system/user split)")
                messages = [HumanMessage(content=prompt)]
            
            logger.debug("Sending request to OpenAI API")
            start_time = __import__('time').time()
            response = self.llm.invoke(messages)
            duration = __import__('time').time() - start_time
            
            result = response.content.strip()
            result_length = len(result)
            
            logger.info(f"Received response from OpenAI in {duration:.2f}s ({result_length} chars)")
            logger.debug(f"Response first 100 chars: {result[:100]}...")
            
            return result
            
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            logger.error(error_msg)
            return error_msg


class OllamaClient(LLMClient):
    """Ollama implementation of LLMClient."""
    
    def __init__(self, model_name: str = None, temperature: float = 0.0, host: str = None):
        # Check for model name in environment variables or use default
        self.model_name = model_name or os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        self.temperature = temperature
        self.base_url = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        
        logger.info(f"Initializing Ollama LLM client with model: {self.model_name}, temperature: {temperature}")
        logger.debug(f"Ollama host: {self.base_url}")
        
        try:
            from langchain_ollama import ChatOllama
            
            # Initialize Ollama client using ChatOllama
            logger.debug("Creating ChatOllama instance")
            self.llm = ChatOllama(
                model=self.model_name,
                temperature=self.temperature,
                base_url=self.base_url
            )
            logger.info(f"Initialized ChatOllama with model: {self.model_name} at {self.base_url}")
            
        except ImportError:
            logger.error("langchain_ollama package not installed")
            raise ImportError("langchain_ollama package not installed. Install with 'pip install langchain-ollama'")
    
    def generate(self, prompt: str) -> str:
        """Generate a response from Ollama."""
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            
            # Extract the instruction part (before the user question)
            parts = prompt.split("User Question:", 1)
            
            prompt_length = len(prompt)
            logger.info(f"Generating response from Ollama (prompt length: {prompt_length} chars)")
            logger.debug(f"Prompt first 100 chars: {prompt[:100]}...")
            
            start_time = __import__('time').time()
            
            if len(parts) == 2:
                logger.debug("Prompt contains system/user message split")
                system_content = parts[0].strip()
                user_content = "User Question: " + parts[1].strip()
                
                # For Ollama, format the messages
                formatted_prompt = f"<s>[INST] {system_content}\n\n{user_content} [/INST]</s>"
                logger.debug(f"Using formatted instruction prompt ({len(formatted_prompt)} chars)")
                response = self.llm.invoke(formatted_prompt)
            else:
                # If no "User Question:" marker, use the entire prompt
                logger.debug("Using entire prompt (no system/user split)")
                response = self.llm.invoke(prompt)
            
            duration = __import__('time').time() - start_time
            
            # Handle response correctly based on type
            if hasattr(response, 'content'):
                # It's an AIMessage or similar object with content attribute
                result = str(response.content)
            else:
                # It's a string or other type
                result = str(response)
                
            result = result.strip()
            result_length = len(result)
            
            logger.info(f"Received response from Ollama in {duration:.2f}s ({result_length} chars)")
            logger.debug(f"Response first 100 chars: {result[:100]}...")
                
            return result
            
        except Exception as e:
            error_msg = str(e)
            # Check for common Ollama connection issues
            if "connect: connection refused" in error_msg:
                error_msg = f"Error: Could not connect to Ollama server at {self.base_url}. Make sure Ollama is running with 'ollama serve'"
                logger.error(f"Connection error to Ollama server: {error_msg}")
            elif "model not found" in error_msg.lower():
                error_msg = f"Error: Model '{self.model_name}' not found. Try installing it with 'ollama pull {self.model_name}'"
                logger.error(f"Model not found: {error_msg}")
            else:
                error_msg = f"Error generating response: {error_msg}"
                logger.error(error_msg)
            
            return error_msg 
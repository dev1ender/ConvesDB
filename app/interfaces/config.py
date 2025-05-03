"""
Configuration interfaces for the RAG-POC application.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class ConfigManagerInterface(ABC):
    """Interface for configuration manager."""
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        pass
    
    @abstractmethod
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        pass
    
    @abstractmethod
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration."""
        pass
    
    @abstractmethod
    def get_schema_agent_config(self) -> Dict[str, Any]:
        """Get schema agent configuration."""
        pass
    
    @abstractmethod
    def get_prompt_agent_config(self) -> Dict[str, Any]:
        """Get prompt agent configuration."""
        pass
    
    @abstractmethod
    def get_query_generator_config(self) -> Dict[str, Any]:
        """Get query generator configuration."""
        pass
    
    @abstractmethod
    def get_query_executor_config(self) -> Dict[str, Any]:
        """Get query executor configuration."""
        pass 
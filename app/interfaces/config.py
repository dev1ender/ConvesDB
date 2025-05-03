"""
Copyright (c) 2024 dev1ender

This file is part of conversDB.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.

Configuration interfaces for the conversDB application.
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
    def get_document_store_config(self) -> Dict[str, Any]:
        """Get document store configuration."""
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
"""
Configuration manager for the RAG-POC application.
Loads and manages configuration from config.yml file.
"""

import os
import yaml
from dotenv import load_dotenv
from typing import Any, Dict, Optional
import re
from app.interfaces.config import ConfigManagerInterface

class ConfigManager(ConfigManagerInterface):
    """Loads and manages application configuration."""
    
    def __init__(self, config_path: str = "config.yml"):
        """Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file
        """
        # Load environment variables first
        load_dotenv()
        
        # Store configuration path
        self.config_path = config_path
        
        # Load configuration
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
            
            # Process environment variable placeholders
            config = self._process_env_vars(config)
            
            return config
        except FileNotFoundError:
            print(f"Warning: Configuration file '{self.config_path}' not found. Using default settings.")
            return {}
        except yaml.YAMLError as e:
            print(f"Error parsing configuration file: {e}")
            return {}
    
    def _process_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Process environment variable placeholders in the configuration.
        
        Example: "${OPENAI_API_KEY}" will be replaced with the value of the
        OPENAI_API_KEY environment variable.
        """
        if isinstance(config, dict):
            return {k: self._process_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._process_env_vars(item) for item in config]
        elif isinstance(config, str):
            # Replace ${ENV_VAR} with the value of the environment variable
            env_var_pattern = r'\${([A-Za-z0-9_]+)}'
            matches = re.findall(env_var_pattern, config)
            
            if matches:
                result = config
                for env_var in matches:
                    env_value = os.getenv(env_var, "")
                    result = result.replace(f"${{{env_var}}}", env_value)
                return result
            return config
        else:
            return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key.
        
        Args:
            key: Dot-separated key path (e.g., "database.path")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_llm_provider(self) -> str:
        """Get the configured LLM provider.
        
        Returns:
            LLM provider name ("openai" or "ollama")
        """
        return self.get("llm.provider", "ollama")
    
    def is_using_openai(self) -> bool:
        """Check if OpenAI is the configured LLM provider.
        
        Returns:
            True if using OpenAI, False otherwise
        """
        return self.get_llm_provider() == "openai"
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration.
        
        Returns:
            Database configuration dictionary
        """
        return self.get("database", {})
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration.
        
        Returns:
            LLM configuration dictionary for the current provider
        """
        provider = self.get_llm_provider()
        return self.get(f"llm.{provider}", {})
    
    def get_schema_agent_config(self) -> Dict[str, Any]:
        """Get schema agent configuration.
        
        Returns:
            Schema agent configuration dictionary
        """
        return self.get("schema_agent", {})
    
    def get_prompt_agent_config(self) -> Dict[str, Any]:
        """Get prompt agent configuration.
        
        Returns:
            Prompt agent configuration dictionary
        """
        return self.get("prompt_agent", {})
    
    def get_query_generator_config(self) -> Dict[str, Any]:
        """Get query generator configuration.
        
        Returns:
            Query generator configuration dictionary
        """
        return self.get("query_generator", {})
    
    def get_query_executor_config(self) -> Dict[str, Any]:
        """Get query executor configuration.
        
        Returns:
            Query executor configuration dictionary
        """
        return self.get("query_executor", {})
    
    def get_ui_config(self) -> Dict[str, Any]:
        """Get UI configuration.
        
        Returns:
            UI configuration dictionary
        """
        return self.get("ui", {}) 
"""
Configuration loading utilities.
"""

import logging
import os
from typing import Any, Dict, List, Optional
from pathlib import Path
import yaml

from app.core.exceptions import ConfigurationError


class ConfigLoader:
    """
    Utility for loading and managing configuration.
    
    This class is responsible for:
    1. Loading configuration files
    2. Merging configurations from different sources
    3. Providing access to configuration values
    4. Validating configuration structure
    """
    
    def __init__(self, config_dir: Optional[str] = None, main_config_path: Optional[str] = None):
        """
        Initialize the configuration loader.
        
        Args:
            config_dir: Directory containing configuration files
            main_config_path: Path to the main configuration file
        """
        self.logger = logging.getLogger("core.config_loader")
        self.config_dir = config_dir
        self.main_config_path = main_config_path or (os.path.join(config_dir, "main.yaml") if config_dir else None)
        
        # Main configuration dictionary
        self._config: Dict[str, Any] = {}
        
        # Service-specific configurations
        self._service_configs: Dict[str, Dict[str, Any]] = {}
        
        # Load configuration if paths are provided
        if self.main_config_path:
            self._load_main_config()
            
        if self.config_dir:
            self._load_service_configs()
    
    def _load_main_config(self) -> None:
        """
        Load the main configuration file.
        
        Raises:
            ConfigurationError: If loading fails
        """
        try:
            if not os.path.exists(self.main_config_path):
                raise ConfigurationError(f"Main configuration file not found: {self.main_config_path}")
            
            with open(self.main_config_path, 'r') as file:
                self._config = yaml.safe_load(file) or {}
                
            self.logger.info(f"Loaded main configuration from {self.main_config_path}")
        
        except Exception as e:
            raise ConfigurationError(f"Failed to load main configuration: {str(e)}")
    
    def _load_service_configs(self) -> None:
        """
        Load service-specific configuration files.
        
        Raises:
            ConfigurationError: If loading fails
        """
        try:
            services_dir = os.path.join(self.config_dir, "services")
            if not os.path.exists(services_dir):
                self.logger.debug(f"Services configuration directory not found: {services_dir}")
                return
            
            # Get enabled services from main config
            enabled_services = self._config.get("enabled_services", [])
            
            for service_file in os.listdir(services_dir):
                if not service_file.endswith((".yaml", ".yml")):
                    continue
                
                service_name = os.path.splitext(service_file)[0]
                
                # Skip disabled services
                if enabled_services and service_name not in enabled_services:
                    self.logger.debug(f"Skipping disabled service: {service_name}")
                    continue
                
                service_path = os.path.join(services_dir, service_file)
                
                try:
                    with open(service_path, 'r') as file:
                        service_config = yaml.safe_load(file) or {}
                        
                    self._service_configs[service_name] = service_config
                    self.logger.debug(f"Loaded service configuration: {service_name}")
                    
                except Exception as e:
                    self.logger.warning(f"Error loading service configuration {service_file}: {str(e)}")
            
            self.logger.info(f"Loaded {len(self._service_configs)} service configurations")
        
        except Exception as e:
            raise ConfigurationError(f"Failed to load service configurations: {str(e)}")
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the complete configuration.
        
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        return self._config
    
    def get_service_config(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        Get service-specific configuration.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Optional[Dict[str, Any]]: Service configuration or None if not found
        """
        return self._service_configs.get(service_name)
    
    def get_value(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value using a dot-notation path.
        
        Args:
            key_path: Dot-notation path (e.g., "app.log_level")
            default: Default value if key is not found
            
        Returns:
            Any: Configuration value or default if not found
        """
        config = self._config
        keys = key_path.split('.')
        
        for key in keys:
            if isinstance(config, dict) and key in config:
                config = config[key]
            else:
                return default
        
        return config
    
    def set_value(self, key_path: str, value: Any) -> None:
        """
        Set a configuration value using a dot-notation path.
        
        Args:
            key_path: Dot-notation path (e.g., "app.log_level")
            value: Value to set
        """
        config = self._config
        keys = key_path.split('.')
        
        for i, key in enumerate(keys[:-1]):
            if key not in config:
                config[key] = {}
            
            config = config[key]
        
        config[keys[-1]] = value
    
    def get_enabled_services(self) -> List[str]:
        """
        Get list of enabled services.
        
        Returns:
            List[str]: List of enabled service names
        """
        return self._config.get("enabled_services", []) 
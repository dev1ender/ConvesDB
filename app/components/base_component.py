"""
Base component implementation.
"""

import logging
from typing import Any, Dict, Optional

from app.interfaces.component import Component
from app.utils.logging_setup import TICK_ICON, CROSS_ICON


class BaseComponent(Component):
    """
    Base implementation of the Component interface.
    
    This class provides common functionality for all components and
    should be extended by concrete component implementations.
    """
    
    def __init__(self, component_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base component.
        
        Args:
            component_id: Unique identifier for the component
            config: Configuration parameters for the component
        """
        super().__init__(component_id, config)
        self.logger = logging.getLogger(f"components.{self.__class__.__name__.lower()}")
        self.logger.debug(f"{TICK_ICON} Creating {self.__class__.__name__} with id {component_id}")
    
    def execute(self, context: Dict[str, Any]) -> Any:
        """
        Execute the component's functionality.
        
        This implementation raises NotImplementedError and should be
        overridden by subclasses to perform actual execution.
        
        Args:
            context: Execution context containing input data and workflow state
            
        Returns:
            Any: Result of the component execution
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        self.logger.debug(f"Executing component {self.component_id} ({self.__class__.__name__})")
        raise NotImplementedError(f"Component {self.component_id} does not implement execute method")
    
    def validate_config(self) -> bool:
        """
        Validate the component's configuration.
        
        This implementation always returns True but should be overridden
        by subclasses to perform actual validation.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        self.logger.debug(f"Validating config for component {self.component_id}")
        # This implementation always returns True but should be overridden
        valid = True
        if valid:
            self.logger.info(f"{TICK_ICON} Config validated for component {self.component_id}")
        else:
            self.logger.warning(f"{CROSS_ICON} Config validation failed for component {self.component_id}")
        return valid
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key is not found
            
        Returns:
            Any: Configuration value or default if not found
        """
        value = self.config.get(key, default)
        self.logger.debug(f"Getting config value for key '{key}' in component {self.component_id}: {value}")
        return value
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get component metadata.
        
        This implementation adds the component type to the base metadata.
        
        Returns:
            Dict[str, Any]: Component metadata
        """
        metadata = super().get_metadata()
        metadata.update({
            "component_type": self.__class__.__name__,
            "configurable": True
        })
        self.logger.debug(f"Metadata for component {self.component_id}: {metadata}")
        return metadata 
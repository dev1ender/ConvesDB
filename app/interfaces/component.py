"""
Component interface for the service-based architecture.

This file defines the base interface that all components must implement.
Components are the building blocks of the workflow system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class Component(ABC):
    """
    Base interface for all components in the system.
    
    Components are the building blocks of the application and are responsible for
    performing specific tasks in the workflow pipeline.
    """
    
    def __init__(self, component_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the component.
        
        Args:
            component_id: Unique identifier for the component
            config: Configuration parameters for the component
        """
        self.component_id = component_id
        self.config = config or {}
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Any:
        """
        Execute the component's primary functionality.
        
        This is the main entry point for component execution.
        
        Args:
            context: Execution context containing input data and workflow state
            
        Returns:
            Any: Result of the component execution
        """
        pass
    
    def validate_config(self) -> bool:
        """
        Validate the component's configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        return True
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get component metadata.
        
        Returns:
            Dict[str, Any]: Component metadata
        """
        return {
            "component_id": self.component_id,
            "type": self.__class__.__name__
        }
    
    def cleanup(self) -> None:
        """Clean up resources used by the component."""
        pass 
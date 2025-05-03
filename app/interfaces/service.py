"""
Service interface for the service-based architecture.

This file defines the interface for services, which represent
different database backends (SQLite, PostgreSQL, Neo4j) and
manage specific components and workflows.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from .workflow import Workflow

class Service(ABC):
    """
    Base interface for all services in the system.
    
    Services are long-running components that provide functionality to the application
    throughout its lifecycle.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the service.
        
        Args:
            config: Configuration parameters for the service
        """
        self.config = config or {}
        self.initialized = False
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the service.
        
        This method is called during application startup to set up the service.
        It should establish connections, allocate resources, etc.
        
        Returns:
            bool: True if initialization was successful
        """
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """
        Shutdown the service.
        
        This method is called during application shutdown to clean up resources.
        It should close connections, release resources, etc.
        """
        pass
    
    def health_check(self) -> bool:
        """
        Check if the service is healthy.
        
        Returns:
            bool: True if service is healthy, False otherwise
        """
        return self.initialized
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get service status information.
        
        Returns:
            Dict[str, Any]: Service status information
        """
        return {
            "initialized": self.initialized,
            "type": self.__class__.__name__
        }
    
    @abstractmethod
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Optional[Workflow]: Workflow instance or None if not found
        """
        pass
    
    @abstractmethod
    def execute_workflow(self, workflow_id: str, input_data: Dict[str, Any],
                        start_stage: Optional[str] = None,
                        end_stage: Optional[str] = None) -> Dict[str, Any]:
        """Execute a workflow with the given input data.
        
        Args:
            workflow_id: Workflow identifier
            input_data: Input data for the workflow
            start_stage: Optional stage to start from
            end_stage: Optional stage to end at
            
        Returns:
            Dict[str, Any]: Workflow execution results
        """
        pass
    
    @abstractmethod
    def process_query(self, query: str, **kwargs) -> Dict[str, Any]:
        """Process a natural language query using the service.
        
        Args:
            query: Natural language query
            **kwargs: Additional parameters
            
        Returns:
            Dict[str, Any]: Query processing result
        """
        pass
    
    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Get service metadata including capabilities and version.
        
        Returns:
            Dict[str, Any]: Service metadata
        """
        pass
    
    def cleanup(self) -> None:
        """Clean up resources used by the service."""
        pass 
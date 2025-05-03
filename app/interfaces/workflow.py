"""
Workflow interface for the service-based architecture.

This file defines the interface for workflows, which are sequences
of components that process data through a defined pipeline.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class Workflow(ABC):
    """
    Interface for workflow definitions.
    
    Workflows define a sequence of processing stages that execute
    components in a specific order to accomplish a task.
    """
    
    @abstractmethod
    def get_id(self) -> str:
        """
        Get the workflow identifier.
        
        Returns:
            str: Workflow identifier
        """
        pass
    
    @abstractmethod
    def get_stages(self) -> List[Dict[str, Any]]:
        """
        Get the workflow stages.
        
        Returns:
            List[Dict[str, Any]]: List of stage definitions
        """
        pass
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the workflow.
        
        Args:
            context: Initial context for the workflow
            
        Returns:
            Dict[str, Any]: Final workflow context after execution
        """
        pass
    
    @abstractmethod
    def execute_stage(self, stage_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific stage of the workflow.
        
        Args:
            stage_id: Identifier of the stage to execute
            context: Context for the stage execution
            
        Returns:
            Dict[str, Any]: Updated context after stage execution
        """
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get workflow metadata.
        
        Returns:
            Dict[str, Any]: Workflow metadata
        """
        return {
            "id": self.get_id(),
            "stage_count": len(self.get_stages())
        } 
"""
Base service implementation.
"""

import logging
from typing import Any, Dict, List, Optional

from app.interfaces.service import Service
from app.interfaces.workflow import Workflow
from app.workflows.base_workflow import BaseWorkflow
from app.core.exceptions import ServiceError, WorkflowError
from app.utils.logging_setup import TICK_ICON, CROSS_ICON


class BaseService(Service):
    """
    Base implementation of the Service interface.
    
    This class provides common functionality for all services and
    should be extended by concrete service implementations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base service.
        
        Args:
            config: Configuration parameters for the service
        """
        super().__init__(config)
        self.logger = logging.getLogger(f"services.{self.__class__.__name__.lower()}")
        self.logger.debug(f"{TICK_ICON} Creating {self.__class__.__name__} with config: {config}")
        
        # Dictionary of workflow instances, keyed by workflow ID
        self._workflows: Dict[str, Workflow] = {}
    
    def initialize(self) -> bool:
        """
        Initialize the service.
        
        This implementation sets the initialized flag to True but should
        be overridden by subclasses to perform actual initialization.
        
        Returns:
            bool: True if initialization was successful
        """
        self.logger.info(f"Initializing {self.__class__.__name__}")
        self.initialized = True
        self.logger.info(f"{TICK_ICON} {self.__class__.__name__} initialized")
        return True
    
    def shutdown(self) -> None:
        """
        Shutdown the service.
        
        This implementation logs the shutdown but should be overridden
        by subclasses to perform actual cleanup.
        """
        self.logger.info(f"Shutting down {self.__class__.__name__}")
        self.initialized = False
        self.logger.info(f"{TICK_ICON} {self.__class__.__name__} shutdown complete")
    
    def health_check(self) -> bool:
        """
        Check if the service is healthy.
        
        This implementation just checks the initialized flag but should
        be overridden by subclasses to perform actual health checks.
        
        Returns:
            bool: True if service is healthy, False otherwise
        """
        self.logger.debug(f"Health check for {self.__class__.__name__}: {self.initialized}")
        if self.initialized:
            self.logger.info(f"{TICK_ICON} {self.__class__.__name__} is healthy")
        else:
            self.logger.warning(f"{CROSS_ICON} {self.__class__.__name__} is not healthy")
        return self.initialized
    
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
        self.logger.debug(f"Getting config value for key '{key}' in service {self.__class__.__name__}: {value}")
        return value
    
    def validate_config(self) -> bool:
        """
        Validate the service configuration.
        
        This implementation always returns True but should be overridden
        by subclasses to perform actual validation.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        self.logger.debug(f"Validating config for service {self.__class__.__name__}")
        valid = True
        if valid:
            self.logger.info(f"{TICK_ICON} Config validated for service {self.__class__.__name__}")
        else:
            self.logger.warning(f"{CROSS_ICON} Config validation failed for service {self.__class__.__name__}")
        return valid
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get service status information.
        
        This implementation adds the service class name to the base status.
        
        Returns:
            Dict[str, Any]: Service status information
        """
        status = super().get_status()
        status.update({
            "service_name": self.__class__.__name__
        })
        return status
    
    def register_workflow(self, workflow: Workflow) -> None:
        """
        Register a workflow with the service.
        
        Args:
            workflow: Workflow instance
        """
        workflow_id = workflow.get_id()
        self._workflows[workflow_id] = workflow
        self.logger.debug(f"Registered workflow: {workflow_id}")
        self.logger.info(f"{TICK_ICON} Registered workflow: {workflow_id}")
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """
        Get a workflow by ID.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Optional[Workflow]: Workflow instance or None if not found
        """
        return self._workflows.get(workflow_id)
    
    def execute_workflow(self, workflow_id: str, input_data: Dict[str, Any],
                        start_stage: Optional[str] = None,
                        end_stage: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a workflow with the given input data.
        
        Args:
            workflow_id: Workflow identifier
            input_data: Input data for the workflow
            start_stage: Optional stage to start from
            end_stage: Optional stage to end at
            
        Returns:
            Dict[str, Any]: Workflow execution results
            
        Raises:
            ServiceError: If workflow execution fails
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            self.logger.error(f"{CROSS_ICON} Workflow not found: {workflow_id}")
            raise ServiceError(f"Workflow not found: {workflow_id}")
        
        try:
            # Prepare context with input data
            context = input_data.copy()
            
            # Add stage control if provided
            if start_stage:
                context['start_stage'] = start_stage
            if end_stage:
                context['end_stage'] = end_stage
            
            # Execute workflow
            result = workflow.execute(context)
            
            self.logger.info(f"{TICK_ICON} Executed workflow: {workflow_id}")
            return result
        except Exception as e:
            self.logger.error(f"{CROSS_ICON} Error executing workflow {workflow_id}: {str(e)}")
            raise ServiceError(f"Error executing workflow {workflow_id}: {str(e)}")
    
    def process_query(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Process a natural language query using the service.
        
        This is a default implementation that uses a default workflow
        if available. Subclasses should override this method to provide
        service-specific query processing.
        
        Args:
            query: Natural language query
            **kwargs: Additional parameters
            
        Returns:
            Dict[str, Any]: Query processing result
            
        Raises:
            ServiceError: If query processing fails
        """
        try:
            # Get default workflow ID from config or use "default"
            default_workflow_id = self.get_config_value("default_workflow", "default")
            
            # Check if default workflow exists
            if default_workflow_id not in self._workflows:
                raise ServiceError(f"Default workflow not found: {default_workflow_id}")
            
            # Create input context with query
            context = {
                "query": query,
                **kwargs
            }
            
            # Execute default workflow
            result = self.execute_workflow(default_workflow_id, context)
            
            self.logger.info(f"{TICK_ICON} Processed query using workflow: {default_workflow_id}")
            return result
        except Exception as e:
            self.logger.error(f"{CROSS_ICON} Error processing query: {str(e)}")
            raise ServiceError(f"Error processing query: {str(e)}")
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get service metadata including capabilities and version.
        
        Returns:
            Dict[str, Any]: Service metadata
        """
        return {
            "service_name": self.__class__.__name__,
            "initialized": self.initialized,
            "workflows": list(self._workflows.keys()),
            "version": "1.0.0"
        } 
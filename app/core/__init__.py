"""
Core framework module for the application.

This module provides the core functionality for the application, including:
- Configuration management
- Component registry
- Workflow engine
- Service management
"""

from app.core.config_loader import ConfigLoader
from app.core.component_registry import ComponentRegistry
from app.core.workflow_engine import WorkflowEngine
from app.core.service_manager import ServiceManager
from app.core.exceptions import (
    CoreException,
    ConfigurationError,
    ComponentRegistryError,
    WorkflowError,
    ServiceError,
    InitializationError
)

# Re-export from app module to avoid circular imports
from app.application import Application
import os
import logging
from typing import Optional, Dict, Any, List, Union

from app.factory import ApplicationFactory

# Configure logging
ApplicationFactory.configure_logging(
    log_level=os.environ.get("LOG_LEVEL", "INFO"),
    log_file=os.environ.get("LOG_FILE")
)

# Load configuration directory from environment
config_dir = os.environ.get("CONFIG_DIR", "config")

# Initialize the application using factory with all verification steps
run_health_checks = os.environ.get("SKIP_HEALTH_CHECKS", "false").lower() != "true"
app_instance = None

try:
    app_instance = ApplicationFactory.create_app(
        config_dir=config_dir,
        verify_config=True,
        verify_components=True,
        verify_services=True,
        run_health_checks=run_health_checks
    )
except Exception as e:
    logger = logging.getLogger("app.core")
    logger.error(f"Failed to initialize app instance: {str(e)}")

# Provide a function to get the app instance for cases where
# a new instance might be needed
def get_app() -> Application:
    """
    Get the initialized application instance.
    
    Returns:
        Application: Application instance
    """
    if app_instance is None:
        # Try again with health checks disabled
        return ApplicationFactory.create_app(
            config_dir=config_dir,
            verify_config=True,
            verify_components=True, 
            verify_services=True,
            run_health_checks=False
        )
    return app_instance

def process_query(query: str, context: Optional[Dict[str, Any]] = None, 
                 stages_to_execute: Optional[Union[List[str], str]] = None) -> Dict[str, Any]:
    """
    Process a natural language query.
    
    Args:
        query: Natural language query to process
        context: Additional context for query processing
        stages_to_execute: List of stage IDs to execute, or a single stage ID,
                          or None to execute all stages in the workflow
        
    Returns:
        Dict[str, Any]: Query processing result
    """
    logger = logging.getLogger("app.core")
    logger.info(f"Processing query: {query}")
    
    # Get app instance - if initial one failed, try with health checks disabled
    app = get_app()
    
    # Call the application's process_query method with the stages to execute
    return app.process_query(query, context, stages_to_execute)

def get_available_workflows() -> List[str]:
    """
    Get a list of all available workflow IDs.
    
    Returns:
        List[str]: List of workflow IDs
    """
    app = get_app()
    return ApplicationFactory.get_available_workflows(app)

def get_available_components() -> Dict[str, List[str]]:
    """
    Get all available components in the application.
    
    Returns:
        Dict[str, List[str]]: Dictionary mapping component types to lists of component IDs
    """
    app = get_app()
    return ApplicationFactory.get_available_components(app)

def get_workflow_stages(workflow_id: str) -> List[Dict[str, Any]]:
    """
    Get the stages of a workflow.
    
    Args:
        workflow_id: Workflow identifier
        
    Returns:
        List[Dict[str, Any]]: List of stage definitions
    """
    app = get_app()
    workflow = app.workflow_engine.get_workflow(workflow_id)
    if not workflow:
        return []
    
    return workflow.get('workflow', {}).get('stages', [])

__all__ = [
    'ConfigLoader',
    'ComponentRegistry',
    'WorkflowEngine',
    'ServiceManager',
    'CoreException',
    'ConfigurationError',
    'ComponentRegistryError',
    'WorkflowError',
    'ServiceError',
    'InitializationError',
    'get_app',
    'process_query',
    'get_available_workflows',
    'get_workflow_stages',
    'app_instance'
] 
"""
Core application module.

This module provides the main entry point for the application.
It initializes the application and provides a function to get the
application instance.
"""

import os
import logging
from typing import Optional, Dict, Any, List, Union

from app.factory import ApplicationFactory
from app.application import Application

# Configure logging
ApplicationFactory.configure_logging(
    log_level=os.environ.get("LOG_LEVEL", "INFO"),
    log_file=os.environ.get("LOG_FILE")
)

# Load configuration directory from environment
config_dir = os.environ.get("CONFIG_DIR", "config")

# Initialize the application using factory with all verification steps
app_instance = ApplicationFactory.create_app(
    config_dir=config_dir,
    verify_config=True,
    verify_components=True,
    verify_services=True,
    run_health_checks=True
)

# Provide a function to get the app instance for cases where
# a new instance might be needed
def get_app() -> Application:
    """
    Get the initialized application instance.
    
    Returns:
        Application: Application instance
    """
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
    
    # Call the application's process_query method with the stages to execute
    return app_instance.process_query(query, context, stages_to_execute)

def get_available_workflows() -> List[str]:
    """
    Get a list of all available workflow IDs.
    
    Returns:
        List[str]: List of workflow IDs
    """
    return ApplicationFactory.get_available_workflows(app_instance)

def get_available_components() -> Dict[str, List[str]]:
    """
    Get all available components in the application.
    
    Returns:
        Dict[str, List[str]]: Dictionary mapping component types to lists of component IDs
    """
    return ApplicationFactory.get_available_components(app_instance)

def get_workflow_stages(workflow_id: str) -> List[Dict[str, Any]]:
    """
    Get the stages of a workflow.
    
    Args:
        workflow_id: Workflow identifier
        
    Returns:
        List[Dict[str, Any]]: List of stage definitions
    """
    workflow = app_instance.workflow_engine.get_workflow(workflow_id)
    if not workflow:
        return []
    
    return workflow.get('workflow', {}).get('stages', []) 
"""
Factory for creating the main application and its components.
"""

import logging
import os
from typing import Dict, Any, Optional, List

from app.application import Application
from app.core.exceptions import InitializationError


class ApplicationFactory:
    """
    Factory for creating the main application and its components.
    
    This class provides static methods for creating and configuring
    the application and its components.
    """
    
    @staticmethod
    def create_app(config_dir: Optional[str] = None, 
                  verify_config: bool = True, 
                  verify_components: bool = True, 
                  verify_services: bool = True, 
                  run_health_checks: bool = True) -> Application:
        """
        Create the main application with all of its components.
        
        Args:
            config_dir: Directory containing configuration files
            verify_config: Whether to verify configuration is loaded properly
            verify_components: Whether to verify components exist
            verify_services: Whether to verify service requirements
            run_health_checks: Whether to run health checks on services
            
        Returns:
            Application: The initialized application
            
        Raises:
            InitializationError: If application initialization fails
        """
        logger = logging.getLogger("app.factory")
        
        # Use environment variable for config dir if not provided
        if not config_dir:
            config_dir = os.environ.get("CONFIG_DIR", "config")
            
        logger.info(f"Creating application with config directory: {config_dir}")
        
        try:
            # Convert legacy parameters to init_options dict
            init_options = {
                "verify_config": verify_config,
                "verify_components": verify_components,
                "verify_services": verify_services,
                "run_health_checks": run_health_checks
            }
            
            # Create and return the application with specified options
            app = Application(
                config_dir=config_dir,
                init_options=init_options
            )
            
            logger.info("Application created successfully")
            return app
            
        except Exception as e:
            logger.error(f"Failed to create application: {str(e)}")
            raise InitializationError(f"Failed to create application: {str(e)}")
    
    @staticmethod
    def configure_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
        """
        Configure application logging.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Path to log file or None for console logging
        """
        logger = logging.getLogger("app")
        
        # Configure log level
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        logger.setLevel(numeric_level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Configure console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Configure file handler if log file is provided
        if log_file:
            # Create log directory if it doesn't exist
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    @staticmethod
    def get_available_components(app: Application) -> Dict[str, List[str]]:
        """
        Get all available components in the application.
        
        Args:
            app: Application instance
            
        Returns:
            Dict[str, List[str]]: Dictionary mapping component types to lists of component IDs
        """
        return {
            component_type: app.component_registry.get_components_by_type(component_type)
            for component_type in app.component_registry.get_component_types()
        }
    
    @staticmethod
    def get_available_workflows(app: Application) -> List[str]:
        """
        Get all available workflow IDs.
        
        Args:
            app: Application instance
            
        Returns:
            List[str]: List of available workflow IDs
        """
        return app.workflow_engine.list_workflows() 
"""
Copyright (c) 2024 dev1ender

This file is part of conversDB.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.

Main application class for conversDB.
"""

import logging
import os
import sys
from typing import Any, Dict, List, Optional, Union

from app.core.config_loader import ConfigLoader
from app.core.component_registry import ComponentRegistry
from app.core.workflow_engine import WorkflowEngine
from app.core.service_manager import ServiceManager
from app.core.exceptions import CoreException, InitializationError
from app.utils.logging_setup import setup_logging_from_config
from app.llm.factory import LLMFactory  # Import at the top for clarity

# Setup logger
logger = logging.getLogger("app.application")

class Application:
    """
    Main application class for the NLP Query Engine.
    
    This class is responsible for:
    1. Initializing the application components
    2. Managing the application lifecycle
    3. Processing natural language queries
    4. Providing access to application services
    """
    
    def __init__(self, config_dir: Optional[str] = None, init_options: Optional[Dict[str, Any]] = None):
        """
        Initialize the application following a structured configuration-driven approach.
        
        Args:
            config_dir: Directory containing configuration files
            init_options: Options controlling initialization behavior (overrides config)
        """
        # Import icons here to avoid circular import issues
        from app.utils.logging_setup import TICK_ICON, CROSS_ICON
        logger.debug(f"{TICK_ICON} Entering Application.__init__")
        self.TICK_ICON = TICK_ICON
        self.CROSS_ICON = CROSS_ICON
        
        # Initialize state
        self.initialized = False
        self.config_dir = config_dir or os.environ.get("CONFIG_DIR", "config")
        self.init_options = init_options or {}
        
        # Step 1: Load main configuration
        self._load_config()
        
        # Step 2: Verify basic configuration 
        self._verify_config()
        
        # Step 3: Initialize core services
        self._initialize_core_services()
        
        # Step 4: Register components
        self._register_components()
        
        # Step 5: Initialize and verify embeddings
        self._initialize_embeddings()
        
        # Step 6: Verify embedding creation
        if self._get_init_option("verify_embedding_creation", True):
            self._verify_embedding_creation()
        
        # Step 7: Verify components
        if self._get_init_option("verify_components", True):
            self._verify_components()
        
        # Step 8: Verify workflows
        if self._get_init_option("verify_workflows", True):
            self._verify_workflows()
        
        # Step 9: Verify workflow requirements
        if self._get_init_option("verify_workflow_requirements", True):
            self._verify_workflow_requirements()
        
        # Step 10: Register services
        self._register_services()
        
        # Step 11: Initialize services
        self._initialize_services()
        
        # Step 12: Run health checks
        if self._get_init_option("run_health_checks", True):
            self._run_health_checks()
        
        # Mark initialization as complete
        self.initialized = True
        logger.info(f"{self.TICK_ICON} Application initialization complete")
    
    def _get_init_option(self, option_name: str, default_value: Any) -> Any:
        """
        Get initialization option from either init_options or config.
        
        Args:
            option_name: Name of the option
            default_value: Default value if not found
            
        Returns:
            Any: Option value
        """
        # First check init_options
        if option_name in self.init_options:
            return self.init_options[option_name]
        
        # Then check config
        if hasattr(self, 'config_loader'):
            return self.config_loader.get_value(f"init_options.{option_name}", default_value)
        
        # Otherwise return default
        return default_value
    
    def _load_config(self) -> None:
        """
        Load the application configuration.
        
        Step 1: Load the main application configuration
        
        Raises:
            InitializationError: If configuration loading fails
        """
        logger.info("Step 1: Loading configuration")
        try:
            # Initialize the config loader
            self.config_loader = ConfigLoader(self.config_dir)
            
            # Setup logging from config 
            logging_config = self.config_loader.get_config().get("logging", {})
            setup_logging_from_config(logging_config)
            logger.info(f"{self.TICK_ICON} Logging configured from YAML")
            
            logger.info(f"{self.TICK_ICON} Configuration loaded from {self.config_dir}")
        except Exception as e:
            logger.error(f"{self.CROSS_ICON} Failed to load configuration: {str(e)}")
            raise InitializationError(f"Failed to load configuration: {str(e)}")
    
    def _verify_config(self) -> None:
        """
        Verify that configuration is loaded properly and contains required sections.
        
        Step 2: Verify configuration
        
        Raises:
            InitializationError: If configuration verification fails
        """
        logger.info("Step 2: Verifying configuration")
        try:
            config = self.config_loader.get_config()
            if not config:
                logger.error(f"{self.CROSS_ICON} Main configuration is empty")
                raise InitializationError("Main configuration is empty")
            
            # Check for required config sections from configuration
            required_sections = self.config_loader.get_value("required_sections", ["enabled_services", "default_workflow"])
            
            missing_sections = [section for section in required_sections if section not in config]
            
            if missing_sections:
                logger.error(f"{self.CROSS_ICON} Missing required configuration sections: {', '.join(missing_sections)}")
                raise InitializationError(f"Missing required configuration sections: {', '.join(missing_sections)}")
            
            logger.info(f"{self.TICK_ICON} Configuration verified successfully")
        
        except Exception as e:
            logger.error(f"{self.CROSS_ICON} Configuration verification failed: {str(e)}")
            raise InitializationError(f"Configuration verification failed: {str(e)}")
    
    def _initialize_core_services(self) -> None:
        """
        Initialize core application services.
        
        Step 3: Initialize core services
        
        Raises:
            InitializationError: If core service initialization fails
        """
        logger.info("Step 3: Initializing core services")
        try:
            # Initialize service manager
            self.service_manager = ServiceManager()
            logger.info(f"{self.TICK_ICON} Service Manager initialized")
        except Exception as e:
            logger.error(f"{self.CROSS_ICON} Failed to initialize core services: {str(e)}")
            raise InitializationError(f"Failed to initialize core services: {str(e)}")
    
    def _register_components(self) -> None:
        """
        Register application components.
        
        Step 4: Register components
        
        Raises:
            InitializationError: If component registration fails
        """
        logger.info("Step 4: Registering components")
        try:
            # Initialize component registry
            self.component_registry = ComponentRegistry(self.config_dir)
            
            # Log registered component types
            component_types = self.component_registry.get_component_types()
            component_count = sum(len(self.component_registry.get_components_by_type(t)) for t in component_types)
            logger.info(f"{self.TICK_ICON} Registered {component_count} components across {len(component_types)} types")
        except Exception as e:
            logger.error(f"{self.CROSS_ICON} Failed to register components: {str(e)}")
            raise InitializationError(f"Failed to register components: {str(e)}")
    
    def _initialize_embeddings(self) -> None:
        """
        Initialize and verify embeddings.
        
        Step 5: Initialize embeddings
        
        Raises:
            InitializationError: If embedding initialization fails
        """
        logger.info("Step 5: Initializing embeddings")
        
        if not self._get_init_option("verify_embeddings", True):
            logger.info("Embedding verification disabled, skipping...")
            return
            
        try:
            # Get embedding component types to verify from config
            embedding_components = self.config_loader.get_value(
                "embeddings.components_to_verify", ["document_embedder", "query_embedder"]
            )
            
            if not embedding_components:
                logger.warning("No embedding components configured for verification")
                return
                
            # Verify each specified component
            for component_id in embedding_components:
                # Check if this component exists in registry
                if component_id not in self.component_registry.get_components_by_type("embedding"):
                    logger.warning(f"Embedding component '{component_id}' not found in registry, skipping verification")
                    continue
                
                # Get component config
                component_config = self.component_registry.get_component_config("embedding", component_id)
                if not component_config:
                    logger.warning(f"No configuration found for embedding component '{component_id}', skipping verification")
                    continue
                
                embedding_config = component_config.get("default_config", {})
                logger.debug(f"Verifying embedding component '{component_id}' with config: {embedding_config}")
                
                # Verify embeddings using LLMFactory
                embeddings_ok = LLMFactory.verify_embeddings(embedding_config)
                if not embeddings_ok:
                    error_msg = f"Embedding verification failed for component '{component_id}'"
                    # Check if this component is required
                    if component_id in self.config_loader.get_value("embeddings.required_components", ["document_embedder"]):
                        logger.error(f"{self.CROSS_ICON} {error_msg}")
                        raise InitializationError(error_msg)
                    else:
                        logger.warning(f"{self.CROSS_ICON} {error_msg} (optional component)")
                else:
                    logger.info(f"{self.TICK_ICON} Embedding verification passed for component '{component_id}'")
        
        except Exception as e:
            logger.error(f"{self.CROSS_ICON} Error during embedding initialization: {str(e)}")
            # Check if embeddings are optional according to config
            if self._get_init_option("embeddings_required", True):
                raise InitializationError(f"Error during embedding initialization: {str(e)}")
            else:
                logger.warning("Continuing despite embedding initialization failure (embeddings_required=False)")
    
    def _verify_embedding_creation(self) -> None:
        """
        Verify that embeddings can be created.
        
        Step 6: Verify embedding creation 
        
        Raises:
            InitializationError: If embedding creation verification fails
        """
        logger.info("Step 6: Verifying embedding creation")
        try:
            # Get the default embedding config to test
            component_id = self._get_init_option("test_embedder_component", "document_embedder")
            
            # Get component config
            component_config = self.component_registry.get_component_config("embedding", component_id)
            if not component_config:
                logger.warning(f"No configuration found for embedding test component '{component_id}', skipping verification")
                return
                
            embedding_config = component_config.get("default_config", {})
            
            # Test embedding creation with the factory
            result = LLMFactory.create_and_verify_test_embedding(embedding_config)
            
            if not result["success"]:
                error_msg = f"Failed to create embeddings: {result.get('error', 'Unknown error')}"
                if self._get_init_option("embedding_creation_required", True):
                    logger.error(f"{self.CROSS_ICON} {error_msg}")
                    raise InitializationError(error_msg)
                else:
                    logger.warning(f"{self.CROSS_ICON} {error_msg} (optional)")
                    return
            
            logger.info(f"{self.TICK_ICON} Successfully created and verified embeddings with {result.get('dimensions', 0)} dimensions")
            
        except Exception as e:
            logger.error(f"{self.CROSS_ICON} Error verifying embedding creation: {str(e)}")
            if self._get_init_option("embedding_creation_required", True):
                raise InitializationError(f"Error verifying embedding creation: {str(e)}")
            else:
                logger.warning(f"Continuing despite embedding creation failure (embedding_creation_required=False)")
    
    def _verify_components(self) -> None:
        """
        Verify that required components exist in the registry.
        
        Step 7: Verify components
        
        Raises:
            InitializationError: If component verification fails
        """
        logger.info("Step 7: Verifying components")
        try:
            # Get required component types from config
            required_components = self.config_loader.get_value(
                "components.required_types", ["embedding", "query_executors", "schema_generators"]
            )
            
            # Check each required component type
            for component_type in required_components:
                components = self.component_registry.get_components_by_type(component_type)
                if not components:
                    error_msg = f"No components found for required type: {component_type}"
                    logger.error(f"{self.CROSS_ICON} {error_msg}")
                    raise InitializationError(error_msg)
                    
                logger.debug(f"Found {len(components)} components of type '{component_type}': {', '.join(components)}")
            
            # Check specific required components
            required_specific = self.config_loader.get_value("components.required_specific", {})
            for component_type, required_ids in required_specific.items():
                available = self.component_registry.get_components_by_type(component_type)
                missing = [cid for cid in required_ids if cid not in available]
                if missing:
                    error_msg = f"Missing required components of type '{component_type}': {', '.join(missing)}"
                    logger.error(f"{self.CROSS_ICON} {error_msg}")
                    raise InitializationError(error_msg)
            
            # Initialize the workflow engine
            workflows_dir = os.path.join(self.config_dir, "workflows")
            self.workflow_engine = WorkflowEngine(
                self.component_registry,
                workflows_dir
            )
            
            logger.info(f"{self.TICK_ICON} Component verification successful")
        
        except Exception as e:
            logger.error(f"{self.CROSS_ICON} Component verification failed: {str(e)}")
            raise InitializationError(f"Component verification failed: {str(e)}")
    
    def _verify_workflows(self) -> None:
        """
        Verify workflows are properly defined.
        
        Step 8: Verify workflows
        
        Raises:
            InitializationError: If workflow verification fails
        """
        logger.info("Step 8: Verifying workflows")
        try:
            # List available workflows
            workflows = self.workflow_engine.list_workflows()
            if not workflows:
                error_msg = "No workflows found"
                logger.error(f"{self.CROSS_ICON} {error_msg}")
                raise InitializationError(error_msg)
            
            # Verify default workflow exists
            default_workflow = self.config_loader.get_value("default_workflow", "default_workflow")
            if default_workflow not in workflows:
                error_msg = f"Default workflow '{default_workflow}' not found"
                logger.error(f"{self.CROSS_ICON} {error_msg}")
                raise InitializationError(error_msg)
            
            # Log available workflows
            logger.info(f"{self.TICK_ICON} Found {len(workflows)} workflows: {', '.join(workflows)}")
            
        except Exception as e:
            logger.error(f"{self.CROSS_ICON} Workflow verification failed: {str(e)}")
            raise InitializationError(f"Workflow verification failed: {str(e)}")
    
    def _verify_workflow_requirements(self) -> None:
        """
        Verify workflow configuration requirements.
        
        Step 9: Verify workflow requirements
        
        Raises:
            InitializationError: If workflow requirement verification fails
        """
        logger.info("Step 9: Verifying workflow requirements")
        try:
            # Get default workflow for verification
            default_workflow = self.config_loader.get_value("default_workflow", "default_workflow")
            
            # Get workflow definition
            workflow_def = self.workflow_engine.get_workflow(default_workflow)
            if not workflow_def:
                error_msg = f"Could not load definition for default workflow '{default_workflow}'"
                logger.error(f"{self.CROSS_ICON} {error_msg}")
                raise InitializationError(error_msg)
            
            # Check stages
            stages = workflow_def.get("workflow", {}).get("stages", [])
            if not stages:
                error_msg = f"No stages defined in default workflow '{default_workflow}'"
                logger.error(f"{self.CROSS_ICON} {error_msg}")
                raise InitializationError(error_msg)
            
            # Verify each stage references valid components
            for idx, stage in enumerate(stages):
                stage_id = stage.get("id", f"stage_{idx}")
                component_type = stage.get("component_type")
                component_id = stage.get("component_id")
                
                if not component_type or not component_id:
                    error_msg = f"Stage '{stage_id}' has missing component_type or component_id"
                    logger.error(f"{self.CROSS_ICON} {error_msg}")
                    raise InitializationError(error_msg)
                
                # Check component exists
                available_components = self.component_registry.get_components_by_type(component_type)
                if component_id not in available_components:
                    error_msg = f"Stage '{stage_id}' references non-existent component '{component_type}/{component_id}'"
                    logger.error(f"{self.CROSS_ICON} {error_msg}")
                    raise InitializationError(error_msg)
            
            logger.info(f"{self.TICK_ICON} Workflow requirements verified successfully for default workflow '{default_workflow}'")
            
        except Exception as e:
            logger.error(f"{self.CROSS_ICON} Workflow requirement verification failed: {str(e)}")
            raise InitializationError(f"Workflow requirement verification failed: {str(e)}")
    
    def _register_services(self) -> None:
        """
        Register application services.
        
        Step 10: Register services
        
        Raises:
            InitializationError: If service registration fails
        """
        logger.info("Step 10: Registering services")
        try:
            # Get enabled services from configuration
            enabled_services = self.config_loader.get_enabled_services()
            
            if not enabled_services:
                logger.warning(f"{self.CROSS_ICON} No services enabled in configuration")
                return
            
            # Register service classes and configurations
            for service_name in enabled_services:
                service_config = self.config_loader.get_service_config(service_name)
                
                if not service_config:
                    logger.warning(f"{self.CROSS_ICON} Configuration not found for service: {service_name}")
                    continue
                
                # Get service class path from configuration
                class_path = service_config.get("class")
                if not class_path:
                    error_msg = f"Class path not specified for service: {service_name}"
                    logger.error(f"{self.CROSS_ICON} {error_msg}")
                    raise InitializationError(error_msg)
                
                # Register service
                self.service_manager.register_service_class(service_name, class_path)
                self.service_manager.register_service_config(service_name, service_config)
                logger.debug(f"Registered service {service_name} with class {class_path}")
            
            logger.info(f"{self.TICK_ICON} Registered {len(enabled_services)} services")
            
        except Exception as e:
            logger.error(f"{self.CROSS_ICON} Failed to register services: {str(e)}")
            raise InitializationError(f"Failed to register services: {str(e)}")
    
    def _initialize_services(self) -> None:
        """
        Initialize all registered services.
        
        Step 11: Initialize services
        
        Raises:
            InitializationError: If service initialization fails
        """
        logger.info("Step 11: Initializing services")
        try:
            # Initialize all registered services
            self.service_manager.initialize_services()
            
            # Check required services
            required_services = self.config_loader.get_value("services.required", [])
            for service_name in required_services:
                if not self.service_manager.get_service(service_name):
                    error_msg = f"Required service '{service_name}' failed to initialize"
                    logger.error(f"{self.CROSS_ICON} {error_msg}")
                    raise InitializationError(error_msg)
            
            # Get count of running services
            running_services = self.service_manager.get_service_names()
            logger.info(f"{self.TICK_ICON} Initialized {len(running_services)} services")
            
        except Exception as e:
            logger.error(f"{self.CROSS_ICON} Failed to initialize services: {str(e)}")
            raise InitializationError(f"Failed to initialize services: {str(e)}")
    
    def _run_health_checks(self) -> None:
        """
        Run health checks on all services.
        
        Step 12: Run health checks
        
        Raises:
            InitializationError: If any required service health check fails
        """
        logger.info("Step 12: Running service health checks")
        try:
            service_names = self.service_manager.get_service_names()
            unhealthy_services = []
            
            for service_name in service_names:
                if not self.service_manager.check_service_health(service_name):
                    logger.warning(f"{self.CROSS_ICON} Service unhealthy: {service_name}")
                    unhealthy_services.append(service_name)
            
            # Check if any required services are unhealthy
            required_services = self.config_loader.get_value("services.required", [])
            unhealthy_required = [s for s in unhealthy_services if s in required_services]
            
            if unhealthy_required:
                error_msg = f"Health check failed for required services: {', '.join(unhealthy_required)}"
                logger.error(f"{self.CROSS_ICON} {error_msg}")
                raise InitializationError(error_msg)
            elif unhealthy_services:
                # Log warning but don't fail for non-required services
                logger.warning(f"Health check failed for optional services: {', '.join(unhealthy_services)}")
            
            logger.info(f"{self.TICK_ICON} Health checks passed for all required services")
            
        except Exception as e:
            logger.error(f"{self.CROSS_ICON} Health check failed: {str(e)}")
            raise InitializationError(f"Health check failed: {str(e)}")
    
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None, 
                      stages_to_execute: Optional[Union[List[str], str]] = None) -> Dict[str, Any]:
        """
        Process a natural language query.
        
        Step 13: Process query
        
        Args:
            query: Natural language query to process
            context: Additional context for query processing
            stages_to_execute: List of stage IDs to execute, or a single stage ID,
                              or None to execute all stages in the workflow
            
        Returns:
            Dict[str, Any]: Query processing result
        """
        if not self.initialized:
            raise InitializationError("Application not fully initialized, cannot process query")
            
        logger.debug(f"Processing query: {query}")
        
        # Create initial workflow context
        workflow_context = context or {}
        workflow_context["query"] = query
        
        # Handle stages selection if provided
        if stages_to_execute:
            if isinstance(stages_to_execute, str):
                stages_to_execute = [stages_to_execute]
            workflow_context["selected_stages"] = stages_to_execute
        
        # Execute default workflow
        default_workflow = self.config_loader.get_value("default_workflow", "default_workflow")
        result = self.workflow_engine.execute_workflow(default_workflow, workflow_context)
        
        logger.info(f"{self.TICK_ICON} Query processing complete")
        return result
    
    def get_service(self, service_name: str) -> Any:
        """
        Get a service instance by name.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Any: Service instance or None if not found
        """
        logger.debug(f"Getting service: {service_name}")
        return self.service_manager.get_service(service_name)
    
    def shutdown(self) -> None:
        """
        Shutdown the application.
        
        Step 14: Shutdown
        
        This method should be called when the application is shutting down
        to ensure proper cleanup of resources.
        """
        logger.info("Step 14: Shutting down application")
        
        # Shutdown services
        try:
            self.service_manager.stop_all_services()
            logger.info(f"{self.TICK_ICON} All services stopped")
        except Exception as e:
            logger.error(f"{self.CROSS_ICON} Error stopping services: {str(e)}")
        
        # Cleanup any other resources
        try:
            # Clear component registry cache
            if hasattr(self, 'component_registry'):
                self.component_registry.clear_instance_cache()
                logger.debug("Component registry cache cleared")
        except Exception as e:
            logger.error(f"{self.CROSS_ICON} Error cleaning up resources: {str(e)}")
        
        # Mark as not initialized
        self.initialized = False
        logger.info(f"{self.TICK_ICON} Application shutdown complete") 
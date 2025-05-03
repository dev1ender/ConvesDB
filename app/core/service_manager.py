"""
Service management utilities.
"""

import logging
from typing import Any, Dict, List, Optional
import importlib

from app.core.exceptions import ServiceError
from app.utils.logging_setup import TICK_ICON, CROSS_ICON


class ServiceManager:
    """
    Manager for application services.
    
    This class is responsible for:
    1. Managing service lifecycles
    2. Providing access to services
    3. Handling service dependencies
    4. Monitoring service health
    """
    
    def __init__(self):
        """Initialize the service manager."""
        self.logger = logging.getLogger("core.service_manager")
        self.logger.debug(f"{TICK_ICON} ServiceManager initialized.")
        
        # Dictionary of service instances, keyed by service name
        self._services: Dict[str, Any] = {}
        
        # Dictionary of service configurations, keyed by service name
        self._service_configs: Dict[str, Dict[str, Any]] = {}
        
        # Dictionary of service class paths, keyed by service name
        self._service_classes: Dict[str, str] = {}
    
    def register_service_class(self, service_name: str, class_path: str) -> None:
        """
        Register a service class.
        
        Args:
            service_name: Name of the service
            class_path: Fully qualified path to the service class
        """
        self.logger.debug(f"Registering service class: {service_name} -> {class_path}")
        self._service_classes[service_name] = class_path
        self.logger.info(f"{TICK_ICON} Registered service class: {service_name}")
    
    def register_service_config(self, service_name: str, config: Dict[str, Any]) -> None:
        """
        Register a service configuration.
        
        Args:
            service_name: Name of the service
            config: Service configuration
        """
        self.logger.debug(f"Registering service config: {service_name}")
        self._service_configs[service_name] = config
        self.logger.info(f"{TICK_ICON} Registered service config: {service_name}")
    
    def register_service_instance(self, service_name: str, service_instance: Any) -> None:
        """
        Register a pre-initialized service instance.
        
        Args:
            service_name: Name of the service
            service_instance: Service instance
        """
        self.logger.debug(f"Registering service instance: {service_name}")
        self._services[service_name] = service_instance
        self.logger.info(f"{TICK_ICON} Registered service instance: {service_name}")
    
    def get_service(self, service_name: str) -> Optional[Any]:
        """
        Get a service instance.
        
        If the service is already instantiated, returns the existing instance.
        Otherwise, instantiates the service and caches it.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Any: Service instance or None if not found
            
        Raises:
            ServiceError: If service instantiation fails
        """
        self.logger.debug(f"Getting service: {service_name}")
        # Check if service is already instantiated
        if service_name in self._services:
            self.logger.debug(f"{TICK_ICON} Service {service_name} already instantiated.")
            return self._services[service_name]
        
        # Check if service class is registered
        if service_name not in self._service_classes:
            self.logger.warning(f"{CROSS_ICON} Service class not found: {service_name}")
            return None
        
        # Get service configuration
        config = self._service_configs.get(service_name, {})
        
        # Instantiate service
        try:
            class_path = self._service_classes[service_name]
            module_path, class_name = class_path.rsplit('.', 1)
            
            module = importlib.import_module(module_path)
            service_class = getattr(module, class_name)
            
            service = service_class(config)
            
            # Cache service instance
            self._services[service_name] = service
            
            self.logger.info(f"{TICK_ICON} Instantiated service: {service_name}")
            return service
        
        except Exception as e:
            self.logger.error(f"{CROSS_ICON} Failed to instantiate service {service_name}: {str(e)}")
            raise ServiceError(f"Failed to instantiate service {service_name}: {str(e)}")
    
    def initialize_services(self, service_names: Optional[List[str]] = None) -> None:
        """
        Initialize multiple services.
        
        Args:
            service_names: List of service names to initialize or None for all
            
        Raises:
            ServiceError: If service initialization fails
        """
        self.logger.debug(f"Initializing services: {service_names if service_names else 'all registered'}")
        services_to_init = service_names or list(self._service_classes.keys())
        
        for service_name in services_to_init:
            try:
                self.logger.debug(f"Initializing service: {service_name}")
                service = self.get_service(service_name)
                
                # Call the initialize method on the service
                if hasattr(service, 'initialize') and callable(getattr(service, 'initialize')):
                    success = service.initialize()
                    if success:
                        self.logger.info(f"{TICK_ICON} Initialized service: {service_name}")
                    else:
                        error_msg = f"Service {service_name} initialize() method returned False"
                        self.logger.error(f"{CROSS_ICON} {error_msg}")
                        raise ServiceError(error_msg)
                else:
                    self.logger.warning(f"{CROSS_ICON} Service {service_name} has no initialize() method")
                
            except Exception as e:
                self.logger.error(f"{CROSS_ICON} Failed to initialize service {service_name}: {str(e)}")
                raise ServiceError(f"Failed to initialize service {service_name}: {str(e)}")
    
    def stop_service(self, service_name: str) -> None:
        """
        Stop a service.
        
        Args:
            service_name: Name of the service
            
        Raises:
            ServiceError: If service shutdown fails
        """
        if service_name not in self._services:
            return
        
        service = self._services[service_name]
        
        try:
            # Call shutdown method if it exists
            if hasattr(service, 'shutdown') and callable(getattr(service, 'shutdown')):
                service.shutdown()
            
            # Remove from services dictionary
            del self._services[service_name]
            
            self.logger.info(f"Stopped service: {service_name}")
        
        except Exception as e:
            raise ServiceError(f"Failed to stop service {service_name}: {str(e)}")
    
    def stop_all_services(self) -> None:
        """
        Stop all running services.
        
        Raises:
            ServiceError: If service shutdown fails
        """
        service_names = list(self._services.keys())
        
        for service_name in service_names:
            try:
                self.stop_service(service_name)
            except Exception as e:
                self.logger.error(f"Error stopping service {service_name}: {str(e)}")
    
    def check_service_health(self, service_name: str) -> bool:
        """
        Check if a service is healthy.
        
        Args:
            service_name: Name of the service
            
        Returns:
            bool: True if service is healthy, False otherwise
        """
        if service_name not in self._services:
            return False
        
        service = self._services[service_name]
        
        try:
            # Call health_check method if it exists
            if hasattr(service, 'health_check') and callable(getattr(service, 'health_check')):
                return service.health_check()
            
            # If no health_check method, assume service is healthy
            return True
        
        except Exception as e:
            self.logger.warning(f"Health check failed for service {service_name}: {str(e)}")
            return False
    
    def check_all_services_health(self) -> Dict[str, bool]:
        """
        Check health of all services.
        
        Returns:
            Dict[str, bool]: Dictionary mapping service names to health status
        """
        health_status = {}
        
        for service_name in self._services.keys():
            health_status[service_name] = self.check_service_health(service_name)
        
        return health_status
    
    def list_services(self) -> List[str]:
        """
        Get list of all registered service names.
        
        Returns:
            List[str]: List of service names
        """
        return list(self._service_classes.keys())
    
    def list_running_services(self) -> List[str]:
        """
        Get list of running service names.
        
        Returns:
            List[str]: List of running service names
        """
        return list(self._services.keys())
    
    def get_service_names(self) -> List[str]:
        """
        Get a list of all registered service names.
        
        Returns:
            List[str]: List of service names
        """
        return list(self._services.keys()) 
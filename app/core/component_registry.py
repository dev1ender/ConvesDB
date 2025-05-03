"""
Component registry for service-based architecture.

This class is responsible for registering, discovering, and 
instantiating components based on their type and ID.
"""

import importlib
import logging
from typing import Any, Dict, List, Optional, Type, Union
from pathlib import Path
import yaml
import os

from app.interfaces.component import Component
from app.core.exceptions import ComponentRegistryError
from app.utils.logging_setup import TICK_ICON, CROSS_ICON

class ComponentRegistry:
    """
    Registry for managing and accessing components.
    
    This class is responsible for:
    1. Loading component configurations
    2. Instantiating components on demand
    3. Caching component instances for reuse
    4. Providing access to component metadata
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the component registry.
        
        Args:
            config_dir: Directory containing component configurations
        """
        self.logger = logging.getLogger("core.component_registry")
        self.config_dir = config_dir
        self.logger.debug(f"{TICK_ICON} ComponentRegistry initialized with config_dir={config_dir}")
        
        # Component class registry - maps component types and IDs to their classes
        self._component_classes: Dict[str, Dict[str, str]] = {}
        
        # Component instance cache - maps component types and IDs to instances
        self._component_instances: Dict[str, Dict[str, Any]] = {}
        
        # Component configurations - maps component types and IDs to configs
        self._component_configs: Dict[str, Dict[str, Dict[str, Any]]] = {}
        
        # Load component registry from configuration if provided
        if config_dir:
            self._load_component_registry()
    
    def _load_component_registry(self) -> None:
        """
        Load component registry from configuration files.
        
        Searches for component configuration files in the config directory
        and builds the component class registry.
        
        Raises:
            ComponentRegistryError: If loading fails
        """
        self.logger.debug("Loading component registry from configuration files.")
        try:
            config_path = Path(self.config_dir)
            if not config_path.exists():
                raise ComponentRegistryError(f"Configuration directory not found: {self.config_dir}")
            
            # Load main registry configuration
            main_config_path = config_path / "main.yaml"
            if main_config_path.exists():
                with open(main_config_path, 'r') as file:
                    main_config = yaml.safe_load(file)
                    registry_config = main_config.get('component_registry', {})
                    
                    # Build class registry from main config
                    for component_type, components in registry_config.items():
                        if component_type not in self._component_classes:
                            self._component_classes[component_type] = {}
                        
                        for component_id, class_path in components.items():
                            self._component_classes[component_type][component_id] = class_path
            
            # Load component-specific configurations
            components_dir = config_path / "components"
            if components_dir.exists() and components_dir.is_dir():
                for component_type_dir in components_dir.iterdir():
                    if component_type_dir.is_dir():
                        component_type = component_type_dir.name
                        
                        if component_type not in self._component_configs:
                            self._component_configs[component_type] = {}
                        
                        for config_file in component_type_dir.glob("*.yaml"):
                            with open(config_file, 'r') as file:
                                component_config = yaml.safe_load(file)
                                
                                if 'component' in component_config and 'id' in component_config['component']:
                                    component_id = component_config['component']['id']
                                    self._component_configs[component_type][component_id] = component_config
                                    
                                    # Add to class registry if class is specified
                                    if 'class' in component_config['component']:
                                        if component_type not in self._component_classes:
                                            self._component_classes[component_type] = {}
                                        
                                        self._component_classes[component_type][component_id] = component_config['component']['class']
            
            self.logger.info(f"{TICK_ICON} Loaded component registry with {sum(len(components) for components in self._component_classes.values())} component classes")
        
        except Exception as e:
            self.logger.error(f"{CROSS_ICON} Failed to load component registry: {str(e)}")
            raise ComponentRegistryError(f"Failed to load component registry: {str(e)}")
    
    def register_component_class(self, component_type: str, component_id: str, class_path: str) -> None:
        """
        Register a component class.
        
        Args:
            component_type: Type of the component
            component_id: ID of the component
            class_path: Fully qualified path to the component class
        """
        self.logger.debug(f"Registering component class: {component_type}/{component_id} -> {class_path}")
        if component_type not in self._component_classes:
            self._component_classes[component_type] = {}
        
        self._component_classes[component_type][component_id] = class_path
        self.logger.info(f"{TICK_ICON} Registered component class: {component_type}/{component_id}")
    
    def register_component_config(self, component_type: str, component_id: str, config: Dict[str, Any]) -> None:
        """
        Register a component configuration.
        
        Args:
            component_type: Type of the component
            component_id: ID of the component
            config: Component configuration
        """
        self.logger.debug(f"Registering component config: {component_type}/{component_id}")
        if component_type not in self._component_configs:
            self._component_configs[component_type] = {}
        
        self._component_configs[component_type][component_id] = config
        self.logger.info(f"{TICK_ICON} Registered component config: {component_type}/{component_id}")
    
    def get_component(self, component_type: str, component_id: str) -> Optional[Any]:
        """
        Get a component instance.
        
        If the component is already instantiated, returns the cached instance.
        Otherwise, instantiates the component and caches it.
        
        Args:
            component_type: Type of the component
            component_id: ID of the component
            
        Returns:
            Any: Component instance or None if not found
            
        Raises:
            ComponentRegistryError: If component instantiation fails
        """
        self.logger.debug(f"Getting component: {component_type}/{component_id}")
        # Check if component is already instantiated
        if (component_type in self._component_instances and 
            component_id in self._component_instances[component_type]):
            self.logger.debug(f"{TICK_ICON} Component {component_type}/{component_id} already instantiated.")
            return self._component_instances[component_type][component_id]
        
        # Check if component class is registered
        if (component_type not in self._component_classes or 
            component_id not in self._component_classes[component_type]):
            self.logger.warning(f"{CROSS_ICON} Component class not found: {component_type}/{component_id}")
            return None
        
        # Get component configuration
        config = {}
        if (component_type in self._component_configs and 
            component_id in self._component_configs[component_type]):
            config = self._component_configs[component_type][component_id].get('default_config', {})
        
        # Instantiate component
        try:
            class_path = self._component_classes[component_type][component_id]
            module_path, class_name = class_path.rsplit('.', 1)
            
            module = importlib.import_module(module_path)
            component_class = getattr(module, class_name)
            
            component = component_class(component_id, config)
            
            # Cache component instance
            if component_type not in self._component_instances:
                self._component_instances[component_type] = {}
            
            self._component_instances[component_type][component_id] = component
            
            self.logger.debug(f"Instantiating component: {component_type}/{component_id}")
            self.logger.info(f"{TICK_ICON} Instantiated component: {component_type}/{component_id}")
            return component
        
        except Exception as e:
            self.logger.error(f"{CROSS_ICON} Failed to instantiate component {component_type}/{component_id}: {str(e)}")
            raise ComponentRegistryError(f"Failed to instantiate component {component_type}/{component_id}: {str(e)}")
    
    def get_component_config(self, component_type: str, component_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a component configuration.
        
        Args:
            component_type: Type of the component
            component_id: ID of the component
            
        Returns:
            Dict[str, Any]: Component configuration or None if not found
        """
        if (component_type in self._component_configs and 
            component_id in self._component_configs[component_type]):
            return self._component_configs[component_type][component_id]
        return None
    
    def get_all_component_ids(self, component_type: str) -> List[str]:
        """
        Get all component IDs of a specific type.
        
        Args:
            component_type: Type of the component
            
        Returns:
            List[str]: List of component IDs
        """
        if component_type in self._component_classes:
            return list(self._component_classes[component_type].keys())
        return []
    
    def clear_instance_cache(self) -> None:
        """
        Clear the component instance cache.
        """
        self.logger.debug("Clearing component instance cache.")
        self._component_instances = {}
        self.logger.info(f"{TICK_ICON} Component instance cache cleared")
    
    def clear_all(self) -> None:
        """
        Clear all component registries and caches.
        """
        self.logger.debug("Clearing all component registries and caches.")
        self._component_classes = {}
        self._component_instances = {}
        self._component_configs = {}
        self.logger.info(f"{TICK_ICON} Component registry cleared")
    
    def list_component_types(self) -> List[str]:
        """Get list of all registered component types.
        
        Returns:
            List[str]: List of component type names
        """
        return list(self._component_classes.keys())
    
    def list_components(self, component_type: str) -> List[str]:
        """Get list of all components of a specific type.
        
        Args:
            component_type: Type category of components
            
        Returns:
            List[str]: List of component IDs
        """
        if component_type not in self._component_classes:
            return []
        return list(self._component_classes[component_type].keys())
    
    def get_component_types(self) -> List[str]:
        """
        Get a list of all component types in the registry.
        
        Returns:
            List[str]: List of component types
        """
        return list(self._component_classes.keys())
    
    def get_components_by_type(self, component_type: str) -> List[str]:
        """
        Get a list of component IDs for a specific component type.
        
        Args:
            component_type: Component type
            
        Returns:
            List[str]: List of component IDs
        """
        if component_type in self._component_classes:
            return list(self._component_classes[component_type].keys())
        return [] 
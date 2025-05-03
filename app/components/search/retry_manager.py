"""
Search retry manager component.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from app.components.base_component import BaseComponent
from app.core.exceptions import ComponentRegistryError


class RetryManager(BaseComponent):
    """
    Search retry management component.
    
    This component manages search operations with retry logic when
    initial searches don't produce good results.
    """
    
    def __init__(self, component_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the retry manager.
        
        Args:
            component_id: Unique identifier for the component
            config: Configuration parameters for the component
        """
        super().__init__(component_id, config)
        
        # Configuration options with defaults
        self.max_retries = self.get_config_value("max_retries", 3)
        self.min_results = self.get_config_value("min_results", 1)
        self.backoff_factor = self.get_config_value("backoff_factor", 1.5)
        self.initial_wait = self.get_config_value("initial_wait_seconds", 0.1)
        self.fallback_strategy = self.get_config_value("fallback_strategy", "threshold_reduction")
        self.threshold_reduction_factor = self.get_config_value("threshold_reduction_factor", 0.8)
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the component to manage search retries.
        
        Args:
            context: Execution context containing search results
            
        Returns:
            Dict[str, Any]: Updated context with final search results
            
        Raises:
            ComponentRegistryError: If retry management fails
        """
        self.logger.debug("Managing search retries")
        
        # Get search results from context
        search_results = context.get("search_results", [])
        search_component_id = context.get("vector_search")
        
        # Check if we have enough results
        if len(search_results) >= self.min_results:
            self.logger.debug(f"Initial search returned {len(search_results)} results, no retry needed")
            return context  # No changes needed
        
        # Get the search component
        if not search_component_id:
            error_msg = "No search component ID found in context"
            self.logger.error(error_msg)
            return {"error": error_msg, "retries": 0}
        
        try:
            # Get component from registry
            search_component = context.get("component_registry").get_component("search", search_component_id)
            
            if not search_component:
                error_msg = f"Search component not found: {search_component_id}"
                self.logger.error(error_msg)
                return {"error": error_msg, "retries": 0}
            
            # Retry search with adjusted parameters
            retry_count = 0
            current_context = context.copy()
            
            while len(search_results) < self.min_results and retry_count < self.max_retries:
                retry_count += 1
                self.logger.debug(f"Retry attempt {retry_count}/{self.max_retries}")
                
                # Apply fallback strategy
                if self.fallback_strategy == "threshold_reduction":
                    # Reduce score threshold
                    current_threshold = search_component.score_threshold
                    new_threshold = current_threshold * self.threshold_reduction_factor
                    search_component.score_threshold = new_threshold
                    self.logger.debug(f"Reduced score threshold from {current_threshold} to {new_threshold}")
                
                elif self.fallback_strategy == "expand_top_k":
                    # Increase top_k
                    current_top_k = search_component.top_k
                    new_top_k = int(current_top_k * 2)
                    search_component.top_k = new_top_k
                    self.logger.debug(f"Increased top_k from {current_top_k} to {new_top_k}")
                
                # Wait with exponential backoff
                wait_time = self.initial_wait * (self.backoff_factor ** (retry_count - 1))
                time.sleep(wait_time)
                
                # Execute search again
                search_result = search_component.execute(current_context)
                current_context.update(search_result)
                
                # Update search results
                search_results = current_context.get("search_results", [])
                
                if len(search_results) >= self.min_results:
                    self.logger.debug(f"Retry successful, found {len(search_results)} results")
                    break
            
            # Return final context with retry info
            current_context["retries"] = retry_count
            current_context["retry_manager"] = self.component_id
            
            return current_context
        
        except Exception as e:
            error_msg = f"Error managing search retries: {str(e)}"
            self.logger.error(error_msg)
            raise ComponentRegistryError(error_msg)
    
    def validate_config(self) -> bool:
        """
        Validate the component configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        # Validate max_retries
        max_retries = self.get_config_value("max_retries", 3)
        if not isinstance(max_retries, int) or max_retries < 0:
            self.logger.warning("max_retries must be a non-negative integer")
            return False
        
        # Validate min_results
        min_results = self.get_config_value("min_results", 1)
        if not isinstance(min_results, int) or min_results <= 0:
            self.logger.warning("min_results must be a positive integer")
            return False
        
        # Validate backoff_factor
        backoff = self.get_config_value("backoff_factor", 1.5)
        if not isinstance(backoff, (int, float)) or backoff <= 0:
            self.logger.warning("backoff_factor must be a positive number")
            return False
        
        # Validate fallback_strategy
        strategy = self.get_config_value("fallback_strategy", "threshold_reduction")
        if strategy not in ["threshold_reduction", "expand_top_k"]:
            self.logger.warning("fallback_strategy must be one of: threshold_reduction, expand_top_k")
            return False
        
        # Validate threshold_reduction_factor
        threshold_factor = self.get_config_value("threshold_reduction_factor", 0.8)
        if not isinstance(threshold_factor, (int, float)) or threshold_factor <= 0 or threshold_factor >= 1:
            self.logger.warning("threshold_reduction_factor must be a number between 0 and 1")
            return False
        
        return True 
"""
JSON response formatter component.
"""

import logging
import json
from typing import Any, Dict, List, Optional

from app.components.base_component import BaseComponent
from app.core.exceptions import ComponentRegistryError


class JSONFormatter(BaseComponent):
    """
    JSON response formatter component.
    
    This component formats query results and other data into JSON format
    for consistent response structure.
    """
    
    def __init__(self, component_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the JSON formatter.
        
        Args:
            component_id: Unique identifier for the component
            config: Configuration parameters for the component
        """
        super().__init__(component_id, config)
        
        # Configuration options with defaults
        self.include_metadata = self.get_config_value("include_metadata", True)
        self.pretty_print = self.get_config_value("pretty_print", False)
        self.include_debug = self.get_config_value("include_debug", False)
        self.max_result_items = self.get_config_value("max_result_items", 100)
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the component to format response.
        
        Args:
            context: Execution context containing query results
            
        Returns:
            Dict[str, Any]: Updated context with formatted response
            
        Raises:
            ComponentRegistryError: If formatting fails
        """
        self.logger.debug("Formatting response as JSON")
        
        try:
            # Get results from context
            results = context.get("results", [])
            query = context.get("query", "")
            sql_query = context.get("sql_query", "")
            error = context.get("error")
            
            # Initialize response structure
            response = {
                "success": error is None,
                "query": query,
                "results": results
            }
            
            # Add SQL query if available
            if sql_query:
                response["sql_query"] = sql_query
            
            # Add error if present
            if error:
                response["error"] = error
            
            # Add metadata if enabled
            if self.include_metadata:
                metadata = self._extract_metadata(context)
                if metadata:
                    response["metadata"] = metadata
            
            # Add debug info if enabled
            if self.include_debug:
                debug_info = self._extract_debug_info(context)
                if debug_info:
                    response["debug"] = debug_info
            
            # Format as JSON string if pretty print is enabled
            if self.pretty_print:
                json_string = json.dumps(response, indent=2, default=str)
                return {
                    "formatted_response": json_string,
                    "response": response,
                    "response_formatter": self.component_id
                }
            
            # Return response object
            return {
                "formatted_response": response,
                "response_formatter": self.component_id
            }
        
        except Exception as e:
            error_msg = f"Error formatting response: {str(e)}"
            self.logger.error(error_msg)
            raise ComponentRegistryError(error_msg)
    
    def _extract_metadata(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from context.
        
        Args:
            context: Execution context
            
        Returns:
            Dict[str, Any]: Metadata
        """
        metadata = {}
        
        # Include execution time if available
        if "execution_time" in context:
            metadata["execution_time"] = context["execution_time"]
        
        # Include database info if available
        if "database_type" in context:
            metadata["database_type"] = context["database_type"]
        
        # Include service info if available
        if "service" in context:
            metadata["service"] = context["service"]
        
        # Include result count if available
        if "results" in context:
            results = context["results"]
            if isinstance(results, list):
                metadata["result_count"] = len(results)
                metadata["has_more"] = context.get("has_more", False)
            
        # Include components used if available
        components_used = []
        for key in context:
            if key.endswith("_generator") or key.endswith("_executor") or key.endswith("_formatter"):
                components_used.append(context[key])
        
        if components_used:
            metadata["components_used"] = components_used
        
        return metadata
    
    def _extract_debug_info(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract debug information from context.
        
        Args:
            context: Execution context
            
        Returns:
            Dict[str, Any]: Debug information
        """
        debug_info = {}
        
        # Include prompt if available
        if "prompt" in context:
            debug_info["prompt"] = context["prompt"]
        
        # Include schema if available
        if "schema" in context:
            # Simplify schema to avoid large debug output
            schema = context["schema"]
            if isinstance(schema, dict) and "tables" in schema:
                table_names = list(schema["tables"].keys())
                debug_info["schema_tables"] = table_names
        
        # Include document search info if available
        if "search_results" in context:
            search_results = context["search_results"]
            if isinstance(search_results, list):
                debug_info["search_result_count"] = len(search_results)
        
        # Include raw LLM response if available
        if "llm_response" in context:
            debug_info["llm_response"] = context["llm_response"]
        
        # Include workflow info if available
        if "workflow" in context:
            workflow = context["workflow"]
            if isinstance(workflow, dict):
                debug_info["workflow_id"] = workflow.get("id")
        
        # Include stage history if available
        if "stage_history" in context:
            debug_info["stage_history"] = context["stage_history"]
        
        return debug_info
    
    def validate_config(self) -> bool:
        """
        Validate the component configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        # Validate max_result_items
        max_result_items = self.get_config_value("max_result_items", 100)
        if not isinstance(max_result_items, int) or max_result_items <= 0:
            self.logger.warning("max_result_items must be a positive integer")
            return False
        
        return True 
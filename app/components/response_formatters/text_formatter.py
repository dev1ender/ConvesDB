"""
Text response formatter component.
"""

import logging
from typing import Any, Dict, List, Optional
import textwrap

from app.components.base_component import BaseComponent
from app.core.exceptions import ComponentRegistryError


class TextFormatter(BaseComponent):
    """
    Response formatter component that outputs plain text.
    
    This component formats query results and other data as human-readable text.
    """
    
    def __init__(self, component_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the text formatter.
        
        Args:
            component_id: Unique identifier for the component
            config: Configuration parameters for the component
        """
        super().__init__(component_id, config)
        
        # Configuration options with defaults
        self.include_headers = self.get_config_value("include_headers", True)
        self.max_column_width = self.get_config_value("max_column_width", 30)
        self.include_query = self.get_config_value("include_query", True)
        self.table_style = self.get_config_value("table_style", "ascii")
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the component to format the response as text.
        
        Args:
            context: Execution context containing the data to format
            
        Returns:
            Dict[str, Any]: Updated context with the formatted response
            
        Raises:
            ComponentRegistryError: If formatting fails
        """
        self.logger.debug("Formatting response as text")
        
        try:
            # Get results from context
            results = context.get("results", [])
            
            # Check for errors
            error = context.get("error")
            if error:
                return {
                    "formatted_response": f"Error: {error}",
                    "response_type": "text/plain",
                    "response_formatter": self.component_id
                }
            
            # Format header
            formatted_text = ""
            
            # Include original query if available and enabled
            if self.include_query and "query" in context:
                formatted_text += f"Query: {context['query']}\n\n"
            
            if self.include_query and "sql_query" in context:
                formatted_text += f"SQL: {context['sql_query']}\n\n"
            
            # Format results
            if isinstance(results, list) and results:
                # List of dictionaries - format as a table
                if isinstance(results[0], dict):
                    formatted_text += self._format_table(results)
                else:
                    # List of scalar values
                    formatted_text += self._format_list(results)
            elif isinstance(results, dict):
                # Single dictionary - format as key-value pairs
                formatted_text += self._format_dict(results)
            else:
                # Other result types
                formatted_text += f"Result: {results}"
            
            self.logger.debug(f"Formatted response with {len(formatted_text)} characters")
            
            # Return formatted response in context
            return {
                "formatted_response": formatted_text,
                "response_type": "text/plain",
                "response_formatter": self.component_id
            }
        
        except Exception as e:
            error_msg = f"Error formatting text response: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                "formatted_response": f"Error: {error_msg}",
                "response_type": "text/plain",
                "response_formatter": self.component_id,
                "error": error_msg
            }
    
    def _format_table(self, results: List[Dict[str, Any]]) -> str:
        """
        Format a list of dictionaries as a text table.
        
        Args:
            results: List of dictionaries to format
            
        Returns:
            str: Formatted table
        """
        if not results:
            return "No results."
        
        # Get column names from first row
        columns = list(results[0].keys())
        
        # Determine column widths
        col_widths = {col: min(self.max_column_width, max(len(str(col)), max(len(str(row.get(col, ""))) for row in results))) for col in columns}
        
        # Create header line
        table = ""
        if self.include_headers:
            headers = [self._truncate_value(col, col_widths[col]) for col in columns]
            if self.table_style == "markdown":
                table += "| " + " | ".join(headers) + " |\n"
                table += "|-" + "-|-".join("-" * col_widths[col] for col in columns) + "-|\n"
            else:  # ascii style
                table += "| " + " | ".join(headers) + " |\n"
                table += "+" + "+".join("-" * (col_widths[col] + 2) for col in columns) + "+\n"
        
        # Add data rows
        for row in results:
            values = [self._truncate_value(str(row.get(col, "")), col_widths[col]) for col in columns]
            if self.table_style == "markdown":
                table += "| " + " | ".join(values) + " |\n"
            else:  # ascii style
                table += "| " + " | ".join(values) + " |\n"
        
        return table
    
    def _format_list(self, results: List[Any]) -> str:
        """
        Format a list of scalar values.
        
        Args:
            results: List of values to format
            
        Returns:
            str: Formatted list
        """
        if not results:
            return "No results."
        
        formatted = "Results:\n"
        for i, item in enumerate(results, 1):
            formatted += f"{i}. {item}\n"
        
        return formatted
    
    def _format_dict(self, results: Dict[str, Any]) -> str:
        """
        Format a dictionary as key-value pairs.
        
        Args:
            results: Dictionary to format
            
        Returns:
            str: Formatted dictionary
        """
        if not results:
            return "No results."
        
        formatted = "Results:\n"
        max_key_len = max(len(str(key)) for key in results.keys())
        
        for key, value in results.items():
            key_str = str(key).ljust(max_key_len)
            if isinstance(value, dict):
                formatted += f"{key_str}: <object with {len(value)} properties>\n"
            elif isinstance(value, list):
                formatted += f"{key_str}: <list with {len(value)} items>\n"
            else:
                formatted += f"{key_str}: {value}\n"
        
        return formatted
    
    def _truncate_value(self, value: str, max_width: int) -> str:
        """
        Truncate a value to fit within the maximum width.
        
        Args:
            value: Value to truncate
            max_width: Maximum width
            
        Returns:
            str: Truncated value
        """
        if len(value) <= max_width:
            return value.ljust(max_width)
        
        return value[:max_width-3] + "..." if max_width > 3 else value[:max_width]
    
    def validate_config(self) -> bool:
        """
        Validate the component configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        # Validate max_column_width
        max_width = self.get_config_value("max_column_width", 30)
        if not isinstance(max_width, int) or max_width <= 0:
            self.logger.warning("max_column_width must be a positive integer")
            return False
        
        # Validate table_style
        style = self.get_config_value("table_style", "ascii")
        if style not in ["ascii", "markdown"]:
            self.logger.warning("table_style must be 'ascii' or 'markdown'")
            return False
        
        return True 
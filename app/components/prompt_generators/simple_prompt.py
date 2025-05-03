"""
Simple prompt generator component.
"""

import logging
from typing import Any, Dict, Optional

from app.components.base_component import BaseComponent
from app.utils.logging_setup import TICK_ICON, CROSS_ICON


class SimplePromptGenerator(BaseComponent):
    """
    Simple prompt generator component.
    
    This component generates a prompt from a query and optional context
    using a simple template-based approach.
    """
    
    def __init__(self, component_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the simple prompt generator.
        
        Args:
            component_id: Unique identifier for the component
            config: Configuration parameters for the component
        """
        super().__init__(component_id, config)
        self.logger.debug(f"{TICK_ICON} Initializing SimplePromptGenerator with id {component_id}")
        
        # Get template from config or use default
        self.template = self.get_config_value("template", 
            "Given the query: {query}\n\n"
            "And the following context: {context}\n\n"
            "Generate a response that answers the query based on the provided context."
        )
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the component to generate a prompt.
        
        Args:
            context: Execution context containing query and optional context
            
        Returns:
            Dict[str, Any]: Updated context with the generated prompt
        """
        self.logger.debug(f"{TICK_ICON} Executing SimplePromptGenerator for context keys: {list(context.keys())}")
        
        # Get query from context
        query = context.get("query", "")
        if not query:
            self.logger.warning(f"{CROSS_ICON} No query found in context")
            return {"prompt": "No query provided", "error": "Missing query"}
        
        # Get additional context if available
        additional_context = context.get("additional_context", "No additional context provided.")
        
        # Format template
        prompt = self.template.format(
            query=query,
            context=additional_context
        )
        
        self.logger.info(f"{TICK_ICON} Generated prompt with {len(prompt)} characters")
        
        # Return prompt in context
        return {
            "prompt": prompt,
            "prompt_generator": self.component_id
        }
    
    def validate_config(self) -> bool:
        """
        Validate the component configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        self.logger.debug("Validating config for SimplePromptGenerator")
        valid = True
        if "template" in self.config:
            template = self.config["template"]
            if "{query}" not in template:
                self.logger.warning(f"{CROSS_ICON} Template does not contain {{query}} placeholder")
                valid = False
        if valid:
            self.logger.info(f"{TICK_ICON} Config validated for SimplePromptGenerator")
        else:
            self.logger.error(f"{CROSS_ICON} Config validation failed for SimplePromptGenerator")
        return valid 
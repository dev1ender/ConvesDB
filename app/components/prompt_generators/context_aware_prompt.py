"""
Context-aware prompt generator component.
"""

import logging
import json
from typing import Any, Dict, List, Optional

from app.components.base_component import BaseComponent
from app.utils.logging_setup import TICK_ICON, CROSS_ICON


class ContextAwarePromptGenerator(BaseComponent):
    """
    Context-aware prompt generator component.
    
    This component generates prompts that intelligently incorporate different
    types of context (database schema, search results, examples, etc.)
    and structures them for optimal LLM performance.
    """
    
    def __init__(self, component_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the context-aware prompt generator.
        
        Args:
            component_id: Unique identifier for the component
            config: Configuration parameters for the component
        """
        super().__init__(component_id, config)
        self.logger.debug(f"{TICK_ICON} Initializing ContextAwarePromptGenerator with id {component_id}")
        
        # Configuration options with defaults
        self.format_schema = self.get_config_value("format_schema", True)
        self.include_search_results = self.get_config_value("include_search_results", True)
        self.max_search_results = self.get_config_value("max_search_results", 3)
        self.include_examples = self.get_config_value("include_examples", True)
        self.examples = self.get_config_value("examples", [])
        self.max_examples = self.get_config_value("max_examples", 2)
        self.max_schema_tables = self.get_config_value("max_schema_tables", 10)
        self.max_context_length = self.get_config_value("max_context_length", 4000)
        
        # Get template from config or use default
        self.template = self.get_config_value("template", 
            "You are an AI assistant that answers questions based on the available context.\n\n"
            "### Query\n{query}\n\n"
            "{database_schema}"
            "{search_results}"
            "{examples}"
            "{additional_context}\n\n"
            "### Instructions\n"
            "Based on the query and provided context, generate a response that:\n"
            "1. Directly addresses the user's question\n"
            "2. Uses only information from the provided context\n"
            "3. Cites relevant sources if available\n"
            "4. Acknowledges limitations or uncertainties\n\n"
            "### Response"
        )
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the component to generate a context-aware prompt.
        
        Args:
            context: Execution context containing query and various context elements
            
        Returns:
            Dict[str, Any]: Updated context with the generated prompt
        """
        self.logger.debug(f"{TICK_ICON} Executing ContextAwarePromptGenerator for context keys: {list(context.keys())}")
        
        # Get query from context
        query = context.get("query", "")
        if not query:
            self.logger.warning(f"{CROSS_ICON} No query found in context")
            return {"prompt": "No query provided", "error": "Missing query"}
        
        # Format the database schema section
        database_schema = self._format_schema_section(context)
        
        # Format the search results section
        search_results = self._format_search_results_section(context)
        
        # Format the examples section
        examples = self._format_examples_section(context)
        
        # Get additional context if available
        additional_context = self._format_additional_context(context)
        
        # Format template
        prompt = self.template.format(
            query=query,
            database_schema=database_schema,
            search_results=search_results,
            examples=examples,
            additional_context=additional_context
        )
        
        # Truncate if necessary
        if len(prompt) > self.max_context_length:
            self.logger.warning(f"{CROSS_ICON} Prompt exceeded max length ({len(prompt)} > {self.max_context_length}). Truncating.")
            prompt = self._truncate_prompt(prompt)
        
        self.logger.info(f"{TICK_ICON} Generated prompt with {len(prompt)} characters")
        
        # Return prompt in context
        return {
            "prompt": prompt,
            "prompt_generator": self.component_id
        }
    
    def _format_schema_section(self, context: Dict[str, Any]) -> str:
        """
        Format the database schema section of the prompt.
        
        Args:
            context: Execution context containing schema information
            
        Returns:
            str: Formatted schema section
        """
        self.logger.debug("Formatting schema section for prompt")
        if not self.format_schema or "schema" not in context:
            return ""
        
        schema = context.get("schema", {})
        if not schema:
            return ""
        
        # Format schema details
        schema_str = "### Database Schema\n"
        
        # Handle tables
        tables = schema.get("tables", {})
        if tables:
            table_count = 0
            for table_name, table_info in tables.items():
                if table_count >= self.max_schema_tables:
                    schema_str += f"... and {len(tables) - table_count} more tables (omitted for brevity)\n"
                    break
                
                # Add table name and description
                schema_str += f"Table: {table_name}"
                if "description" in table_info and table_info["description"]:
                    schema_str += f" - {table_info['description']}"
                schema_str += "\n"
                
                # Add columns
                columns = table_info.get("columns", [])
                if columns:
                    for column in columns:
                        col_name = column.get("name", "")
                        col_type = column.get("type", "")
                        is_pk = " (PK)" if column.get("primary_key", False) else ""
                        is_fk = " (FK)" if "referenced_table" in column else ""
                        
                        schema_str += f"  - {col_name}: {col_type}{is_pk}{is_fk}"
                        
                        # Add foreign key reference if available
                        if "referenced_table" in column and "referenced_column" in column:
                            schema_str += f" -> {column['referenced_table']}.{column['referenced_column']}"
                        
                        schema_str += "\n"
                
                schema_str += "\n"
                table_count += 1
        
        # Handle graph database schema (Neo4j)
        node_labels = schema.get("node_labels", {})
        if node_labels:
            schema_str += "### Graph Database Schema\n"
            
            # Format node labels
            for label, info in node_labels.items():
                schema_str += f"Node Label: {label}\n"
                properties = info.get("properties", {})
                if properties:
                    schema_str += "  Properties:\n"
                    for prop_name, prop_info in properties.items():
                        prop_type = prop_info.get("type", "")
                        schema_str += f"    - {prop_name}: {prop_type}\n"
                schema_str += "\n"
            
            # Format relationship types
            rel_types = schema.get("relationship_types", {})
            if rel_types:
                schema_str += "Relationship Types:\n"
                for rel_type, info in rel_types.items():
                    schema_str += f"  - {rel_type}\n"
                    patterns = info.get("patterns", [])
                    if patterns and len(patterns) > 0:
                        example_pattern = patterns[0]
                        from_labels = example_pattern.get("from_labels", [])
                        to_labels = example_pattern.get("to_labels", [])
                        if from_labels and to_labels:
                            schema_str += f"    Example: ({','.join(from_labels)})-[:{rel_type}]->({','.join(to_labels)})\n"
                schema_str += "\n"
        
        return schema_str
    
    def _format_search_results_section(self, context: Dict[str, Any]) -> str:
        """
        Format the search results section of the prompt.
        
        Args:
            context: Execution context containing search results
            
        Returns:
            str: Formatted search results section
        """
        self.logger.debug("Formatting search results section for prompt")
        if not self.include_search_results or "search_results" not in context:
            return ""
        
        search_results = context.get("search_results", [])
        if not search_results:
            return ""
        
        results_str = "### Search Results\n"
        
        # Format each search result
        for i, result in enumerate(search_results[:self.max_search_results], 1):
            results_str += f"Result {i}:\n"
            
            # Get content
            content = result.get("content", "")
            if content:
                # Truncate long content
                if len(content) > 500:
                    content = content[:500] + "..."
                results_str += f"{content}\n\n"
            
            # Get metadata
            metadata = result.get("metadata", {})
            if metadata:
                source = metadata.get("source", "")
                if source:
                    results_str += f"Source: {source}\n"
                
                # Other metadata
                for key, value in metadata.items():
                    if key != "source" and value:
                        results_str += f"{key}: {value}\n"
            
            results_str += "\n"
        
        # Note if there are more results
        if len(search_results) > self.max_search_results:
            results_str += f"... and {len(search_results) - self.max_search_results} more results (omitted for brevity)\n\n"
        
        return results_str
    
    def _format_examples_section(self, context: Dict[str, Any]) -> str:
        """
        Format the examples section of the prompt.
        
        Args:
            context: Execution context containing examples
            
        Returns:
            str: Formatted examples section
        """
        self.logger.debug("Formatting examples section for prompt")
        if not self.include_examples:
            return ""
        
        # Use examples from context or config
        examples = context.get("examples", self.examples)
        if not examples:
            return ""
        
        examples_str = "### Examples\n"
        
        # Format each example
        for i, example in enumerate(examples[:self.max_examples], 1):
            examples_str += f"Example {i}:\n"
            
            # Example query
            query = example.get("query", "")
            if query:
                examples_str += f"Query: {query}\n"
            
            # Example response
            response = example.get("response", "")
            if response:
                examples_str += f"Response: {response}\n"
            
            examples_str += "\n"
        
        return examples_str
    
    def _format_additional_context(self, context: Dict[str, Any]) -> str:
        """
        Format additional context if available.
        
        Args:
            context: Execution context containing additional context
            
        Returns:
            str: Formatted additional context section
        """
        additional_context = context.get("additional_context", "")
        
        if additional_context:
            return f"### Additional Context\n{additional_context}\n\n"
        
        return ""
    
    def _truncate_prompt(self, prompt: str) -> str:
        """
        Truncate prompt to stay within the maximum context length.
        
        Args:
            prompt: Original prompt
            
        Returns:
            str: Truncated prompt
        """
        # Keep the beginning and end of the prompt
        # Cut content from the middle
        sections = prompt.split("###")
        
        if len(sections) < 3:
            # Simple truncation if not enough sections
            return prompt[:self.max_context_length]
        
        # Always keep the query section and instructions
        query_section = "###" + sections[1]
        instructions_section = "###" + sections[-1]
        
        # Calculate how much space we have for the middle sections
        available_space = self.max_context_length - len(query_section) - len(instructions_section) - 100
        
        # If not enough space, keep only the most important parts
        if available_space <= 0:
            return query_section + instructions_section
        
        # Add middle sections until we run out of space
        middle_content = ""
        for i in range(2, len(sections) - 1):
            section = "###" + sections[i]
            
            if len(middle_content) + len(section) <= available_space:
                middle_content += section
            else:
                # Try to add a truncated version if it's an important section
                section_title = section.split("\n")[0].strip()
                if "Schema" in section_title or "Search Results" in section_title:
                    truncated_section = section[:available_space - len(middle_content)]
                    middle_content += truncated_section + "\n[Content truncated due to length constraints]\n"
                break
        
        return query_section + middle_content + instructions_section
    
    def validate_config(self) -> bool:
        """
        Validate the component configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        # Check if template contains required placeholders
        if "template" in self.config:
            template = self.config["template"]
            if "{query}" not in template:
                self.logger.warning("Template does not contain {query} placeholder")
                return False
        
        # Validate max values
        max_search_results = self.get_config_value("max_search_results", 3)
        if not isinstance(max_search_results, int) or max_search_results <= 0:
            self.logger.warning("max_search_results must be a positive integer")
            return False
        
        max_examples = self.get_config_value("max_examples", 2)
        if not isinstance(max_examples, int) or max_examples <= 0:
            self.logger.warning("max_examples must be a positive integer")
            return False
        
        max_schema_tables = self.get_config_value("max_schema_tables", 10)
        if not isinstance(max_schema_tables, int) or max_schema_tables <= 0:
            self.logger.warning("max_schema_tables must be a positive integer")
            return False
        
        max_context_length = self.get_config_value("max_context_length", 4000)
        if not isinstance(max_context_length, int) or max_context_length <= 0:
            self.logger.warning("max_context_length must be a positive integer")
            return False
        
        return True 
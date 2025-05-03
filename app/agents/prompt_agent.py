"""
Prompt agent implementation for the RAG-POC application.
"""

from typing import Dict, List, Any, Optional, Tuple
import json
import textwrap
from app.interfaces.agents import PromptAgentInterface, SchemaAgentInterface
from app.logging_setup import get_logger

# Setup module logger
logger = get_logger(__name__)

class PromptAgent(PromptAgentInterface):
    """Creates and manages prompts for the LLM."""
    
    def __init__(self, schema_agent: SchemaAgentInterface):
        """Initialize the prompt agent.
        
        Args:
            schema_agent: Schema agent instance for accessing schema information
        """
        self.schema_agent = schema_agent
        logger.debug("PromptAgent initialized")
    
    def build_prompt(self, user_question: str, relevant_tables: List[str]) -> str:
        """Build a prompt for the LLM to generate SQL from a question.
        
        Args:
            user_question: Natural language question
            relevant_tables: List of table names relevant to the question
            
        Returns:
            Prompt for the LLM
        """
        logger.debug(f"Building prompt for question: '{user_question}'")
        logger.debug(f"Using relevant tables: {relevant_tables}")
        
        # Get schema information for the relevant tables
        schema_context = self._get_schema_context(relevant_tables)
        
        # Build the system instruction
        system_instruction = self._build_system_instruction(schema_context)
        
        # Build the full prompt
        prompt = f"{system_instruction}\n\nUser Question: {user_question}"
        
        logger.debug(f"Built prompt with {len(prompt)} characters")
        
        return prompt
    
    def build_error_correction_prompt(self, sql_query: str, error: str, schema_context: str) -> str:
        """Build a prompt for error correction.
        
        Args:
            sql_query: The SQL query with errors
            error: Error message or description
            schema_context: Schema context for relevant tables
            
        Returns:
            Error correction prompt for the LLM
        """
        logger.debug(f"Building error correction prompt for query: '{sql_query}'")
        
        # Get the system instruction with schema context
        system_instruction = self._build_system_instruction(schema_context)
        
        # Build the error correction prompt
        prompt = f"""{system_instruction}

            The SQL query:
            ```sql
            {sql_query}
            ```

            Has the following errors:
            {error}

            Please fix the query and provide the corrected version. Ensure it is valid SQL syntax and references only the tables and columns provided in the schema information.

        User Question: Please fix the SQL query above."""
        
        logger.debug(f"Built error correction prompt with {len(prompt)} characters")
        
        return prompt
    
    def _get_schema_context(self, table_names: List[str]) -> str:
        """Get schema context for the specified tables.
        
        Args:
            table_names: List of table names
            
        Returns:
            Schema context string
        """
        logger.debug(f"Getting schema context for tables: {table_names}")
        
        schema_context = []
        
        for table_name in table_names:
            # Get table schema
            table_schema = self.schema_agent.get_table_schema(table_name)
            
            if not table_schema:
                logger.warning(f"Table '{table_name}' not found in schema")
                continue
                
            # Format table schema for the prompt
            columns = table_schema.get("columns", [])
            schema_context.append(f"Table: {table_name}")
            schema_context.append("Columns:")
            
            for column in columns:
                column_name = column.get("name", "")
                column_type = column.get("type", "")
                
                # Add foreign key information if available
                fk_info = ""
                if "foreign_keys" in column:
                    for fk in column["foreign_keys"]:
                        fk_info = f" (Foreign key to {fk['table']}.{fk['column']})"
                
                # Add primary key information if available
                pk_info = " (Primary Key)" if column.get("pk", 0) == 1 else ""
                
                schema_context.append(f"  - {column_name} ({column_type}){pk_info}{fk_info}")
            
            schema_context.append("")  # Empty line between tables
            
        return "\n".join(schema_context)
    
    def _build_system_instruction(self, schema_context: str) -> str:
        """Build the system instruction part of the prompt.
        
        Args:
            schema_context: Schema context for relevant tables
            
        Returns:
            System instruction
        """
        # Wrap text to ensure it's not too long
        wrapped_schema_context = schema_context
        
        system_instruction = f"""You are a SQL expert that converts natural language questions into SQL queries.

SCHEMA INFORMATION:
{wrapped_schema_context}

INSTRUCTIONS:
1. Use only the tables and columns provided in the schema information.
2. Create a valid SQL query that answers the user's question.
3. Make sure to use proper JOIN conditions based on the foreign key relationships.
4. Use proper SQL syntax and formatting.
5. Return only the SQL query without any explanations or comments.
6. Use double quotes for table and column names if they contain spaces or special characters.
7. Always qualify column names with table names or aliases to avoid ambiguity (e.g., customers.name, c.name).
8. Use appropriate SQL functions and operators based on the question's intent.
9. Use proper case-insensitive string comparisons if needed (e.g., LOWER(name) = 'john').
10. Always assume you're writing for a SQLite database."""
        
        return system_instruction 
"""
Query generator implementation for the RAG-POC application.
"""

from typing import Dict, List, Any, Optional, Tuple
import re
import sqlparse
from app.interfaces.agents import QueryGeneratorInterface, SchemaAgentInterface, PromptAgentInterface
from app.interfaces.llm import LLMClient
from app.logging_setup import get_logger

# Setup module logger
logger = get_logger(__name__)

class QueryGenerator(QueryGeneratorInterface):
    """Agent that generates SQL queries from natural language questions."""
    
    def __init__(self, llm_client: LLMClient, schema_agent: SchemaAgentInterface, 
                prompt_agent: PromptAgentInterface, max_retries: int = 3,
                validation_enabled: bool = True, validation_mode: str = "full"):
        """Initialize the query generator.
        
        Args:
            llm_client: LLM client for generating SQL
            schema_agent: Schema agent instance for schema information
            prompt_agent: Prompt agent instance for building prompts
            max_retries: Maximum number of retries for query generation
            validation_enabled: Whether to enable SQL validation
            validation_mode: Validation mode - "full", "syntax_only", or "none"
        """
        self.llm_client = llm_client
        self.schema_agent = schema_agent
        self.prompt_agent = prompt_agent
        self.max_retries = max_retries
        self.validation_enabled = validation_enabled
        self.validation_mode = validation_mode
        logger.debug(f"QueryGenerator initialized with max_retries={self.max_retries}, "
                    f"validation_enabled={self.validation_enabled}, validation_mode={self.validation_mode}")
    
    def generate(self, user_question: str) -> str:
        """Generate a SQL query from a natural language question.
        
        Args:
            user_question: The natural language question to convert
            
        Returns:
            The generated SQL query
        """
        logger.info(f"Generating SQL query for question: '{user_question}'")
        
        # Identify the relevant tables for this question
        logger.debug("Identifying relevant tables")
        relevant_tables = self.schema_agent.get_relevant_tables(user_question)
        
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            # Build prompt for the LLM
            logger.debug("Building LLM prompt")
            prompt = self.prompt_agent.build_prompt(user_question, relevant_tables)
            
            # Send to LLM
            logger.info("Sending prompt to LLM for SQL generation")
            sql_query = self.llm_client.generate(prompt)
            logger.info(f"LLM generated SQL query: {sql_query}")
            
            # Validate the query
            if self.validation_enabled:
                logger.debug("Validating generated SQL query")
                is_valid, error = self.validate_sql(sql_query, retry_count)
                
                if is_valid:
                    # If query validation is successful, break the loop
                    logger.info("SQL validation successful")
                    break
                    
                # If we have reached max retries, break the loop and return the last query
                if retry_count >= self.max_retries:
                    logger.warning(f"Max retries ({self.max_retries}) reached, returning last generated query")
                    break
                    
                # Special handling for specific validation errors
                if error:
                    last_error = error
                    
                    # Missing table reference - add missing table to relevant tables
                    if "uses table alias" in error and "not included in any FROM or JOIN clause" in error:
                        # Extract the missing table alias from the error message
                        match = re.search(r"uses table alias '(\w+)'", error)
                        if match:
                            missing_alias = match.group(1)
                            logger.debug(f"Detected missing table alias: {missing_alias}")
                            
                            # Add hint to prompt for next retry
                            user_question = f"{user_question} (Please include table {missing_alias} in your query joins)"
            else:
                # If validation is disabled, break the loop
                logger.debug("Query validation is disabled, accepting the query as is")
                break
                
            # Increment retry counter
            retry_count += 1
            if retry_count <= self.max_retries:
                logger.debug(f"Retrying query generation (attempt {retry_count}/{self.max_retries})")
                
        # If validation failed on the last attempt, log a warning
        if last_error:
            logger.warning(f"Final query may have issues: {last_error}")
            
        return sql_query
    
    def validate_sql(self, query: str, retry_count: int = 0) -> Tuple[bool, Optional[str]]:
        """Validate a SQL query.
        
        Args:
            query: The SQL query to validate
            retry_count: Current retry attempt number
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        logger.debug(f"Validating SQL query (retry {retry_count}/{self.max_retries}): {query}")
        
        # Skip validation if disabled or in "none" mode
        if not self.validation_enabled or self.validation_mode == "none":
            logger.debug("Validation skipped (disabled or in 'none' mode)")
            return True, None
            
        # Basic syntax validation
        try:
            parsed = sqlparse.parse(query)
            if not parsed:
                error_msg = "Failed to parse SQL query"
                logger.warning(error_msg)
                return False, error_msg
                
            logger.debug("Basic SQL syntax check passed")
        except Exception as e:
            error_msg = f"SQL syntax error: {str(e)}"
            logger.warning(error_msg)
            return False, error_msg
            
        # If only syntax validation is requested, return success
        if self.validation_mode == "syntax_only":
            logger.debug("Syntax-only validation passed")
            return True, None
            
        # Full validation - check table and column references
        try:
            # Extract tables from the query
            tables_in_query = self._extract_tables_from_query(query)
            logger.debug(f"Tables referenced in query: {tables_in_query}")
            
            # Check if referenced tables exist
            for table in tables_in_query:
                if not self.schema_agent.get_table_schema(table):
                    error_msg = f"Table '{table}' does not exist in the database schema"
                    logger.warning(error_msg)
                    return False, error_msg
                    
            # Advanced validation could be added here
            # For example, checking column references against the schema
            
            logger.debug("Full validation passed")
            return True, None
            
        except Exception as e:
            error_msg = f"Error during SQL validation: {str(e)}"
            logger.warning(error_msg)
            return False, error_msg
    
    def _extract_tables_from_query(self, query: str) -> List[str]:
        """Extract table names from a SQL query.
        
        Args:
            query: The SQL query to analyze
            
        Returns:
            List of table names
        """
        logger.debug("Extracting table names from query")
        
        # This is a simplified implementation
        # In a production system, use a proper SQL parser
        
        # Convert to lowercase for case-insensitive matching
        query = query.lower()
        
        # Extract tables from FROM clause
        from_match = re.search(r'from\s+([a-z0-9_,\s]+)(?:\s+where|\s+group|\s+having|\s+order|\s+limit|\s*$)', query)
        tables = []
        
        if from_match:
            from_tables = from_match.group(1).split(',')
            for table in from_tables:
                # Extract table name or alias
                table = table.strip()
                
                # Handle "table AS alias" or "table alias" formats
                if ' as ' in table:
                    table = table.split(' as ')[0].strip()
                elif ' ' in table:
                    table = table.split(' ')[0].strip()
                    
                tables.append(table)
        
        # Extract tables from JOIN clauses
        join_matches = re.finditer(r'join\s+([a-z0-9_]+)', query)
        for match in join_matches:
            tables.append(match.group(1).strip())
            
        logger.debug(f"Extracted tables: {tables}")
        return tables 
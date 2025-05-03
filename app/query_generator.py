from typing import Dict, List, Any, Optional, Tuple
import sqlparse
import re
from app.prompt_agent import PromptAgent
from app.schema_agent import SchemaAgent
from app.logging_setup import get_logger

# Setup module logger
logger = get_logger(__name__)

class LLMClient:
    """Abstract base class for LLM clients."""
    
    def generate(self, prompt: str) -> str:
        """Generate a response from the LLM."""
        raise NotImplementedError("LLM client must implement generate method")


class QueryGenerator:
    """Agent responsible for generating and validating SQL queries."""
    
    def __init__(self, llm_client, schema_agent: SchemaAgent, prompt_agent, max_retries: int = 3, 
                 validation_enabled: bool = True, validation_mode: str = "full"):
        """Initialize the QueryGenerator.
        
        Args:
            llm_client: LLM client for generating SQL
            schema_agent: SchemaAgent instance for schema information
            prompt_agent: PromptAgent instance for building prompts
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
        """
        Generate a SQL query from a natural language question.
        
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
                
            # Increment retry counter
            retry_count += 1
            if retry_count <= self.max_retries:
                logger.debug(f"Retrying query generation (attempt {retry_count}/{self.max_retries})")
                
        # If validation failed on the last attempt, log a warning
        if last_error:
            logger.warning(f"Final query may have issues: {last_error}")
            
        return sql_query
    
    def validate_query(self, sql_query: str, relevant_tables: List[str], 
                      retry_count: int = 0) -> Tuple[str, List[str]]:
        """Validate the generated SQL query and fix if needed."""
        logger.debug(f"Validating SQL query (retry {retry_count}/{self.max_retries}): {sql_query}")
        errors = []
        
        # Basic syntax validation with sqlparse
        try:
            parsed = sqlparse.parse(sql_query)
            if not parsed:
                error_msg = "Failed to parse SQL query"
                logger.warning(error_msg)
                errors.append(error_msg)
                return self._handle_error_correction(sql_query, errors, relevant_tables, retry_count)
            logger.debug("Basic SQL syntax check passed")
        except Exception as e:
            error_msg = f"Syntax error: {str(e)}"
            logger.warning(error_msg)
            errors.append(error_msg)
            return self._handle_error_correction(sql_query, errors, relevant_tables, retry_count)
        
        # Check for table existence
        logger.debug("Checking referenced tables exist in schema")
        tables_in_query = self._extract_tables_from_query(sql_query)
        logger.debug(f"Tables referenced in query: {tables_in_query}")
        
        for table in tables_in_query:
            if not self.schema_agent.get_table_schema(table):
                error_msg = f"Table '{table}' does not exist in the database schema"
                logger.warning(error_msg)
                errors.append(error_msg)
        
        if errors:
            logger.warning(f"Query validation failed with {len(errors)} errors")
            return self._handle_error_correction(sql_query, errors, relevant_tables, retry_count)
        
        logger.info("Query validation successful")
        return sql_query, errors
    
    def _handle_error_correction(self, sql_query: str, errors: List[str], 
                               relevant_tables: List[str], retry_count: int) -> Tuple[str, List[str]]:
        """Handle error correction for invalid queries."""
        if retry_count >= self.max_retries:
            logger.warning(f"Maximum retry count ({self.max_retries}) reached, returning query with errors")
            return sql_query, errors
        
        logger.info(f"Attempting query correction (retry {retry_count+1}/{self.max_retries})")
        
        # Get schema context for relevant tables
        logger.debug("Building schema context for error correction")
        schema_context = ""
        for table_name in relevant_tables:
            table_schema = self.schema_agent.get_table_schema(table_name)
            if table_schema:
                schema_context += f"Table: {table_name}\n"
                schema_context += "Columns:\n"
                for column in table_schema.get("columns", []):
                    schema_context += f"- {column['name']} ({column['type']})\n"
                schema_context += "\n"
        
        # Build error correction prompt
        logger.debug("Building error correction prompt")
        error_prompt = self.prompt_agent.build_error_correction_prompt(
            sql_query, 
            "\n".join(errors),
            schema_context
        )
        
        # Generate corrected query
        logger.info("Sending error correction prompt to LLM")
        corrected_query = self.llm_client.generate(error_prompt)
        logger.info(f"LLM generated corrected query: {corrected_query}")
        
        # Validate the corrected query
        logger.debug("Validating corrected query")
        return self.validate_query(corrected_query, relevant_tables, retry_count + 1)
    
    def _extract_tables_from_query(self, sql_query: str) -> List[str]:
        """Extract table names from a SQL query (simplified version)."""
        logger.debug("Extracting table names from query")
        # This is a simplified implementation
        # In a production system, use a proper SQL parser
        
        sql_query = sql_query.lower()
        words = sql_query.split()
        tables = []
        
        # Look for patterns like "FROM table" or "JOIN table"
        for i, word in enumerate(words):
            if word in ["from", "join"] and i < len(words) - 1:
                table_name = words[i + 1].strip(",;()")
                if table_name:
                    tables.append(table_name)
        
        unique_tables = list(set(tables))
        logger.debug(f"Extracted table names: {unique_tables}")
        return unique_tables

    def _validate_query(self, query: str) -> Tuple[bool, Optional[str]]:
        """Validate the SQL query according to our validation rules."""
        # Basic syntax check to catch obvious errors
        try:
            sqlparse.parse(query)
            logger.debug("Basic SQL syntax check passed")
        except Exception as e:
            return False, f"SQL syntax error: {str(e)}"
        
        # Check if all referenced tables exist in the database
        logger.debug("Checking referenced tables exist in schema")
        tables = self._extract_tables_from_query(query)
        logger.debug(f"Extracted table names: {tables}")
        
        # Create a map of aliases to table names
        aliases = self._extract_table_aliases(tables)
        
        logger.debug(f"Table aliases: {aliases}")
        logger.debug(f"Tables referenced in query: {tables}")
        
        # Check if all tables exist
        for table in tables:
            # Strip off any alias if present
            base_table = table.split(" ")[0].strip()
            if not self.schema_agent.table_exists(base_table):
                return False, f"Table '{base_table}' does not exist in the database"
        
        # Check if referenced columns exist in their respective tables
        column_refs = self._extract_column_references(query)
        logger.debug(f"Column references: {column_refs}")
        
        # Check all column references against schema
        for table_alias, col_name in column_refs:
            # If this is a table alias, resolve it to the actual table name
            if table_alias in aliases:
                table_name = aliases[table_alias]
            elif table_alias in tables:
                table_name = table_alias
            else:
                # Handle special case for T1, T2 style aliases - these might be resolved differently
                found_alias = False
                for alias_key, alias_value in aliases.items():
                    if alias_key.lower() == table_alias.lower():
                        table_name = alias_value
                        found_alias = True
                        break
                    
                if not found_alias:
                    for table in tables:
                        if " as " in table.lower():
                            parts = table.lower().split(" as ")
                            if parts[1].strip() == table_alias.lower():
                                table_name = parts[0].strip()
                                found_alias = True
                                break
                        elif " " in table:
                            parts = table.lower().split()
                            if len(parts) > 1 and parts[1].strip() == table_alias.lower():
                                table_name = parts[0].strip()
                                found_alias = True
                                break
                
                if not found_alias:
                    return False, f"Column reference '{table_alias}.{col_name}' uses table alias '{table_alias}' which is not included in any FROM or JOIN clause"
            
            # At this point we have resolved table_name to an actual table
            schema = self.schema_agent.get_table_schema(table_name)
            if not schema:
                return False, f"Could not find schema for table '{table_name}'"
                
            # Check if the column exists in this table
            column_exists = False
            for column in schema["columns"]:
                if column["name"] == col_name:
                    column_exists = True
                    break
                    
            if not column_exists:
                return False, f"Column '{col_name}' does not exist in table '{table_name}'"
        
        # If we got here, all validations passed
        logger.info("Query validation successful")
        return True, None

    def validate_sql(self, query: str, retry_count: int = 0) -> Tuple[bool, Optional[str]]:
        """
        Validate the generated SQL query.
        
        Args:
            query: The SQL query to validate
            retry_count: Current retry attempt (for debugging)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        logger.debug(f"Validating SQL query (retry {retry_count}/{self.max_retries}): {query}")
        
        # Skip validation if disabled
        if not self.validation_enabled or self.validation_mode == "none":
            logger.debug("SQL validation is disabled")
            return True, None
            
        # For syntax-only validation, just check basic SQL syntax
        if self.validation_mode == "syntax_only":
            logger.debug("Performing syntax-only validation")
            try:
                sqlparse.parse(query)
                logger.debug("Basic SQL syntax check passed")
                return True, None
            except Exception as e:
                error_message = f"SQL syntax error: {str(e)}"
                logger.warning(f"SQL syntax validation failed: {error_message}")
                return False, error_message
        
        # Full validation (default)
        logger.debug("Performing full SQL validation (schema + syntax)")
        is_valid, error_message = self._validate_query(query)
        
        if not is_valid:
            logger.warning(f"SQL validation failed: {error_message}")
            return False, error_message
            
        # If we got here, the query is valid
        logger.info("Query validation successful")
        return True, None

    def _extract_table_aliases(self, tables: List[str]) -> Dict[str, str]:
        """Extract table aliases from table references."""
        aliases = {}
        
        for table_ref in tables:
            # Look for "AS" keyword (case-insensitive)
            if re.search(r"\s+(?i:as)\s+", table_ref):
                parts = re.split(r"\s+(?i:as)\s+", table_ref)  # Split on "as" or "AS" with spaces
                if len(parts) == 2:
                    table_name = parts[0].strip()
                    alias = parts[1].strip()
                    aliases[alias] = table_name
                    
                    # Also handle potential T1, T2 style aliases by adding lowercase/uppercase mappings
                    if re.match(r"^[Tt][0-9]+$", alias):  # Matches T1, t1, T2, etc.
                        aliases[alias.lower()] = table_name
                        aliases[alias.upper()] = table_name
            elif " " in table_ref:
                # Format: "table_name alias" (implicit alias without AS keyword)
                parts = table_ref.split()
                if len(parts) >= 2:
                    table_name = parts[0].strip()
                    alias = parts[1].strip()
                    aliases[alias] = table_name
                    
                    # Also handle potential T1, T2 style aliases by adding lowercase/uppercase mappings
                    if re.match(r"^[Tt][0-9]+$", alias):  # Matches T1, t1, T2, etc.
                        aliases[alias.lower()] = table_name
                        aliases[alias.upper()] = table_name
                    
                    # Look for one-letter aliases typically used in SQL (like 'c', 'o', 'p')
                    if len(alias) == 1:
                        aliases[alias.lower()] = table_name
                        aliases[alias.upper()] = table_name
                    
        logger.debug(f"Extracted aliases: {aliases}")
        return aliases

    def _extract_column_references(self, query: str) -> List[Tuple[str, str]]:
        """Extract column references with their table aliases from a SQL query.
        
        Returns:
            List of tuples of (table_alias, column_name)
        """
        # Extract column references with table aliases (T1.name, customers.id, etc.)
        column_pattern = r'([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)'
        column_refs = re.findall(column_pattern, query)
        
        return column_refs 
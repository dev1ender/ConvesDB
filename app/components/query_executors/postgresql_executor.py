"""
PostgreSQL query executor component.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from app.components.base_component import BaseComponent
from app.core.exceptions import ComponentRegistryError
from app.utils.logging_setup import TICK_ICON, CROSS_ICON


class PostgreSQLExecutor(BaseComponent):
    """
    Query executor component for PostgreSQL databases.
    
    This component executes SQL queries against a PostgreSQL database
    and returns the results.
    """
    
    def __init__(self, component_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the PostgreSQL query executor.
        
        Args:
            component_id: Unique identifier for the component
            config: Configuration parameters for the component
        """
        super().__init__(component_id, config)
        self.logger.debug(f"{TICK_ICON} Initializing PostgreSQLExecutor with id {component_id}")
        
        # Configuration options with defaults
        self.read_only = self.get_config_value("read_only", True)
        self.max_rows = self.get_config_value("max_rows", 1000)
        self.statement_timeout = self.get_config_value("statement_timeout_ms", 30000)
        self.use_cursor = self.get_config_value("use_cursor", False)
        self.cursor_size = self.get_config_value("cursor_size", 100)
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an SQL query against a PostgreSQL database.
        
        Args:
            context: Execution context containing the SQL query and connection info
            
        Returns:
            Dict[str, Any]: Updated context with query results
            
        Raises:
            ComponentRegistryError: If query execution fails
        """
        self.logger.debug(f"{TICK_ICON} Executing PostgreSQLExecutor for context keys: {list(context.keys())}")
        
        # Get required parameters from context
        sql_query = context.get("sql_query")
        connection = context.get("connection")
        params = context.get("query_params", {})
        
        # Validate required parameters
        if not sql_query:
            error_msg = f"{CROSS_ICON} No SQL query provided in context"
            self.logger.error(error_msg)
            return {"error": error_msg, "results": []}
        
        if not connection:
            error_msg = f"{CROSS_ICON} No database connection provided in context"
            self.logger.error(error_msg)
            return {"error": error_msg, "results": []}
        
        # Check if query is allowed in read-only mode
        if self.read_only and self._is_write_query(sql_query):
            error_msg = f"{CROSS_ICON} Write operation attempted in read-only mode"
            self.logger.error(error_msg)
            return {"error": error_msg, "results": []}
        
        try:
            # Create cursor
            cursor = connection.cursor()
            
            # Set statement timeout if configured
            if self.statement_timeout > 0:
                cursor.execute(f"SET statement_timeout = {self.statement_timeout}")
            
            # Execute query with parameters if provided
            if self.use_cursor and self._is_select_query(sql_query):
                # For large result sets, use server-side cursor
                named_cursor = connection.cursor(name='large_result_cursor')
                
                if params:
                    named_cursor.execute(sql_query, params)
                else:
                    named_cursor.execute(sql_query)
                
                results, has_more = self._fetch_with_cursor(named_cursor)
                named_cursor.close()
            else:
                # Standard execution
                if params:
                    cursor.execute(sql_query, params)
                else:
                    cursor.execute(sql_query)
                
                results, has_more = self._fetch_results(cursor)
            
            # Commit changes for write operations
            if not self.read_only and self._is_write_query(sql_query):
                connection.commit()
                self.logger.debug(f"{TICK_ICON} Changes committed to database")
            
            # Return results in context
            self.logger.info(f"{TICK_ICON} PostgreSQL query executed successfully by {self.component_id}")
            return {
                "results": results,
                "has_more": has_more,
                "query_executor": self.component_id
            }
        
        except Exception as e:
            error_msg = f"{CROSS_ICON} Error executing PostgreSQL query: {str(e)}"
            self.logger.error(error_msg)
            
            # Rollback in case of error
            try:
                connection.rollback()
            except:
                pass
            
            raise ComponentRegistryError(error_msg)
    
    def _fetch_results(self, cursor) -> Tuple[Any, bool]:
        """
        Fetch results from a cursor.
        
        Args:
            cursor: PostgreSQL cursor
            
        Returns:
            Tuple[Any, bool]: Results and a flag indicating if more results are available
        """
        # Check if query returns data
        if cursor.description:
            # Get column names
            columns = [column.name for column in cursor.description]
            
            # Fetch results with row limit
            rows = cursor.fetchmany(self.max_rows)
            
            # Convert to dictionaries
            results = []
            for row in rows:
                results.append({columns[i]: row[i] for i in range(len(columns))})
            
            # Check if more rows are available
            has_more = len(results) == self.max_rows and cursor.fetchone() is not None
            
            if has_more:
                self.logger.warning(f"{CROSS_ICON} Query results truncated to {self.max_rows} rows")
            
            return results, has_more
        else:
            # For non-SELECT queries, return affected row count
            return {"affected_rows": cursor.rowcount}, False
    
    def _fetch_with_cursor(self, cursor) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Fetch results using a server-side cursor for large result sets.
        
        Args:
            cursor: PostgreSQL named cursor
            
        Returns:
            Tuple[List[Dict[str, Any]], bool]: Results and a flag indicating if more results are available
        """
        # Get column names
        columns = [column.name for column in cursor.description]
        
        # Fetch results in batches
        results = []
        total_fetched = 0
        has_more = False
        
        while total_fetched < self.max_rows:
            # Fetch a batch
            batch = cursor.fetchmany(min(self.cursor_size, self.max_rows - total_fetched))
            
            if not batch:
                break
            
            # Convert to dictionaries
            for row in batch:
                results.append({columns[i]: row[i] for i in range(len(columns))})
            
            total_fetched += len(batch)
            
            # Check if we've reached the batch size limit
            if len(batch) < self.cursor_size:
                break
        
        # Check if more rows are available
        if total_fetched == self.max_rows and cursor.fetchone() is not None:
            has_more = True
            self.logger.warning(f"{CROSS_ICON} Query results truncated to {self.max_rows} rows")
        
        return results, has_more
    
    def _is_select_query(self, query: str) -> bool:
        """
        Check if a query is a SELECT statement.
        
        Args:
            query: SQL query
            
        Returns:
            bool: True if query is a SELECT statement, False otherwise
        """
        # Clean query
        clean_query = self._clean_query(query)
        
        # Get first word of query
        first_word = clean_query.split(' ', 1)[0].upper() if clean_query else ''
        
        return first_word == 'SELECT'
    
    def _is_write_query(self, query: str) -> bool:
        """
        Check if a query modifies the database.
        
        Args:
            query: SQL query
            
        Returns:
            bool: True if query modifies the database, False otherwise
        """
        # Check if query starts with a write operation keyword
        # (case-insensitive check)
        write_operations = [
            'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 
            'TRUNCATE', 'GRANT', 'REVOKE', 'BEGIN', 'COMMIT', 'ROLLBACK'
        ]
        
        # Clean query
        clean_query = self._clean_query(query)
        
        # Get first word of query
        first_word = clean_query.split(' ', 1)[0].upper() if clean_query else ''
        
        return first_word in write_operations
    
    def _clean_query(self, query: str) -> str:
        """
        Clean a query by removing comments and whitespace.
        
        Args:
            query: SQL query
            
        Returns:
            str: Cleaned query
        """
        # Strip comments and whitespace from beginning
        clean_query = query.strip()
        
        # Remove line comments
        clean_query = re.sub(r'--.*?(\r\n|\r|\n|$)', ' ', clean_query)
        
        # Remove block comments
        clean_query = re.sub(r'/\*.*?\*/', ' ', clean_query, flags=re.DOTALL)
        
        # Normalize whitespace
        clean_query = re.sub(r'\s+', ' ', clean_query).strip()
        
        return clean_query
    
    def validate_config(self) -> bool:
        """
        Validate the component configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        self.logger.debug("Validating config for PostgreSQLExecutor")
        valid = True
        max_rows = self.get_config_value("max_rows", 1000)
        if not isinstance(max_rows, int) or max_rows <= 0:
            self.logger.warning(f"{CROSS_ICON} max_rows must be a positive integer")
            valid = False
        timeout = self.get_config_value("statement_timeout_ms", 30000)
        if not isinstance(timeout, int) or timeout < 0:
            self.logger.warning(f"{CROSS_ICON} statement_timeout_ms must be a non-negative integer")
            valid = False
        if self.get_config_value("use_cursor", False):
            cursor_size = self.get_config_value("cursor_size", 100)
            if not isinstance(cursor_size, int) or cursor_size <= 0:
                self.logger.warning(f"{CROSS_ICON} cursor_size must be a positive integer")
                valid = False
        if valid:
            self.logger.info(f"{TICK_ICON} Config validated for PostgreSQLExecutor")
        else:
            self.logger.error(f"{CROSS_ICON} Config validation failed for PostgreSQLExecutor")
        return valid 
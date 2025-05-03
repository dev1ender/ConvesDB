"""
SQLite query executor component.
"""

import logging
import sqlite3
from typing import Any, Dict, List, Optional

from app.components.base_component import BaseComponent
from app.core.exceptions import ComponentRegistryError
from app.utils.logging_setup import TICK_ICON, CROSS_ICON


class SQLiteExecutor(BaseComponent):
    """
    Query executor component for SQLite databases.
    
    This component executes SQL queries against a SQLite database
    and returns the results.
    """
    
    def __init__(self, component_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the SQLite query executor.
        
        Args:
            component_id: Unique identifier for the component
            config: Configuration parameters for the component
        """
        super().__init__(component_id, config)
        self.logger.debug(f"{TICK_ICON} Initializing SQLiteExecutor with id {component_id}")
        
        # Configuration options with defaults
        self.read_only = self.get_config_value("read_only", True)
        self.max_rows = self.get_config_value("max_rows", 1000)
        self.timeout = self.get_config_value("timeout_seconds", 30)
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an SQL query against a SQLite database.
        
        Args:
            context: Execution context containing the SQL query and connection info
            
        Returns:
            Dict[str, Any]: Updated context with query results
            
        Raises:
            ComponentRegistryError: If query execution fails
        """
        self.logger.debug(f"{TICK_ICON} Executing SQLiteExecutor for context keys: {list(context.keys())}")
        
        # Get required parameters from context
        sql_query = context.get("sql_query")
        db_path = context.get("db_path")
        connection = context.get("connection")
        params = context.get("query_params", {})
        
        # Validate required parameters
        if not sql_query:
            error_msg = f"{CROSS_ICON} No SQL query provided in context"
            self.logger.error(error_msg)
            return {"error": error_msg, "results": []}
        
        if not connection and not db_path:
            error_msg = f"{CROSS_ICON} Neither database connection nor path provided in context"
            self.logger.error(error_msg)
            return {"error": error_msg, "results": []}
        
        # Check if query is allowed in read-only mode
        if self.read_only and self._is_write_query(sql_query):
            error_msg = f"{CROSS_ICON} Write operation attempted in read-only mode"
            self.logger.error(error_msg)
            return {"error": error_msg, "results": []}
        
        try:
            # Use existing connection or create a new one
            if connection:
                self.logger.debug("Using provided database connection")
                conn = connection
                should_close = False
            else:
                self.logger.debug(f"Creating new connection to {db_path}")
                conn = sqlite3.connect(db_path, timeout=self.timeout)
                conn.row_factory = sqlite3.Row
                should_close = True
            
            # Create cursor
            cursor = conn.cursor()
            
            # Execute query with parameters if provided
            if params:
                cursor.execute(sql_query, params)
            else:
                cursor.execute(sql_query)
            
            # Get results if query returns data
            results = []
            if cursor.description:
                # Get column names
                columns = [column[0] for column in cursor.description]
                
                # Fetch results with row limit
                rows = cursor.fetchmany(self.max_rows)
                
                # Convert to dictionaries
                for row in rows:
                    # Handle both tuple and sqlite3.Row objects
                    if isinstance(row, sqlite3.Row):
                        results.append(dict(row))
                    else:
                        results.append({columns[i]: row[i] for i in range(len(columns))})
                
                # Note if more rows are available
                has_more = len(results) == self.max_rows and cursor.fetchone() is not None
                
                if has_more:
                    self.logger.warning(f"{CROSS_ICON} Query results truncated to {self.max_rows} rows")
            else:
                # For non-SELECT queries, return affected row count
                results = {"affected_rows": cursor.rowcount}
            
            # Commit changes for write operations
            if not self.read_only and self._is_write_query(sql_query):
                conn.commit()
                self.logger.debug(f"{TICK_ICON} Changes committed to database")
            
            # Close connection if we created it
            if should_close:
                conn.close()
            
            # Return results in context
            self.logger.info(f"{TICK_ICON} SQLite query executed successfully by {self.component_id}")
            return {
                "results": results,
                "has_more": has_more if 'has_more' in locals() else False,
                "query_executor": self.component_id
            }
        
        except Exception as e:
            error_msg = f"{CROSS_ICON} Error executing SQLite query: {str(e)}"
            self.logger.error(error_msg)
            
            # Close connection if we created it and an error occurred
            if 'should_close' in locals() and should_close and 'conn' in locals():
                conn.close()
            
            raise ComponentRegistryError(error_msg)
    
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
            'PRAGMA', 'ATTACH', 'DETACH', 'BEGIN', 'COMMIT', 'ROLLBACK'
        ]
        
        # Strip comments and whitespace from beginning
        clean_query = query.strip()
        
        # Remove comments
        while clean_query.startswith('--') or clean_query.startswith('/*'):
            if clean_query.startswith('--'):
                # Find end of line comment
                newline_pos = clean_query.find('\n')
                if newline_pos == -1:
                    return False  # Only comment in query
                clean_query = clean_query[newline_pos + 1:].strip()
            else:
                # Find end of block comment
                end_comment_pos = clean_query.find('*/', 2)
                if end_comment_pos == -1:
                    return False  # Unclosed comment
                clean_query = clean_query[end_comment_pos + 2:].strip()
        
        # Get first word of query
        first_word = clean_query.split(' ', 1)[0].upper()
        
        return first_word in write_operations
    
    def validate_config(self) -> bool:
        """
        Validate the component configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        self.logger.debug("Validating config for SQLiteExecutor")
        valid = True
        max_rows = self.get_config_value("max_rows", 1000)
        if not isinstance(max_rows, int) or max_rows <= 0:
            self.logger.warning(f"{CROSS_ICON} max_rows must be a positive integer")
            valid = False
        timeout = self.get_config_value("timeout_seconds", 30)
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            self.logger.warning(f"{CROSS_ICON} timeout_seconds must be a positive number")
            valid = False
        if valid:
            self.logger.info(f"{TICK_ICON} Config validated for SQLiteExecutor")
        else:
            self.logger.error(f"{CROSS_ICON} Config validation failed for SQLiteExecutor")
        return valid 
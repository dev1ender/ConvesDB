from typing import Dict, List, Any, Optional, Tuple
import time
from app.database import DatabaseConnector
from app.logging_setup import get_logger

# Setup module logger
logger = get_logger(__name__)

class QueryExecutor:
    """Component responsible for executing SQL queries safely."""
    
    def __init__(self, db_connector: DatabaseConnector):
        self.db_connector = db_connector
        self.read_only = True  # Default to read-only for safety
        self.timeout_seconds = 10  # Default timeout
        logger.debug(f"QueryExecutor initialized with read_only={self.read_only}, timeout={self.timeout_seconds}s")
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute a SQL query against the database.
        
        Args:
            query: The SQL query to execute
            
        Returns:
            A list of result dictionaries
            
        Raises:
            Exception: If query execution fails
        """
        logger.info(f"Executing SQL query: {query}")
        
        # Safety check for read-only mode
        if self.read_only and not self._is_read_only_query(query):
            error_msg = "Write operations are disabled in read-only mode"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Additional validation for safety
        if not self._is_safe_query(query):
            error_msg = "Query validation failed: potentially unsafe operation"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Execute the query with timeout
        start_time = time.time()
        logger.debug(f"Query execution started at {start_time}")
        
        try:
            logger.debug("Sending query to database connector")
            results = self._execute_with_timeout(query)
            
            execution_time = time.time() - start_time
            logger.debug(f"Query execution took {execution_time:.3f} seconds")
            
            # Log success
            logger.info(f"Query execution successful, returned {len(results)} results")
            logger.debug(f"Query results: {results[:10]}{'...' if len(results) > 10 else ''}")
            
            return results
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Database returned error: {error_msg}")
            raise Exception(error_msg)
    
    def _is_select_query(self, query: str) -> bool:
        """Check if a query is a SELECT query (simple check)."""
        query = query.strip().lower()
        is_select = query.startswith("select") and not any(
            dangerous_term in query 
            for dangerous_term in ["insert", "update", "delete", "drop", "alter", "create"]
        )
        
        if is_select:
            logger.debug("Query validated as safe SELECT query")
        else:
            logger.warning(f"Query rejected as non-SELECT or potentially dangerous: {query}")
        
        return is_select 

    def _is_read_only_query(self, query: str) -> bool:
        """Check if a query is a read-only query."""
        query = query.strip().lower()
        return query.startswith(("select", "show", "describe", "explain"))

    def _is_safe_query(self, query: str) -> bool:
        """Check if a query is safe to execute."""
        return self._is_select_query(query) or self._is_read_only_query(query)

    def _execute_with_timeout(self, query: str) -> List[Dict[str, Any]]:
        """Execute a query with timeout handling."""
        start_time = time.time()
        logger.debug(f"Query execution started at {start_time}")
        
        try:
            # Execute the query
            logger.debug("Sending query to database connector")
            results = self.db_connector.run(query)
            
            execution_time = time.time() - start_time
            logger.debug(f"Query execution took {execution_time:.3f} seconds")
            
            # Check for timeout
            if execution_time > self.timeout_seconds:
                error_msg = f"Query execution timed out (limit: {self.timeout_seconds}s)"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            return results
            
        except Exception as e:
            error_msg = f"Error executing query: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) 
"""
Query executor implementation for the RAG-POC application.
"""

from typing import Dict, List, Any, Optional, Tuple
from app.interfaces.agents import QueryExecutorInterface
from app.interfaces.database import DatabaseConnector
from app.logging_setup import get_logger

# Setup module logger
logger = get_logger(__name__)

class QueryExecutor(QueryExecutorInterface):
    """Executes SQL queries against the database."""
    
    def __init__(self, db_connector: DatabaseConnector):
        """Initialize the query executor.
        
        Args:
            db_connector: Database connector instance
        """
        self.db_connector = db_connector
        self.read_only = True  # Default to read-only for safety
        logger.debug("QueryExecutor initialized with read_only=True")
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results.
        
        Args:
            query: The SQL query to execute
            
        Returns:
            List of results as dictionaries
            
        Raises:
            Exception: If the query is not allowed in read-only mode
                      or if there is a database error
        """
        # Check if the query is read-only (SELECT)
        is_read_only = self._is_read_only_query(query)
        
        if not is_read_only and self.read_only:
            error_msg = "Attempted to execute non-SELECT query in read-only mode"
            logger.warning(error_msg)
            raise Exception(error_msg)
        
        try:
            logger.debug(f"Executing query: {query}")
            results = self.db_connector.run(query)
            logger.info(f"Query executed successfully, returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise
    
    def _is_read_only_query(self, query: str) -> bool:
        """Check if a query is read-only (SELECT only).
        
        Args:
            query: The SQL query to check
            
        Returns:
            True if the query is read-only, False otherwise
        """
        # Normalize query - remove leading/trailing whitespace and convert to lowercase
        normalized_query = query.strip().lower()
        
        # Check if the query starts with SELECT
        return normalized_query.startswith("select") 
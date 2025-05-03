"""
Syntax verifier component.
"""

import logging
import re
import sqlite3
from typing import Any, Dict, List, Optional

from app.components.base_component import BaseComponent
from app.core.exceptions import ComponentRegistryError


class SyntaxVerifier(BaseComponent):
    """
    Query syntax verification component.
    
    This component verifies that queries are syntactically valid
    and don't contain potentially harmful operations.
    """
    
    def __init__(self, component_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the syntax verifier.
        
        Args:
            component_id: Unique identifier for the component
            config: Configuration parameters for the component
        """
        super().__init__(component_id, config)
        
        # Configuration options with defaults
        self.db_type = self.get_config_value("db_type", "sqlite")
        self.allow_write = self.get_config_value("allow_write", False)
        self.disallowed_keywords = self.get_config_value("disallowed_keywords", [])
        
        # Default disallowed operations based on db_type
        if self.db_type == "sqlite":
            self.default_disallowed = ["ATTACH", "DETACH", "VACUUM", "PRAGMA"]
            if not self.allow_write:
                self.default_disallowed.extend(["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "REPLACE"])
        
        elif self.db_type == "postgres":
            self.default_disallowed = ["VACUUM", "REINDEX", "CLUSTER"]
            if not self.allow_write:
                self.default_disallowed.extend(["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "COMMENT", "COPY", "GRANT", "REVOKE"])
        
        elif self.db_type == "neo4j":
            self.default_disallowed = []
            if not self.allow_write:
                self.default_disallowed.extend(["CREATE", "DELETE", "SET", "REMOVE", "MERGE", "DROP"])
        
        # Combine default and custom disallowed keywords
        self.all_disallowed = set(self.default_disallowed + self.disallowed_keywords)
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the component to verify query syntax.
        
        Args:
            context: Execution context containing the query to verify
            
        Returns:
            Dict[str, Any]: Updated context with verification result
            
        Raises:
            ComponentRegistryError: If verification fails
        """
        self.logger.debug("Verifying query syntax")
        
        # Get query from context
        query = context.get("query", "")
        sql_query = context.get("sql_query", query)  # Use sql_query if available, otherwise use query
        
        if not sql_query:
            error_msg = "No query found in context"
            self.logger.error(error_msg)
            return {"is_valid": False, "error": error_msg}
        
        try:
            # Check for disallowed keywords
            disallowed_found = self._check_disallowed_keywords(sql_query)
            if disallowed_found:
                error_msg = f"Query contains disallowed keywords: {', '.join(disallowed_found)}"
                self.logger.warning(error_msg)
                return {"is_valid": False, "error": error_msg}
            
            # Verify SQL syntax based on database type
            if self.db_type == "sqlite":
                syntax_error = self._verify_sqlite_syntax(sql_query)
            elif self.db_type == "postgres":
                syntax_error = self._verify_postgres_syntax(sql_query)
            elif self.db_type == "neo4j":
                syntax_error = self._verify_neo4j_syntax(sql_query)
            else:
                syntax_error = "Unsupported database type"
            
            if syntax_error:
                self.logger.warning(f"Syntax verification failed: {syntax_error}")
                return {"is_valid": False, "error": syntax_error}
            
            self.logger.debug("Query syntax verified")
            
            # Return verification result
            return {
                "is_valid": True,
                "syntax_verified": True,
                "syntax_verifier": self.component_id
            }
        
        except Exception as e:
            error_msg = f"Error verifying query syntax: {str(e)}"
            self.logger.error(error_msg)
            raise ComponentRegistryError(error_msg)
    
    def _check_disallowed_keywords(self, query: str) -> List[str]:
        """
        Check if query contains disallowed keywords.
        
        Args:
            query: SQL query
            
        Returns:
            List[str]: List of disallowed keywords found
        """
        # Normalize query for case-insensitive comparison
        normalized_query = query.upper()
        found = []
        
        for keyword in self.all_disallowed:
            # Check if keyword exists as a whole word
            pattern = r'\b' + re.escape(keyword.upper()) + r'\b'
            if re.search(pattern, normalized_query):
                found.append(keyword)
        
        return found
    
    def _verify_sqlite_syntax(self, query: str) -> Optional[str]:
        """
        Verify SQLite syntax by parsing the query.
        
        Args:
            query: SQL query
            
        Returns:
            Optional[str]: Error message if syntax is invalid, None otherwise
        """
        try:
            # Create a temporary in-memory database
            conn = sqlite3.connect(":memory:")
            cursor = conn.cursor()
            
            # Parse query without executing it
            cursor.execute(f"EXPLAIN {query}")
            
            # Close connection
            conn.close()
            
            return None  # No error
        
        except sqlite3.Error as e:
            return f"SQLite syntax error: {str(e)}"
    
    def _verify_postgres_syntax(self, query: str) -> Optional[str]:
        """
        Verify PostgreSQL syntax (placeholder implementation).
        
        Args:
            query: SQL query
            
        Returns:
            Optional[str]: Error message if syntax is invalid, None otherwise
        """
        # In a real implementation, this would use psycopg2 to verify syntax
        # without executing the query, similar to SQLite implementation.
        # For now, we'll just do some basic checks.
        
        if not query.strip().endswith(';'):
            return "PostgreSQL query should end with semicolon"
        
        return None  # No error detected
    
    def _verify_neo4j_syntax(self, query: str) -> Optional[str]:
        """
        Verify Neo4j Cypher syntax (placeholder implementation).
        
        Args:
            query: Cypher query
            
        Returns:
            Optional[str]: Error message if syntax is invalid, None otherwise
        """
        # In a real implementation, this would use the Neo4j driver to verify syntax
        # without executing the query. For now, we'll just do some basic checks.
        
        if not query.strip().endswith(';') and not query.strip().endswith(')'):
            return "Neo4j query should end with semicolon or closing parenthesis"
        
        return None  # No error detected
    
    def validate_config(self) -> bool:
        """
        Validate the component configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        # Validate db_type
        db_type = self.get_config_value("db_type", "sqlite")
        if db_type not in ["sqlite", "postgres", "neo4j"]:
            self.logger.warning("db_type must be one of: sqlite, postgres, neo4j")
            return False
        
        # Validate allow_write
        allow_write = self.get_config_value("allow_write", False)
        if not isinstance(allow_write, bool):
            self.logger.warning("allow_write must be a boolean")
            return False
        
        # Validate disallowed_keywords
        disallowed = self.get_config_value("disallowed_keywords", [])
        if not isinstance(disallowed, list):
            self.logger.warning("disallowed_keywords must be a list")
            return False
        
        return True 
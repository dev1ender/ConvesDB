"""
Neo4j query executor component.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from app.components.base_component import BaseComponent
from app.core.exceptions import ComponentRegistryError
from app.utils.logging_setup import TICK_ICON, CROSS_ICON


class Neo4jExecutor(BaseComponent):
    """
    Query executor component for Neo4j graph databases.
    
    This component executes Cypher queries against a Neo4j database
    and returns the results.
    """
    
    def __init__(self, component_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Neo4j query executor.
        
        Args:
            component_id: Unique identifier for the component
            config: Configuration parameters for the component
        """
        super().__init__(component_id, config)
        self.logger.debug(f"{TICK_ICON} Initializing Neo4jExecutor with id {component_id}")
        
        # Configuration options with defaults
        self.read_only = self.get_config_value("read_only", True)
        self.max_rows = self.get_config_value("max_rows", 1000)
        self.timeout = self.get_config_value("timeout_seconds", 30)
        self.include_stats = self.get_config_value("include_stats", False)
        self.default_database = self.get_config_value("default_database", None)
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a Cypher query against a Neo4j database.
        
        Args:
            context: Execution context containing the Cypher query and connection info
            
        Returns:
            Dict[str, Any]: Updated context with query results
            
        Raises:
            ComponentRegistryError: If query execution fails
        """
        self.logger.debug(f"{TICK_ICON} Executing Neo4jExecutor for context keys: {list(context.keys())}")
        
        # Get required parameters from context
        cypher_query = context.get("cypher_query", context.get("query", None))
        session = context.get("session")
        driver = context.get("driver")
        params = context.get("query_params", {})
        database = context.get("database", self.default_database)
        
        # Validate required parameters
        if not cypher_query:
            error_msg = f"{CROSS_ICON} No Cypher query provided in context"
            self.logger.error(error_msg)
            return {"error": error_msg, "results": []}
        
        if not session and not driver:
            error_msg = f"{CROSS_ICON} No Neo4j session or driver provided in context"
            self.logger.error(error_msg)
            return {"error": error_msg, "results": []}
        
        # Check if query is allowed in read-only mode
        if self.read_only and self._is_write_query(cypher_query):
            error_msg = f"{CROSS_ICON} Write operation attempted in read-only mode"
            self.logger.error(error_msg)
            return {"error": error_msg, "results": []}
        
        try:
            # Use existing session or create a new one
            should_close = False
            
            if session:
                self.logger.debug("Using provided Neo4j session")
            else:
                self.logger.debug("Creating new Neo4j session from driver")
                if database:
                    session = driver.session(database=database)
                else:
                    session = driver.session()
                should_close = True
            
            # Execute the query based on read vs write
            if self._is_write_query(cypher_query) and not self.read_only:
                results, has_more, stats = self._execute_write_query(session, cypher_query, params)
            else:
                results, has_more, stats = self._execute_read_query(session, cypher_query, params)
            
            # Close session if we created it
            if should_close:
                session.close()
            
            # Return results in context
            response = {
                "results": results,
                "has_more": has_more,
                "query_executor": self.component_id
            }
            
            # Include query stats if enabled
            if self.include_stats and stats:
                response["stats"] = stats
            
            self.logger.info(f"{TICK_ICON} Neo4j query executed successfully by {self.component_id}")
            return response
        
        except Exception as e:
            error_msg = f"{CROSS_ICON} Error executing Neo4j query: {str(e)}"
            self.logger.error(error_msg)
            
            # Close session if we created it and an error occurred
            if 'should_close' in locals() and should_close and 'session' in locals():
                session.close()
            
            raise ComponentRegistryError(error_msg)
    
    def _execute_read_query(
        self, session: Any, query: str, params: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], bool, Optional[Dict[str, Any]]]:
        """
        Execute a read-only query.
        
        Args:
            session: Neo4j session
            query: Cypher query
            params: Query parameters
            
        Returns:
            Tuple[List[Dict[str, Any]], bool, Optional[Dict[str, Any]]]: 
                Results, has_more flag, and stats (if available)
        """
        # Execute query with parameters
        result = session.run(query, params)
        
        # Process results
        return self._process_results(result)
    
    def _execute_write_query(
        self, session: Any, query: str, params: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], bool, Optional[Dict[str, Any]]]:
        """
        Execute a write query.
        
        Args:
            session: Neo4j session
            query: Cypher query
            params: Query parameters
            
        Returns:
            Tuple[List[Dict[str, Any]], bool, Optional[Dict[str, Any]]]: 
                Results, has_more flag, and stats (if available)
        """
        # Execute query with parameters in a write transaction
        # For Neo4j 4.x and above (with explicit transaction functions)
        try:
            with session.begin_transaction() as tx:
                result = tx.run(query, params)
                results, has_more, stats = self._process_results(result)
                tx.commit()
                return results, has_more, stats
        except AttributeError:
            # Fallback for Neo4j 3.x (with transaction functions)
            try:
                with session.transaction() as tx:
                    result = tx.run(query, params)
                    return self._process_results(result)
            except AttributeError:
                # Direct execution as last resort
                result = session.run(query, params)
                return self._process_results(result)
    
    def _process_results(self, result: Any) -> Tuple[List[Dict[str, Any]], bool, Optional[Dict[str, Any]]]:
        """
        Process query results.
        
        Args:
            result: Neo4j result object
            
        Returns:
            Tuple[List[Dict[str, Any]], bool, Optional[Dict[str, Any]]]: 
                Results, has_more flag, and stats (if available)
        """
        results = []
        stats = None
        has_more = False
        
        # Get result keys/columns
        keys = result.keys()
        
        # Fetch results with row limit
        count = 0
        for record in result:
            if count >= self.max_rows:
                has_more = True
                break
            
            # Convert record to dict, with special handling for nodes, relationships and paths
            row_dict = {}
            for key in keys:
                row_dict[key] = self._convert_neo4j_value(record[key])
            
            results.append(row_dict)
            count += 1
        
        # Get query stats if available
        if self.include_stats:
            try:
                summary = result.summary()
                stats = {
                    "nodes_created": summary.counters.nodes_created,
                    "nodes_deleted": summary.counters.nodes_deleted,
                    "relationships_created": summary.counters.relationships_created,
                    "relationships_deleted": summary.counters.relationships_deleted,
                    "properties_set": summary.counters.properties_set,
                    "labels_added": summary.counters.labels_added,
                    "labels_removed": summary.counters.labels_removed,
                    "contains_updates": summary.counters.contains_updates
                }
            except:
                # Stats not available
                pass
        
        return results, has_more, stats
    
    def _convert_neo4j_value(self, value: Any) -> Any:
        """
        Convert Neo4j types to Python native types.
        
        Args:
            value: Neo4j value
            
        Returns:
            Any: Python native value
        """
        # Handle None
        if value is None:
            return None
        
        # Handle Node
        if hasattr(value, 'labels') and hasattr(value, 'id'):
            # Convert Neo4j Node
            result = {
                "_type": "node",
                "_id": value.id,
                "labels": list(value.labels),
                "properties": dict(value)
            }
            return result
        
        # Handle Relationship
        if hasattr(value, 'type') and hasattr(value, 'start_node') and hasattr(value, 'end_node'):
            # Convert Neo4j Relationship
            result = {
                "_type": "relationship",
                "_id": value.id,
                "type": value.type,
                "start_node_id": value.start_node.id if hasattr(value.start_node, 'id') else None,
                "end_node_id": value.end_node.id if hasattr(value.end_node, 'id') else None,
                "properties": dict(value)
            }
            return result
        
        # Handle Path
        if hasattr(value, 'nodes') and hasattr(value, 'relationships'):
            # Convert Neo4j Path
            nodes = [self._convert_neo4j_value(node) for node in value.nodes]
            relationships = [self._convert_neo4j_value(rel) for rel in value.relationships]
            
            result = {
                "_type": "path",
                "nodes": nodes,
                "relationships": relationships
            }
            return result
        
        # Handle basic collections
        if isinstance(value, list):
            return [self._convert_neo4j_value(item) for item in value]
        
        if isinstance(value, dict):
            return {k: self._convert_neo4j_value(v) for k, v in value.items()}
        
        # Return primitive values as-is
        return value
    
    def _is_write_query(self, query: str) -> bool:
        """
        Check if a Cypher query modifies the database.
        
        Args:
            query: Cypher query
            
        Returns:
            bool: True if query modifies the database, False otherwise
        """
        # Check if query contains write operations
        # Clean the query first
        clean_query = self._clean_query(query).upper()
        
        # List of Cypher write operations
        write_operations = [
            'CREATE', 'MERGE', 'DELETE', 'REMOVE', 'SET', 'DROP',
            'CALL {', 'CALL db.', 'WITH'  # Some CALL procedures can write
        ]
        
        # Check if query contains any write operations
        for op in write_operations:
            if op in clean_query:
                # Additional check for WITH to avoid false positives
                if op == 'WITH':
                    # Check if WITH is followed by a write operation
                    with_pattern = r'WITH\s+.+?\b(CREATE|MERGE|DELETE|REMOVE|SET)\b'
                    if re.search(with_pattern, clean_query, re.IGNORECASE | re.DOTALL):
                        return True
                else:
                    return True
        
        return False
    
    def _clean_query(self, query: str) -> str:
        """
        Clean a query by removing comments and normalizing whitespace.
        
        Args:
            query: Cypher query
            
        Returns:
            str: Cleaned query
        """
        # Strip comments and whitespace from beginning
        clean_query = query.strip()
        
        # Remove line comments
        clean_query = re.sub(r'//.*?(\r\n|\r|\n|$)', ' ', clean_query)
        
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
        self.logger.debug("Validating config for Neo4jExecutor")
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
            self.logger.info(f"{TICK_ICON} Config validated for Neo4jExecutor")
        else:
            self.logger.error(f"{CROSS_ICON} Config validation failed for Neo4jExecutor")
        return valid 
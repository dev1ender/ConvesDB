"""
SQLite service implementation.
"""

import logging
import os
import sqlite3
from typing import Any, Dict, List, Optional

from app.services.base_service import BaseService
from app.interfaces.workflow import Workflow
from app.workflows.base_workflow import BaseWorkflow
from app.core.exceptions import ServiceError
from app.core.component_registry import ComponentRegistry


class SQLiteService(BaseService):
    """
    Service implementation for SQLite database.
    
    This service provides functionality for working with SQLite databases,
    including query execution, schema extraction, and data retrieval.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the SQLite service.
        
        Args:
            config: Configuration parameters for the service
        """
        # Make sure to initialize the base service properly
        super().__init__(config)
        
        # Important: set initialized to False until initialize() is called
        self.initialized = False
        
        # Get SQLite database path from config
        self.db_path = self.get_config_value("db_path", "example.sqlite")
        
        # Connection and cursor (initialized in initialize method)
        self.connection = None
        self.cursor = None
        
        # Component registry (set during initialization)
        self.component_registry = None
    
    def initialize(self) -> bool:
        """
        Initialize the SQLite service.
        
        Returns:
            bool: True if initialization was successful
        """
        try:
            self.logger.info(f"Initializing SQLite service with database: {self.db_path}")
            
            # Log initial state
            self.logger.debug(f"Initialized flag before: {self.initialized}")
            
            # Ensure database directory exists
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
            
            # Connect to database
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
            
            # Explicitly set initialized flag to True
            self.initialized = True
            
            # Log final state
            self.logger.debug(f"Initialized flag after: {self.initialized}")
            
            self.logger.info("SQLite service initialized successfully")
            return True
        
        except Exception as e:
            self.logger.error(f"Error initializing SQLite service: {str(e)}")
            # Make sure to set initialized to False in case of failure
            self.initialized = False
            return False
    
    def set_component_registry(self, registry: ComponentRegistry) -> None:
        """
        Set the component registry for this service.
        
        Args:
            registry: Component registry instance
        """
        self.component_registry = registry
        
        # Register default workflows if component registry is provided
        if self.component_registry:
            self._register_default_workflows()
    
    def _register_default_workflows(self) -> None:
        """Register default workflows for this service."""
        try:
            # Skip if component registry is not set
            if not self.component_registry:
                return
            
            # Create and register default workflow
            default_workflow = BaseWorkflow(
                "sqlite_default",
                self.component_registry,
                [
                    {
                        "id": "prompt_generation",
                        "component_type": "prompt_generators",
                        "component_id": "simple_prompt",
                        "config": {
                            "template": "Given the SQLite schema:\n\n{schema}\n\nGenerate SQL for the following query: {query}"
                        }
                    },
                    # Additional stages would be defined here
                ]
            )
            
            self.register_workflow(default_workflow)
            self.logger.info("Registered default workflow for SQLite service")
        
        except Exception as e:
            self.logger.error(f"Error registering default workflows: {str(e)}")
    
    def shutdown(self) -> None:
        """
        Shutdown the SQLite service.
        
        This method closes the database connection and releases resources.
        """
        self.logger.info("Shutting down SQLite service")
        
        if self.connection:
            try:
                self.connection.close()
                self.logger.debug("SQLite database connection closed")
            except Exception as e:
                self.logger.error(f"Error closing SQLite connection: {str(e)}")
        
        self.initialized = False
    
    def health_check(self) -> bool:
        """
        Check if the SQLite service is healthy.
        
        Returns:
            bool: True if service is healthy, False otherwise
        """
        self.logger.debug("Running SQLite health check...")
        self.logger.debug(f"Initialized flag status: {self.initialized}")
        
        if not self.initialized:
            self.logger.warning("Health check failed: SQLite service not initialized")
            return False
        
        if not self.connection:
            self.logger.warning("Health check failed: No active connection")
            return False
        
        try:
            # Check if connection is still valid
            self.logger.debug("Checking connection with simple query...")
            self.cursor.execute("SELECT 1")
            result = self.cursor.fetchone()
            
            if result is None or result[0] != 1:
                self.logger.warning("Health check failed: Invalid query result")
                return False
            
            # Verify we can access tables
            self.logger.debug("Checking table access...")
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
            table_result = self.cursor.fetchone()
            
            if table_result is None:
                self.logger.warning("Health check found no tables in the database")
                # Create a test table if none exists
                self.logger.debug("Creating a test table for health check...")
                self.cursor.execute("CREATE TABLE IF NOT EXISTS system_health_check (id INTEGER PRIMARY KEY)")
                self.connection.commit()
            
            self.logger.info("SQLite health check passed")
            return True
        
        except sqlite3.OperationalError as e:
            self.logger.warning(f"SQLite health check failed with operational error: {str(e)}")
            return False
        except sqlite3.DatabaseError as e:
            self.logger.warning(f"SQLite health check failed with database error: {str(e)}")
            return False
        except Exception as e:
            self.logger.warning(f"SQLite health check failed: {str(e)}")
            return False
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a SQL query.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            List[Dict[str, Any]]: Query results
            
        Raises:
            ServiceError: If query execution fails
        """
        if not self.initialized:
            raise ServiceError("SQLite service is not initialized")
        
        try:
            # Execute query
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            # Get column names
            columns = [column[0] for column in self.cursor.description] if self.cursor.description else []
            
            # Fetch results
            rows = self.cursor.fetchall()
            
            # Convert to dictionaries
            results = []
            for row in rows:
                results.append({columns[i]: row[i] for i in range(len(columns))})
            
            return results
        
        except Exception as e:
            self.logger.error(f"Error executing query: {str(e)}")
            raise ServiceError(f"Error executing query: {str(e)}")
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get the SQLite database schema.
        
        Returns:
            Dict[str, Any]: Database schema information
            
        Raises:
            ServiceError: If schema extraction fails
        """
        if not self.initialized:
            raise ServiceError("SQLite service is not initialized")
        
        try:
            # Get table names
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in self.cursor.fetchall()]
            
            schema = {"tables": {}}
            
            # Get schema for each table
            for table in tables:
                # Get table info
                self.cursor.execute(f"PRAGMA table_info({table})")
                columns = []
                
                for row in self.cursor.fetchall():
                    columns.append({
                        "name": row[1],
                        "type": row[2],
                        "not_null": bool(row[3]),
                        "default": row[4],
                        "primary_key": bool(row[5])
                    })
                
                schema["tables"][table] = {
                    "columns": columns
                }
            
            return schema
        
        except Exception as e:
            self.logger.error(f"Error extracting schema: {str(e)}")
            raise ServiceError(f"Error extracting schema: {str(e)}")
    
    def process_query(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Process a natural language query.
        
        Args:
            query: Natural language query
            **kwargs: Additional parameters
            
        Returns:
            Dict[str, Any]: Query processing result
            
        Raises:
            ServiceError: If query processing fails
        """
        try:
            # Get schema for context
            schema = self.get_schema()
            
            # Create input context
            context = {
                "query": query,
                "schema": schema,
                **kwargs
            }
            
            # Get default workflow ID from config or use "sqlite_default"
            default_workflow_id = self.get_config_value("default_workflow", "sqlite_default")
            
            # Check if default workflow exists
            if default_workflow_id not in self._workflows:
                raise ServiceError(f"Default workflow not found: {default_workflow_id}")
            
            # Execute default workflow
            result = self.execute_workflow(default_workflow_id, context)
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            raise ServiceError(f"Error processing query: {str(e)}")
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get service metadata.
        
        Returns:
            Dict[str, Any]: Service metadata
        """
        metadata = super().get_metadata()
        
        # Add SQLite-specific metadata
        if self.initialized:
            try:
                # Get SQLite version
                self.cursor.execute("SELECT sqlite_version()")
                sqlite_version = self.cursor.fetchone()[0]
                
                # Get database file size
                db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                
                # Add to metadata
                metadata.update({
                    "sqlite_version": sqlite_version,
                    "db_path": self.db_path,
                    "db_size_bytes": db_size,
                    "tables": list(self.get_schema()["tables"].keys()) if self.initialized else []
                })
            except Exception as e:
                self.logger.error(f"Error getting SQLite metadata: {str(e)}")
        
        return metadata 
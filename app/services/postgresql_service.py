"""
PostgreSQL service implementation.
"""

import logging
import os
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

from app.services.base_service import BaseService
from app.interfaces.workflow import Workflow
from app.workflows.base_workflow import BaseWorkflow
from app.core.exceptions import ServiceError
from app.core.component_registry import ComponentRegistry


class PostgreSQLService(BaseService):
    """
    Service implementation for PostgreSQL database.
    
    This service provides functionality for working with PostgreSQL databases,
    including query execution, schema extraction, and data retrieval.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the PostgreSQL service.
        
        Args:
            config: Configuration parameters for the service
        """
        super().__init__(config)
        
        # PostgreSQL connection parameters
        self.host = self.get_config_value("host", "localhost")
        self.port = self.get_config_value("port", 5432)
        self.database = self.get_config_value("database", "postgres")
        self.user = self.get_config_value("user", "postgres")
        self.password = self.get_config_value("password", "postgres")
        self.schema = self.get_config_value("schema", "public")
        
        # Connection and cursor (initialized in initialize method)
        self.connection = None
        self.cursor = None
        
        # Component registry (set during initialization)
        self.component_registry = None
    
    def initialize(self) -> bool:
        """
        Initialize the PostgreSQL service.
        
        Returns:
            bool: True if initialization was successful
        """
        try:
            self.logger.info(f"Initializing PostgreSQL service with database: {self.database} on {self.host}:{self.port}")
            
            # Connect to database
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            
            # Create cursor with dictionary factory
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            # Set initialized flag
            self.initialized = True
            
            self.logger.info("PostgreSQL service initialized successfully")
            return True
        
        except Exception as e:
            self.logger.error(f"Error initializing PostgreSQL service: {str(e)}")
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
                "postgresql_default",
                self.component_registry,
                [
                    {
                        "id": "schema_generation",
                        "component_type": "schema_generators",
                        "component_id": "postgresql_schema",
                        "config": {
                            "schema": self.schema
                        }
                    },
                    {
                        "id": "prompt_generation",
                        "component_type": "prompt_generators",
                        "component_id": "context_aware_prompt",
                        "config": {
                            "template": "Given the PostgreSQL schema:\n\n{schema}\n\nGenerate SQL for the following query: {query}",
                            "include_examples": True
                        }
                    },
                    {
                        "id": "query_generation",
                        "component_type": "query_executors",
                        "component_id": "postgresql_executor",
                        "config": {
                            "read_only": True
                        }
                    },
                    {
                        "id": "response_formatting",
                        "component_type": "response_formatters",
                        "component_id": "json_formatter",
                        "config": {
                            "include_metadata": True
                        }
                    }
                ]
            )
            
            self.register_workflow(default_workflow)
            self.logger.info("Registered default workflow for PostgreSQL service")
        
        except Exception as e:
            self.logger.error(f"Error registering default workflows: {str(e)}")
    
    def shutdown(self) -> None:
        """
        Shutdown the PostgreSQL service.
        
        This method closes the database connection and releases resources.
        """
        self.logger.info("Shutting down PostgreSQL service")
        
        if self.connection:
            try:
                self.connection.close()
                self.logger.debug("PostgreSQL database connection closed")
            except Exception as e:
                self.logger.error(f"Error closing PostgreSQL connection: {str(e)}")
        
        self.initialized = False
    
    def health_check(self) -> bool:
        """
        Check if the PostgreSQL service is healthy.
        
        Returns:
            bool: True if service is healthy, False otherwise
        """
        if not self.initialized or not self.connection:
            return False
        
        try:
            # Execute simple query to check connection
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            return result is not None and result["?column?"] == 1
        except Exception as e:
            self.logger.warning(f"PostgreSQL health check failed: {str(e)}")
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
            raise ServiceError("PostgreSQL service is not initialized")
        
        try:
            # Execute query
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            # Fetch results if query returns rows
            if self.cursor.description:
                results = [dict(row) for row in self.cursor.fetchall()]
                return results
            
            # For non-SELECT queries, return affected row count
            return [{"affected_rows": self.cursor.rowcount}]
        
        except Exception as e:
            self.logger.error(f"Error executing query: {str(e)}")
            raise ServiceError(f"Error executing query: {str(e)}")
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get the PostgreSQL database schema.
        
        Returns:
            Dict[str, Any]: Database schema information
            
        Raises:
            ServiceError: If schema extraction fails
        """
        if not self.initialized:
            raise ServiceError("PostgreSQL service is not initialized")
        
        try:
            schema = {"tables": {}}
            
            # Get tables in the schema
            self.cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """, (self.schema,))
            
            tables = [row["table_name"] for row in self.cursor.fetchall()]
            
            # Get columns for each table
            for table in tables:
                # Get column information
                self.cursor.execute("""
                    SELECT 
                        column_name, 
                        data_type, 
                        is_nullable, 
                        column_default
                    FROM information_schema.columns
                    WHERE table_schema = %s
                    AND table_name = %s
                    ORDER BY ordinal_position
                """, (self.schema, table))
                
                columns = []
                for row in self.cursor.fetchall():
                    columns.append({
                        "name": row["column_name"],
                        "type": row["data_type"],
                        "not_null": row["is_nullable"] == "NO",
                        "default": row["column_default"]
                    })
                
                # Get primary key information
                self.cursor.execute("""
                    SELECT a.attname
                    FROM pg_index i
                    JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                    WHERE i.indrelid = %s::regclass
                    AND i.indisprimary
                """, (f"{self.schema}.{table}",))
                
                pk_columns = [row["attname"] for row in self.cursor.fetchall()]
                
                # Mark primary key columns
                for column in columns:
                    column["primary_key"] = column["name"] in pk_columns
                
                # Get foreign key information
                self.cursor.execute("""
                    SELECT
                        a.attname as column_name,
                        cl2.relname as referenced_table,
                        a2.attname as referenced_column
                    FROM pg_constraint c
                    JOIN pg_namespace n ON n.oid = c.connamespace
                    JOIN pg_class cl ON cl.oid = c.conrelid
                    JOIN pg_class cl2 ON cl2.oid = c.confrelid
                    JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = c.conkey[1]
                    JOIN pg_attribute a2 ON a2.attrelid = c.confrelid AND a2.attnum = c.confkey[1]
                    WHERE c.contype = 'f'
                    AND n.nspname = %s
                    AND cl.relname = %s
                """, (self.schema, table))
                
                # Add foreign key info to columns
                fk_info = self.cursor.fetchall()
                for fk in fk_info:
                    for column in columns:
                        if column["name"] == fk["column_name"]:
                            column["referenced_table"] = fk["referenced_table"]
                            column["referenced_column"] = fk["referenced_column"]
                            break
                
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
            self.logger.info(f"Processing query: {query}")
            
            # Use default workflow if available
            workflow = self.get_workflow("postgresql_default")
            if workflow:
                # Create workflow context
                context = {
                    "query": query,
                    "service": "postgresql",
                    "connection": self.connection
                }
                
                # Add additional context from kwargs
                context.update(kwargs)
                
                # Execute workflow
                result = workflow.execute(context)
                return result
            
            # Fallback if no workflow is available
            self.logger.warning("No workflow available, returning error")
            return {
                "error": "No workflow available for processing queries",
                "query": query
            }
        
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
        metadata.update({
            "service_type": "postgresql",
            "database": self.database,
            "host": self.host,
            "port": self.port,
            "schema": self.schema,
            "features": [
                "query_execution",
                "schema_extraction",
                "natural_language_processing"
            ]
        })
        return metadata
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """
        Get a workflow by ID.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Optional[Workflow]: Workflow instance or None if not found
        """
        return self._workflows.get(workflow_id)
    
    def execute_workflow(self, workflow_id: str, input_data: Dict[str, Any],
                        start_stage: Optional[str] = None,
                        end_stage: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a workflow with the given input data.
        
        Args:
            workflow_id: Workflow identifier
            input_data: Input data for the workflow
            start_stage: Optional stage to start from
            end_stage: Optional stage to end at
            
        Returns:
            Dict[str, Any]: Workflow execution results
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ServiceError(f"Workflow not found: {workflow_id}")
        
        return workflow.execute(input_data) 
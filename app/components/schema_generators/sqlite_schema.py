"""
SQLite schema generator component.
"""

import logging
import sqlite3
from typing import Any, Dict, List, Optional

from app.components.base_component import BaseComponent
from app.core.exceptions import ComponentRegistryError
from app.utils.logging_setup import TICK_ICON, CROSS_ICON


class SQLiteSchemaGenerator(BaseComponent):
    """
    Schema generator component for SQLite databases.
    
    This component extracts schema information from a SQLite database,
    including tables, columns, types, and relationships.
    """
    
    def __init__(self, component_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the SQLite schema generator.
        
        Args:
            component_id: Unique identifier for the component
            config: Configuration parameters for the component
        """
        super().__init__(component_id, config)
        self.logger.debug(f"{TICK_ICON} Initializing SQLiteSchemaGenerator with id {component_id}")
        
        # Configuration options with defaults
        self.include_system_tables = self.get_config_value("include_system_tables", False)
        self.include_views = self.get_config_value("include_views", True)
        self.include_indexes = self.get_config_value("include_indexes", True)
        self.include_foreign_keys = self.get_config_value("include_foreign_keys", True)
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the component to generate database schema.
        
        Args:
            context: Execution context containing database connection info
            
        Returns:
            Dict[str, Any]: Updated context with the extracted schema
            
        Raises:
            ComponentRegistryError: If schema extraction fails
        """
        self.logger.debug(f"{TICK_ICON} Executing SQLiteSchemaGenerator for context keys: {list(context.keys())}")
        
        # Get database connection from context
        db_path = context.get("db_path")
        connection = context.get("connection")
        
        if not connection and not db_path:
            error_msg = f"{CROSS_ICON} Neither database connection nor path provided in context"
            self.logger.error(error_msg)
            return {"error": error_msg, "schema": {}}
        
        try:
            # Use existing connection or create a new one
            if connection:
                self.logger.debug("Using provided database connection")
                conn = connection
                should_close = False
            else:
                self.logger.debug(f"Creating new connection to {db_path}")
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                should_close = True
            
            # Create cursor
            cursor = conn.cursor()
            
            # Extract schema
            schema = self._extract_schema(cursor)
            
            # Close connection if we created it
            if should_close:
                conn.close()
            
            self.logger.info(f"{TICK_ICON} Extracted schema with {len(schema['tables'])} tables")
            
            # Return schema in context
            return {
                "schema": schema,
                "schema_generator": self.component_id
            }
        
        except Exception as e:
            error_msg = f"{CROSS_ICON} Error extracting SQLite schema: {str(e)}"
            self.logger.error(error_msg)
            raise ComponentRegistryError(error_msg)
    
    def _extract_schema(self, cursor) -> Dict[str, Any]:
        """
        Extract schema from SQLite database.
        
        Args:
            cursor: SQLite cursor
            
        Returns:
            Dict[str, Any]: Database schema
        """
        schema = {
            "tables": {},
            "views": {} if self.include_views else None,
            "indexes": {} if self.include_indexes else None
        }
        
        # Get all tables
        table_query = "SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view')"
        cursor.execute(table_query)
        
        for row in cursor.fetchall():
            name = row[0]
            object_type = row[1]
            
            # Skip sqlite_ system tables unless explicitly included
            if name.startswith('sqlite_') and not self.include_system_tables:
                continue
            
            if object_type == 'table':
                # Get table columns
                cursor.execute(f"PRAGMA table_info({name})")
                columns = []
                
                for col_row in cursor.fetchall():
                    columns.append({
                        "name": col_row[1],
                        "type": col_row[2],
                        "not_null": bool(col_row[3]),
                        "default_value": col_row[4],
                        "primary_key": bool(col_row[5])
                    })
                
                # Create table info
                table_info = {
                    "columns": columns,
                    "foreign_keys": []
                }
                
                # Add foreign keys if enabled
                if self.include_foreign_keys:
                    cursor.execute(f"PRAGMA foreign_key_list({name})")
                    for fk_row in cursor.fetchall():
                        table_info["foreign_keys"].append({
                            "id": fk_row[0],
                            "seq": fk_row[1],
                            "table": fk_row[2],
                            "from": fk_row[3],
                            "to": fk_row[4],
                            "on_update": fk_row[5],
                            "on_delete": fk_row[6],
                            "match": fk_row[7]
                        })
                
                # Add to schema
                schema["tables"][name] = table_info
            
            elif object_type == 'view' and self.include_views:
                # Get view definition
                cursor.execute(f"SELECT sql FROM sqlite_master WHERE name = '{name}'")
                definition = cursor.fetchone()[0]
                
                schema["views"][name] = {
                    "definition": definition
                }
        
        # Get indexes if enabled
        if self.include_indexes:
            cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type = 'index'")
            for idx_row in cursor.fetchall():
                idx_name = idx_row[0]
                tbl_name = idx_row[1]
                
                # Skip internal indexes
                if idx_name.startswith('sqlite_'):
                    continue
                
                # Get index info
                cursor.execute(f"PRAGMA index_info({idx_name})")
                index_columns = []
                
                for info_row in cursor.fetchall():
                    index_columns.append({
                        "seq": info_row[0],
                        "column": info_row[2]
                    })
                
                schema["indexes"][idx_name] = {
                    "table": tbl_name,
                    "columns": index_columns
                }
        
        return schema
    
    def validate_config(self) -> bool:
        """
        Validate the component configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        self.logger.debug("Validating config for SQLiteSchemaGenerator")
        # All configurations are optional with sensible defaults
        self.logger.info(f"{TICK_ICON} Config validated for SQLiteSchemaGenerator")
        return True 
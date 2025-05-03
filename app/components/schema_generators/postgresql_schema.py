"""
PostgreSQL schema generator component.
"""

import logging
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

from app.components.base_component import BaseComponent
from app.core.exceptions import ComponentRegistryError
from app.utils.logging_setup import TICK_ICON, CROSS_ICON


class PostgreSQLSchemaGenerator(BaseComponent):
    """
    PostgreSQL schema generator component.
    
    This component extracts schema information from a PostgreSQL database
    and formats it for use in prompts and other components.
    """
    
    def __init__(self, component_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the PostgreSQL schema generator.
        
        Args:
            component_id: Unique identifier for the component
            config: Configuration parameters for the component
        """
        super().__init__(component_id, config)
        self.logger.debug(f"{TICK_ICON} Initializing PostgreSQLSchemaGenerator with id {component_id}")
        
        # Configuration options with defaults
        self.schema = self.get_config_value("schema", "public")
        self.include_system_tables = self.get_config_value("include_system_tables", False)
        self.include_views = self.get_config_value("include_views", True)
        self.max_tables = self.get_config_value("max_tables", 50)
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the component to extract PostgreSQL schema.
        
        Args:
            context: Execution context containing database connection
            
        Returns:
            Dict[str, Any]: Updated context with schema information
            
        Raises:
            ComponentRegistryError: If schema extraction fails
        """
        self.logger.debug(f"{TICK_ICON} Executing PostgreSQLSchemaGenerator for context keys: {list(context.keys())}")
        
        # Get connection from context
        connection = context.get("connection")
        
        # Connection parameters from context if connection is not provided
        host = context.get("host", "localhost")
        port = context.get("port", 5432)
        database = context.get("database", "postgres")
        user = context.get("user", "postgres")
        password = context.get("password", "postgres")
        schema = context.get("schema", self.schema)
        
        # Create connection if not provided
        should_close = False
        if not connection:
            error_msg = f"{CROSS_ICON} No database connection provided in context"
            self.logger.error(error_msg)
            return {"error": error_msg, "schema": {}}
        
        try:
            # Create cursor with dictionary factory
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            
            # Initialize schema object
            schema_info = {
                "tables": {},
                "database_type": "postgresql",
                "schema": schema
            }
            
            # Get list of tables
            table_query = """
                SELECT table_name, table_type
                FROM information_schema.tables
                WHERE table_schema = %s
            """
            
            if not self.include_system_tables:
                table_query += " AND table_name NOT LIKE 'pg\\_%'"
            
            if not self.include_views:
                table_query += " AND table_type = 'BASE TABLE'"
            
            table_query += " ORDER BY table_name"
            
            cursor.execute(table_query, (schema,))
            tables = cursor.fetchall()
            
            # Limit to max_tables
            tables = tables[:self.max_tables]
            
            # Process each table
            for table_info in tables:
                table_name = table_info["table_name"]
                table_type = table_info["table_type"]
                
                self.logger.debug(f"Processing {table_type.lower()}: {table_name}")
                
                # Get column information
                cursor.execute("""
                    SELECT 
                        column_name, 
                        data_type, 
                        is_nullable, 
                        column_default,
                        character_maximum_length,
                        numeric_precision,
                        numeric_scale
                    FROM information_schema.columns
                    WHERE table_schema = %s
                    AND table_name = %s
                    ORDER BY ordinal_position
                """, (schema, table_name))
                
                columns = []
                for column in cursor.fetchall():
                    # Format the data type with precision/scale for numeric types
                    data_type = column["data_type"]
                    if data_type == "character varying" and column["character_maximum_length"]:
                        data_type = f"varchar({column['character_maximum_length']})"
                    elif data_type == "numeric" and column["numeric_precision"]:
                        if column["numeric_scale"]:
                            data_type = f"numeric({column['numeric_precision']},{column['numeric_scale']})"
                        else:
                            data_type = f"numeric({column['numeric_precision']})"
                    
                    columns.append({
                        "name": column["column_name"],
                        "type": data_type,
                        "nullable": column["is_nullable"] == "YES",
                        "default": column["column_default"]
                    })
                
                # Get primary key columns
                cursor.execute("""
                    SELECT a.attname
                    FROM pg_index i
                    JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                    WHERE i.indrelid = %s::regclass
                    AND i.indisprimary
                """, (f"{schema}.{table_name}",))
                
                pk_columns = [row["attname"] for row in cursor.fetchall()]
                
                # Mark primary key columns
                for column in columns:
                    column["primary_key"] = column["name"] in pk_columns
                
                # Get foreign key information
                cursor.execute("""
                    SELECT
                        kcu.column_name,
                        ccu.table_name AS referenced_table,
                        ccu.column_name AS referenced_column
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                      AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = %s
                    AND tc.table_name = %s
                """, (schema, table_name))
                
                # Add foreign key info to columns
                for fk in cursor.fetchall():
                    for column in columns:
                        if column["name"] == fk["column_name"]:
                            column["referenced_table"] = fk["referenced_table"]
                            column["referenced_column"] = fk["referenced_column"]
                            break
                
                # Get table description (comment) if available
                cursor.execute("""
                    SELECT obj_description(%s::regclass, 'pg_class') as comment
                """, (f"{schema}.{table_name}",))
                
                comment_row = cursor.fetchone()
                description = comment_row["comment"] if comment_row and comment_row["comment"] else ""
                
                # Add table to schema
                schema_info["tables"][table_name] = {
                    "columns": columns,
                    "type": "table" if table_type == "BASE TABLE" else "view",
                    "description": description
                }
            
            # Get table relationships
            for table_name in schema_info["tables"]:
                relationships = []
                
                # Find foreign keys in this table (outgoing relationships)
                for column in schema_info["tables"][table_name]["columns"]:
                    if "referenced_table" in column:
                        relationships.append({
                            "type": "belongs_to",
                            "table": column["referenced_table"],
                            "from_column": column["name"],
                            "to_column": column["referenced_column"]
                        })
                
                # Find tables that reference this table (incoming relationships)
                for other_table, other_info in schema_info["tables"].items():
                    if other_table == table_name:
                        continue
                    
                    for column in other_info["columns"]:
                        if "referenced_table" in column and column["referenced_table"] == table_name:
                            relationships.append({
                                "type": "has_many",
                                "table": other_table,
                                "from_column": column["referenced_column"],
                                "to_column": column["name"]
                            })
                
                # Add relationships to table info
                if relationships:
                    schema_info["tables"][table_name]["relationships"] = relationships
            
            # Close cursor
            cursor.close()
            
            # Close connection if we created it
            if should_close:
                connection.close()
            
            # Add schema to context
            self.logger.info(f"{TICK_ICON} Extracted schema with {len(schema_info['tables'])} tables")
            
            return {
                "schema": schema_info,
                "schema_generator": self.component_id
            }
        
        except Exception as e:
            error_msg = f"{CROSS_ICON} Error extracting PostgreSQL schema: {str(e)}"
            self.logger.error(error_msg)
            
            # Close connection if we created it
            if should_close and connection:
                connection.close()
            
            raise ComponentRegistryError(error_msg)
    
    def validate_config(self) -> bool:
        """
        Validate the component configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        self.logger.debug("Validating config for PostgreSQLSchemaGenerator")
        valid = True
        # Validate max_tables
        max_tables = self.get_config_value("max_tables", 50)
        if not isinstance(max_tables, int) or max_tables <= 0:
            self.logger.warning("max_tables must be a positive integer")
            valid = False
        
        if valid:
            self.logger.info(f"{TICK_ICON} Config validated for PostgreSQLSchemaGenerator")
        else:
            self.logger.error(f"{CROSS_ICON} Config validation failed for PostgreSQLSchemaGenerator")
        return valid 
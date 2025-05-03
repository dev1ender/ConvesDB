"""
Neo4j schema generator component.
"""

import logging
from typing import Any, Dict, List, Optional

from app.components.base_component import BaseComponent
from app.core.exceptions import ComponentRegistryError
from app.utils.logging_setup import TICK_ICON, CROSS_ICON


class Neo4jSchemaGenerator(BaseComponent):
    """
    Schema generator component for Neo4j graph databases.
    
    This component extracts schema information from a Neo4j database,
    including node labels, relationship types, properties, and constraints.
    """
    
    def __init__(self, component_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Neo4j schema generator.
        
        Args:
            component_id: Unique identifier for the component
            config: Configuration parameters for the component
        """
        super().__init__(component_id, config)
        self.logger.debug(f"{TICK_ICON} Initializing Neo4jSchemaGenerator with id {component_id}")
        
        # Configuration options with defaults
        self.include_constraints = self.get_config_value("include_constraints", True)
        self.include_indexes = self.get_config_value("include_indexes", True)
        self.include_statistics = self.get_config_value("include_statistics", False)
        self.include_procedures = self.get_config_value("include_procedures", False)
        self.include_functions = self.get_config_value("include_functions", False)
        self.sample_properties = self.get_config_value("sample_properties", True)
        self.sample_limit = self.get_config_value("sample_limit", 10)
    
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
        self.logger.debug(f"{TICK_ICON} Executing Neo4jSchemaGenerator for context keys: {list(context.keys())}")
        
        # Get database connection from context
        session = context.get("session")
        driver = context.get("driver")
        
        if not driver and not session:
            error_msg = f"{CROSS_ICON} No Neo4j driver or session provided in context"
            self.logger.error(error_msg)
            return {"error": error_msg, "schema": {}}
        
        try:
            # Use existing session or create a new one
            if session:
                self.logger.debug("Using provided Neo4j session")
                should_close = False
            else:
                self.logger.debug("Creating new Neo4j session from driver")
                session = driver.session()
                should_close = True
            
            # Extract schema
            schema = self._extract_schema(session)
            
            # Close session if we created it
            if should_close:
                session.close()
            
            self.logger.info(f"{TICK_ICON} Extracted Neo4j schema with {len(schema.get('node_labels', {}))} node labels and {len(schema.get('relationship_types', {}))} relationship types")
            
            # Return schema in context
            return {
                "schema": schema,
                "schema_generator": self.component_id
            }
        
        except Exception as e:
            error_msg = f"{CROSS_ICON} Error extracting Neo4j schema: {str(e)}"
            self.logger.error(error_msg)
            raise ComponentRegistryError(error_msg)
    
    def _extract_schema(self, session) -> Dict[str, Any]:
        """
        Extract schema from Neo4j database.
        
        Args:
            session: Neo4j session
            
        Returns:
            Dict[str, Any]: Database schema
        """
        schema = {
            "node_labels": {},
            "relationship_types": {},
            "constraints": {} if self.include_constraints else None,
            "indexes": {} if self.include_indexes else None,
            "statistics": {} if self.include_statistics else None,
            "procedures": {} if self.include_procedures else None,
            "functions": {} if self.include_functions else None
        }
        
        # Extract node labels
        self._extract_node_labels(session, schema)
        
        # Extract relationship types
        self._extract_relationship_types(session, schema)
        
        # Extract constraints if enabled
        if self.include_constraints:
            self._extract_constraints(session, schema)
        
        # Extract indexes if enabled
        if self.include_indexes:
            self._extract_indexes(session, schema)
        
        # Extract statistics if enabled
        if self.include_statistics:
            self._extract_statistics(session, schema)
        
        # Extract procedures if enabled
        if self.include_procedures:
            self._extract_procedures(session, schema)
        
        # Extract functions if enabled
        if self.include_functions:
            self._extract_functions(session, schema)
        
        return schema
    
    def _extract_node_labels(self, session, schema: Dict[str, Any]) -> None:
        """
        Extract node labels and their properties.
        
        Args:
            session: Neo4j session
            schema: Schema dictionary to update
        """
        # Get all node labels
        label_query = "CALL db.labels()"
        result = session.run(label_query)
        
        node_labels = [record["label"] for record in result]
        
        # Get properties for each label
        for label in node_labels:
            # Sample properties to determine data types
            if self.sample_properties:
                sample_query = f"""
                    MATCH (n:{label})
                    RETURN n LIMIT {self.sample_limit}
                """
                
                result = session.run(sample_query)
                properties = {}
                property_types = {}
                sample_count = 0
                
                # Process each node
                for record in result:
                    node = record["n"]
                    sample_count += 1
                    
                    # Process each property
                    for key, value in node.items():
                        # Track property occurrence
                        properties[key] = properties.get(key, 0) + 1
                        
                        # Infer property type
                        python_type = type(value).__name__
                        neo4j_type = self._map_type_to_neo4j(python_type)
                        
                        if key not in property_types:
                            property_types[key] = {neo4j_type: 1}
                        else:
                            property_types[key][neo4j_type] = property_types[key].get(neo4j_type, 0) + 1
                
                # Determine most common type for each property
                property_info = {}
                for prop, counts in property_types.items():
                    # Sort by count, descending
                    sorted_types = sorted(counts.items(), key=lambda x: x[1], reverse=True)
                    most_common_type = sorted_types[0][0] if sorted_types else "unknown"
                    frequency = properties[prop] / max(1, sample_count)
                    
                    property_info[prop] = {
                        "type": most_common_type,
                        "occurrence": properties[prop],
                        "frequency": frequency
                    }
                
                # Get total count of nodes with this label
                count_query = f"MATCH (:{label}) RETURN count(*) AS count"
                count_result = session.run(count_query)
                total_count = count_result.single()["count"]
                
                schema["node_labels"][label] = {
                    "properties": property_info,
                    "count": total_count,
                    "sample_size": sample_count
                }
            else:
                # Just get the count without sampling
                count_query = f"MATCH (:{label}) RETURN count(*) AS count"
                count_result = session.run(count_query)
                total_count = count_result.single()["count"]
                
                schema["node_labels"][label] = {
                    "properties": {},
                    "count": total_count
                }
    
    def _extract_relationship_types(self, session, schema: Dict[str, Any]) -> None:
        """
        Extract relationship types and their properties.
        
        Args:
            session: Neo4j session
            schema: Schema dictionary to update
        """
        # Get all relationship types
        rel_query = "CALL db.relationshipTypes()"
        result = session.run(rel_query)
        
        rel_types = [record["relationshipType"] for record in result]
        
        # Get properties and connection details for each type
        for rel_type in rel_types:
            # Get connection patterns (from-to labels)
            pattern_query = f"""
                MATCH (from)-[r:{rel_type}]->(to)
                RETURN DISTINCT labels(from) AS from_labels, labels(to) AS to_labels
                LIMIT 100
            """
            
            pattern_result = session.run(pattern_query)
            patterns = []
            
            for record in pattern_result:
                from_labels = record["from_labels"]
                to_labels = record["to_labels"]
                
                patterns.append({
                    "from_labels": from_labels,
                    "to_labels": to_labels
                })
            
            # Sample properties to determine data types
            if self.sample_properties:
                sample_query = f"""
                    MATCH ()-[r:{rel_type}]->()
                    RETURN r LIMIT {self.sample_limit}
                """
                
                result = session.run(sample_query)
                properties = {}
                property_types = {}
                sample_count = 0
                
                # Process each relationship
                for record in result:
                    rel = record["r"]
                    sample_count += 1
                    
                    # Process each property
                    for key, value in rel.items():
                        # Track property occurrence
                        properties[key] = properties.get(key, 0) + 1
                        
                        # Infer property type
                        python_type = type(value).__name__
                        neo4j_type = self._map_type_to_neo4j(python_type)
                        
                        if key not in property_types:
                            property_types[key] = {neo4j_type: 1}
                        else:
                            property_types[key][neo4j_type] = property_types[key].get(neo4j_type, 0) + 1
                
                # Determine most common type for each property
                property_info = {}
                for prop, counts in property_types.items():
                    # Sort by count, descending
                    sorted_types = sorted(counts.items(), key=lambda x: x[1], reverse=True)
                    most_common_type = sorted_types[0][0] if sorted_types else "unknown"
                    frequency = properties[prop] / max(1, sample_count)
                    
                    property_info[prop] = {
                        "type": most_common_type,
                        "occurrence": properties[prop],
                        "frequency": frequency
                    }
                
                # Get total count of relationships with this type
                count_query = f"MATCH ()-[:{rel_type}]->() RETURN count(*) AS count"
                count_result = session.run(count_query)
                total_count = count_result.single()["count"]
                
                schema["relationship_types"][rel_type] = {
                    "properties": property_info,
                    "patterns": patterns,
                    "count": total_count,
                    "sample_size": sample_count
                }
            else:
                # Just get the count and patterns without sampling properties
                count_query = f"MATCH ()-[:{rel_type}]->() RETURN count(*) AS count"
                count_result = session.run(count_query)
                total_count = count_result.single()["count"]
                
                schema["relationship_types"][rel_type] = {
                    "properties": {},
                    "patterns": patterns,
                    "count": total_count
                }
    
    def _extract_constraints(self, session, schema: Dict[str, Any]) -> None:
        """
        Extract database constraints.
        
        Args:
            session: Neo4j session
            schema: Schema dictionary to update
        """
        # The query is different depending on Neo4j version
        try:
            # Neo4j 4.x+
            constraints_query = "SHOW CONSTRAINTS"
            result = session.run(constraints_query)
            
            for record in result:
                constraint_id = record.get("id") or record.get("name", f"constraint_{len(schema['constraints'])}")
                
                constraint_info = {
                    "name": record.get("name"),
                    "type": record.get("type"),
                    "entity_type": record.get("entityType"),
                    "labelsOrTypes": record.get("labelsOrTypes", []),
                    "properties": record.get("properties", []),
                    "description": record.get("description", "")
                }
                
                schema["constraints"][str(constraint_id)] = constraint_info
        
        except Exception as e:
            self.logger.warning(f"Error getting constraints with SHOW CONSTRAINTS: {str(e)}")
            
            try:
                # Neo4j 3.x
                constraints_query = "CALL db.constraints()"
                result = session.run(constraints_query)
                
                for i, record in enumerate(result):
                    constraint_id = f"constraint_{i}"
                    description = record.get("description")
                    
                    constraint_info = {
                        "description": description
                    }
                    
                    schema["constraints"][constraint_id] = constraint_info
            
            except Exception as e2:
                self.logger.error(f"Error getting constraints with db.constraints(): {str(e2)}")
                schema["constraints"] = {"error": "Failed to retrieve constraints"}
    
    def _extract_indexes(self, session, schema: Dict[str, Any]) -> None:
        """
        Extract database indexes.
        
        Args:
            session: Neo4j session
            schema: Schema dictionary to update
        """
        # The query is different depending on Neo4j version
        try:
            # Neo4j 4.x+
            indexes_query = "SHOW INDEXES"
            result = session.run(indexes_query)
            
            for record in result:
                index_id = record.get("id") or record.get("name", f"index_{len(schema['indexes'])}")
                
                index_info = {
                    "name": record.get("name"),
                    "type": record.get("type"),
                    "entity_type": record.get("entityType"),
                    "labelsOrTypes": record.get("labelsOrTypes", []),
                    "properties": record.get("properties", []),
                    "state": record.get("state", ""),
                    "uniqueness": record.get("uniqueness", ""),
                    "provider": record.get("provider", "")
                }
                
                schema["indexes"][str(index_id)] = index_info
        
        except Exception as e:
            self.logger.warning(f"Error getting indexes with SHOW INDEXES: {str(e)}")
            
            try:
                # Neo4j 3.x
                indexes_query = "CALL db.indexes()"
                result = session.run(indexes_query)
                
                for i, record in enumerate(result):
                    index_id = f"index_{i}"
                    description = record.get("description")
                    
                    index_info = {
                        "description": description
                    }
                    
                    schema["indexes"][index_id] = index_info
            
            except Exception as e2:
                self.logger.error(f"Error getting indexes with db.indexes(): {str(e2)}")
                schema["indexes"] = {"error": "Failed to retrieve indexes"}
    
    def _extract_statistics(self, session, schema: Dict[str, Any]) -> None:
        """
        Extract database statistics.
        
        Args:
            session: Neo4j session
            schema: Schema dictionary to update
        """
        try:
            # Get store sizes
            store_query = "CALL dbms.queryJmx('org.neo4j:instance=kernel#0,name=Store sizes') YIELD attributes"
            store_result = session.run(store_query)
            
            store_sizes = {}
            record = store_result.single()
            
            if record and "attributes" in record:
                attrs = record["attributes"]
                
                for key, value in attrs.items():
                    if "value" in value:
                        store_sizes[key] = value["value"]
            
            # Get database-level metrics
            query = """
                CALL apoc.meta.stats() YIELD labels, relTypes, relTypeCount, 
                     nodeCount, relCount, propertyKeyCount
                RETURN labels, relTypes, relTypeCount, nodeCount, relCount, propertyKeyCount
            """
            
            try:
                meta_result = session.run(query)
                meta_record = meta_result.single()
                
                if meta_record:
                    schema["statistics"] = {
                        "node_count": meta_record["nodeCount"],
                        "relationship_count": meta_record["relCount"],
                        "property_key_count": meta_record["propertyKeyCount"],
                        "label_counts": meta_record["labels"],
                        "relationship_type_counts": meta_record["relTypeCount"],
                        "store_sizes": store_sizes
                    }
                else:
                    # Fallback if APOC is not available
                    schema["statistics"] = {
                        "store_sizes": store_sizes
                    }
            
            except Exception as e:
                self.logger.warning(f"Error getting APOC stats: {str(e)}")
                
                # Fallback - get basic counts
                count_query = "MATCH (n) RETURN count(n) as nodeCount"
                rel_query = "MATCH ()-->() RETURN count(*) as relCount"
                
                node_count = session.run(count_query).single()["nodeCount"]
                rel_count = session.run(rel_query).single()["relCount"]
                
                schema["statistics"] = {
                    "node_count": node_count,
                    "relationship_count": rel_count,
                    "store_sizes": store_sizes
                }
        
        except Exception as e:
            self.logger.error(f"Error getting database statistics: {str(e)}")
            schema["statistics"] = {"error": "Failed to retrieve statistics"}
    
    def _extract_procedures(self, session, schema: Dict[str, Any]) -> None:
        """
        Extract available procedures.
        
        Args:
            session: Neo4j session
            schema: Schema dictionary to update
        """
        try:
            query = "CALL dbms.procedures()"
            result = session.run(query)
            
            procedures = {}
            
            for record in result:
                name = record["name"]
                signature = record.get("signature", "")
                description = record.get("description", "")
                
                procedures[name] = {
                    "signature": signature,
                    "description": description
                }
            
            schema["procedures"] = procedures
        
        except Exception as e:
            self.logger.error(f"Error getting procedures: {str(e)}")
            schema["procedures"] = {"error": "Failed to retrieve procedures"}
    
    def _extract_functions(self, session, schema: Dict[str, Any]) -> None:
        """
        Extract available functions.
        
        Args:
            session: Neo4j session
            schema: Schema dictionary to update
        """
        try:
            query = "CALL dbms.functions()"
            result = session.run(query)
            
            functions = {}
            
            for record in result:
                name = record["name"]
                signature = record.get("signature", "")
                description = record.get("description", "")
                
                functions[name] = {
                    "signature": signature,
                    "description": description
                }
            
            schema["functions"] = functions
        
        except Exception as e:
            self.logger.error(f"Error getting functions: {str(e)}")
            schema["functions"] = {"error": "Failed to retrieve functions"}
    
    def _map_type_to_neo4j(self, python_type: str) -> str:
        """
        Map Python type to Neo4j type.
        
        Args:
            python_type: Python type name
            
        Returns:
            str: Neo4j type name
        """
        type_mapping = {
            "str": "STRING",
            "int": "INTEGER",
            "float": "FLOAT",
            "bool": "BOOLEAN",
            "list": "LIST",
            "dict": "MAP",
            "NoneType": "NULL"
        }
        
        return type_mapping.get(python_type, "UNKNOWN")
    
    def validate_config(self) -> bool:
        """
        Validate the component configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        self.logger.debug("Validating config for Neo4jSchemaGenerator")
        valid = True
        # Validate schema options
        # Sample limit validation
        sample_limit = self.get_config_value("sample_limit", 10)
        if not isinstance(sample_limit, int) or sample_limit <= 0:
            self.logger.warning("sample_limit must be a positive integer")
            valid = False
        
        if valid:
            self.logger.info(f"{TICK_ICON} Config validated for Neo4jSchemaGenerator")
        else:
            self.logger.error(f"{CROSS_ICON} Config validation failed for Neo4jSchemaGenerator")
        return valid 
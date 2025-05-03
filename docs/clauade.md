# extensions/database_connectors.py
"""
Database connector extensions for the NLP to SQL system
"""

from typing import Dict, List, Any, Optional
from modules.database import DatabaseInterface
import neo4j
import json


class Neo4jConnector(DatabaseInterface):
    """Neo4j database connector implementation"""
    
    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j"):
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self.driver = None
        self.connect()
    
    def connect(self):
        """Connect to Neo4j database"""
        try:
            self.driver = neo4j.GraphDatabase.driver(
                self.uri, 
                auth=(self.user, self.password)
            )
            return True
        except Exception as e:
            print(f"Error connecting to Neo4j database: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from Neo4j database"""
        if self.driver:
            self.driver.close()
            self.driver = None
            return True
        return False
    
    def execute_query(self, query: str) -> Dict[str, Any]:
        """Execute a Cypher query against the Neo4j database"""
        if not self.driver:
            return {"success": False, "error": "Not connected to database"}
            
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query)
                records = [record.data() for record in result]
                
                return {"success": True, "results": records}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def execute_script(self, script: str) -> Dict[str, Any]:
        """Execute a Cypher script against the Neo4j database"""
        if not self.driver:
            return {"success": False, "error": "Not connected to database"}
            
        try:
            # Split script by semicolons to execute multiple statements
            statements = [s.strip() for s in script.split(';') if s.strip()]
            
            with self.driver.session(database=self.database) as session:
                for statement in statements:
                    session.run(statement)
                
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_tables(self) -> List[str]:
        """Get list of node labels in the Neo4j database"""
        if not self.driver:
            return []
            
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run("CALL db.labels()")
                return [record["label"] for record in result]
        except Exception:
            return []
    
    def get_table_schema(self, label: str) -> Dict[str, Any]:
        """Get schema for a specific node label in Neo4j"""
        if not self.driver:
            return {}
            
        try:
            # Get property keys for this label
            with self.driver.session(database=self.database) as session:
                # Get properties for this label
                property_query = f"""
                MATCH (n:{label})
                WITH n LIMIT 1
                RETURN keys(n) AS properties
                """
                properties_result = session.run(property_query)
                property_keys = properties_result.single()["properties"] if properties_result.peek() else []
                
                # Get relationships for this label
                relationship_query = f"""
                MATCH (n:{label})-[r]->(m)
                RETURN type(r) AS relationship_type, 
                       labels(m) AS target_labels,
                       count(r) AS count
                """
                relationships_result = session.run(relationship_query)
                relationships = []
                
                for record in relationships_result:
                    rel_info = {
                        "type": record["relationship_type"],
                        "target_labels": record["target_labels"],
                        "count": record["count"]
                    }
                    relationships.append(rel_info)
                
                # Get sample data
                sample_query = f"""
                MATCH (n:{label})
                RETURN n LIMIT 3
                """
                sample_result = session.run(sample_query)
                sample_data = [dict(record["n"].items()) for record in sample_result]
                
                return {
                    "name": label,
                    "properties": property_keys,
                    "relationships": relationships,
                    "sample_data": sample_data
                }
                
        except Exception as e:
            print(f"Error getting schema for label {label}: {e}")
            return {}


# extensions/llm_providers.py
"""
LLM provider extensions for the NLP to SQL system
"""

from typing import Dict, List, Any, Optional
from modules.llm import LLMInterface
import requests
import json


class OpenAILLM(LLMInterface):
    """OpenAI LLM provider implementation"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model
        self.api_base = "https://api.openai.com/v1"
    
    def
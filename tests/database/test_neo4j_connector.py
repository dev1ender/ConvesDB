"""
Tests for Neo4j database connector.
"""
import os
import pytest
from unittest.mock import patch, MagicMock

from app.database.neo4j_connector import Neo4jConnector

# Test configuration
TEST_CONFIG = {
    "uri": "bolt://localhost:7687",
    "username": "neo4j",
    "password": "password",
    "database": "neo4j"
}

class TestNeo4jConnector:
    """Test suite for Neo4jConnector class."""
    
    @pytest.fixture
    def mock_driver(self):
        """Create a mock Neo4j driver."""
        with patch('neo4j.GraphDatabase') as mock_graph_db:
            # Create mock driver, session, and transaction
            mock_session = MagicMock()
            mock_driver = MagicMock()
            mock_driver.session.return_value = mock_session
            
            # Configure GraphDatabase.driver to return our mock driver
            mock_graph_db.driver.return_value = mock_driver
            
            yield mock_driver
    
    def test_init(self):
        """Test connector initialization."""
        connector = Neo4jConnector(TEST_CONFIG)
        
        assert connector.uri == TEST_CONFIG["uri"]
        assert connector.username == TEST_CONFIG["username"]
        assert connector.password == TEST_CONFIG["password"]
        assert connector.database == TEST_CONFIG["database"]
        assert connector.driver is None
    
    def test_connect(self, mock_driver):
        """Test connection to Neo4j."""
        connector = Neo4jConnector(TEST_CONFIG)
        connector.connect()
        
        # Verify GraphDatabase.driver was called with correct arguments
        from neo4j import GraphDatabase
        GraphDatabase.driver.assert_called_once_with(
            TEST_CONFIG["uri"],
            auth=(TEST_CONFIG["username"], TEST_CONFIG["password"])
        )
        
        # Verify a session was created with the correct database
        mock_driver.session.assert_called_with(database=TEST_CONFIG["database"])
        
        # Verify the session's run method was called with a test query
        mock_session = mock_driver.session.return_value.__enter__.return_value
        mock_session.run.assert_called_with("RETURN 1")
    
    def test_get_table_names(self, mock_driver):
        """Test retrieving node labels."""
        # Set up mock to return some labels
        mock_record1 = MagicMock()
        mock_record1["label"] = "Person"
        mock_record2 = MagicMock()
        mock_record2["label"] = "Movie"
        
        mock_result = MagicMock()
        mock_result.__iter__.return_value = [mock_record1, mock_record2]
        
        mock_session = mock_driver.session.return_value.__enter__.return_value
        mock_session.run.return_value = mock_result
        
        # Test the method
        connector = Neo4jConnector(TEST_CONFIG)
        connector.driver = mock_driver  # Set the driver directly
        
        labels = connector.get_table_names()
        
        # Verify the right query was executed
        mock_session.run.assert_called_with("CALL db.labels()")
        
        # Verify results
        assert labels == ["Person", "Movie"]
    
    def test_get_table_schema(self, mock_driver):
        """Test retrieving schema for a node label."""
        # Set up mock for first query (get properties)
        mock_properties_record = MagicMock()
        mock_properties_record["properties"] = ["name", "age"]
        
        mock_properties_result = MagicMock()
        mock_properties_result.single.return_value = mock_properties_record
        
        # Set up mock for second query (get property type)
        mock_type_record = MagicMock()
        mock_type_record["property_type"] = "STRING"
        
        mock_type_result = MagicMock()
        mock_type_result.single.return_value = mock_type_record
        
        # Configure session mock to return different results based on query
        mock_session = mock_driver.session.return_value.__enter__.return_value
        mock_session.run.side_effect = [mock_properties_result, mock_type_result, mock_type_result]
        
        # Test the method
        connector = Neo4jConnector(TEST_CONFIG)
        connector.driver = mock_driver  # Set the driver directly
        
        schema = connector.get_table_schema("Person")
        
        # Verify the right queries were executed
        assert mock_session.run.call_count == 3
        
        # Verify results
        assert len(schema) == 2
        assert schema[0]["column_name"] == "name"
        assert schema[0]["data_type"] == "STRING"
        assert schema[1]["column_name"] == "age"
        assert schema[1]["data_type"] == "STRING"
    
    def test_run(self, mock_driver):
        """Test running a Cypher query."""
        # Set up mock records
        mock_record1 = {"name": "Alice", "age": 30}
        mock_record2 = {"name": "Bob", "age": 25}
        
        mock_result = MagicMock()
        mock_result.__iter__.return_value = [mock_record1, mock_record2]
        
        mock_session = mock_driver.session.return_value.__enter__.return_value
        mock_session.run.return_value = mock_result
        
        # Test the method
        connector = Neo4jConnector(TEST_CONFIG)
        connector.driver = mock_driver  # Set the driver directly
        
        query = "MATCH (p:Person) RETURN p.name AS name, p.age AS age"
        results = connector.run(query)
        
        # Verify the right query was executed
        mock_session.run.assert_called_with(query)
        
        # Verify results
        assert len(results) == 2
        assert results[0]["name"] == "Alice"
        assert results[0]["age"] == 30
        assert results[1]["name"] == "Bob"
        assert results[1]["age"] == 25
    
    def test_close(self, mock_driver):
        """Test closing the connection."""
        connector = Neo4jConnector(TEST_CONFIG)
        connector.driver = mock_driver  # Set the driver directly
        
        connector.close()
        
        # Verify driver was closed
        mock_driver.close.assert_called_once()
        assert connector.driver is None
    
    def test_is_connected(self, mock_driver):
        """Test checking connection status."""
        connector = Neo4jConnector(TEST_CONFIG)
        
        # Test when driver is None
        assert not connector.is_connected()
        
        # Test when driver exists and connection works
        connector.driver = mock_driver
        mock_session = mock_driver.session.return_value.__enter__.return_value
        
        assert connector.is_connected()
        mock_session.run.assert_called_with("RETURN 1")
        
        # Test when driver exists but connection fails
        mock_session.run.side_effect = Exception("Connection error")
        assert not connector.is_connected()
    
    def test_get_relationship_schema(self, mock_driver):
        """Test retrieving relationship schema."""
        # Mock for get_view_names
        mock_rel_record1 = MagicMock()
        mock_rel_record1["relationshipType"] = "ACTED_IN"
        
        mock_rel_result = MagicMock()
        mock_rel_result.__iter__.return_value = [mock_rel_record1]
        
        # Mock for relationship schema query
        mock_schema_record = MagicMock()
        mock_schema_record["source_labels"] = ["Person"]
        mock_schema_record["target_labels"] = ["Movie"]
        
        mock_schema_result = MagicMock()
        mock_schema_result.single.return_value = mock_schema_record
        
        # Configure session mock
        mock_session = mock_driver.session.return_value.__enter__.return_value
        mock_session.run.side_effect = [mock_rel_result, mock_schema_result]
        
        # Test the method
        connector = Neo4jConnector(TEST_CONFIG)
        connector.driver = mock_driver  # Set the driver directly
        
        # Mock get_view_names
        with patch.object(connector, 'get_view_names', return_value=["ACTED_IN"]):
            schema = connector.get_relationship_schema()
        
        # Verify results
        assert len(schema) == 1
        assert schema[0]["relationship_type"] == "ACTED_IN"
        assert schema[0]["source_labels"] == ["Person"]
        assert schema[0]["target_labels"] == ["Movie"]

# For integration testing with a real Neo4j instance (disabled by default)
@pytest.mark.skip(reason="Requires a running Neo4j instance")
class TestNeo4jConnectorIntegration:
    """Integration tests for Neo4jConnector with a real Neo4j instance."""
    
    @pytest.fixture
    def connector(self):
        """Create and yield a Neo4j connector for testing."""
        # Use environment variables for connection information if available
        uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        username = os.environ.get("NEO4J_USERNAME", "neo4j")
        password = os.environ.get("NEO4J_PASSWORD", "password")
        database = os.environ.get("NEO4J_DATABASE", "neo4j")
        
        config = {
            "uri": uri,
            "username": username,
            "password": password,
            "database": database
        }
        
        connector = Neo4jConnector(config)
        connector.connect()
        
        # Create test data
        connector.run("CREATE (p:Person {name: 'Alice', age: 30})")
        connector.run("CREATE (p:Person {name: 'Bob', age: 25})")
        connector.run("CREATE (m:Movie {title: 'The Matrix', year: 1999})")
        connector.run("MATCH (p:Person {name: 'Alice'}), (m:Movie {title: 'The Matrix'}) CREATE (p)-[:ACTED_IN]->(m)")
        
        yield connector
        
        # Clean up test data
        connector.run("MATCH (n) DETACH DELETE n")
        connector.close()
    
    def test_get_table_names_integration(self, connector):
        """Test retrieving node labels from a real Neo4j instance."""
        labels = connector.get_table_names()
        assert "Person" in labels
        assert "Movie" in labels
    
    def test_get_table_schema_integration(self, connector):
        """Test retrieving schema for a node label from a real Neo4j instance."""
        schema = connector.get_table_schema("Person")
        
        # Find the name and age properties
        name_prop = next((prop for prop in schema if prop["column_name"] == "name"), None)
        age_prop = next((prop for prop in schema if prop["column_name"] == "age"), None)
        
        assert name_prop is not None
        assert age_prop is not None
        assert name_prop["data_type"] in ["STRING", "String"]
        assert age_prop["data_type"] in ["INTEGER", "Long", "Int"]
    
    def test_run_integration(self, connector):
        """Test running a Cypher query on a real Neo4j instance."""
        results = connector.run("MATCH (p:Person) RETURN p.name AS name, p.age AS age ORDER BY p.name")
        
        assert len(results) == 2
        assert results[0]["name"] == "Alice"
        assert results[0]["age"] == 30
        assert results[1]["name"] == "Bob"
        assert results[1]["age"] == 25
    
    def test_get_relationship_schema_integration(self, connector):
        """Test retrieving relationship schema from a real Neo4j instance."""
        schema = connector.get_relationship_schema()
        
        # Find the ACTED_IN relationship
        acted_in = next((rel for rel in schema if rel["relationship_type"] == "ACTED_IN"), None)
        
        assert acted_in is not None
        assert "Person" in acted_in["source_labels"]
        assert "Movie" in acted_in["target_labels"] 
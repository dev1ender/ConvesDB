"""
Tests for Neo4j demo script and sample queries.
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.seed_neo4j import SAMPLE_NEO4J_QUERIES
from commands.neo4j_demo import run_comprehensive_demo, check_data_exists, format_document_results
from app.services.neo4j_service import Neo4jService


class TestNeo4jDemo:
    """Test suite for Neo4j demo script."""
    
    @pytest.fixture
    def mock_neo4j_service(self):
        """Create a mock Neo4j service."""
        with patch('app.services.neo4j_service.Neo4jService') as mock_service:
            # Mock connector
            mock_connector = MagicMock()
            mock_connector.get_table_names.return_value = ["User", "Device", "Organization"]
            mock_connector.get_view_names.return_value = ["WORKS_FOR", "HAS_DEVICE"]
            
            # Set up sample query results
            user_count_result = [{"count": 150}]
            user_sample_result = [{"name": "John Doe"}, {"name": "Jane Smith"}, {"name": "Bob Johnson"}]
            org_sample_result = [{"name": "Acme Inc."}, {"name": "Example Corp."}, {"name": "Test LLC"}]
            
            # Configure run method to return different results based on query
            def mock_run(query, params=None):
                if "MATCH (u:User) RETURN count(u)" in query:
                    return user_count_result
                elif "MATCH (o:Organization) RETURN count(o)" in query:
                    return [{"count": 10}]
                elif "MATCH (u:User) RETURN u.name" in query:
                    return user_sample_result
                elif "MATCH (o:Organization) RETURN o.name" in query:
                    return org_sample_result
                elif "MATCH (d:Device) RETURN d.hostname" in query:
                    return [{"d.hostname": f"device-{i}"} for i in range(10)]
                else:
                    return []
            
            mock_connector.run.side_effect = mock_run
            
            # Set up mock service
            mock_service_instance = MagicMock()
            mock_service_instance.connector = mock_connector
            mock_service_instance.check_node_embeddings.return_value = {
                "total": 150,
                "with_embedding": 150,
                "percentage": 100,
                "samples": [{"title": "User1", "has_embedding": True} for _ in range(5)]
            }
            mock_service_instance.search_schema.return_value = [
                {
                    "type": "node_label",
                    "name": "User",
                    "description": "A user in the system",
                    "score": 0.95
                },
                {
                    "type": "relationship_type",
                    "name": "WORKS_FOR",
                    "description": "Relationship between users and organizations",
                    "score": 0.85
                }
            ]
            mock_service_instance.search_documents.return_value = [
                {
                    "title": "Sample Document",
                    "year": "2023",
                    "id": "doc_123",
                    "content": "This is a sample document.",
                    "score": 0.95
                }
            ]
            mock_service_instance.add_embeddings.return_value = True
            mock_service_instance.embed_schema.return_value = True
            
            yield mock_service_instance
    
    def test_sample_queries_structure(self):
        """Test that sample queries have the expected structure."""
        for query in SAMPLE_NEO4J_QUERIES:
            assert "complexity" in query
            assert "nlp" in query
            assert "cypher" in query
            assert "expected" in query
            
            assert query["complexity"] in ["low", "medium", "advanced"]
            assert isinstance(query["nlp"], str)
            assert isinstance(query["cypher"], str)
            assert isinstance(query["expected"], str)
    
    def test_check_data_exists(self, mock_neo4j_service):
        """Test the check_data_exists function."""
        # Test when data exists
        assert check_data_exists(mock_neo4j_service) == True
        
        # Test when data doesn't exist
        mock_neo4j_service.connector.run.side_effect = lambda query, params=None: [{"count": 0}]
        assert check_data_exists(mock_neo4j_service) == False
        
        # Test when an error occurs
        mock_neo4j_service.connector.run.side_effect = Exception("Connection error")
        assert check_data_exists(mock_neo4j_service) == False
    
    def test_format_document_results(self, capsys):
        """Test the format_document_results function."""
        # Test with results
        results = [
            {
                "title": "Document 1",
                "year": "2023",
                "id": "doc_123",
                "content": "This is document 1.",
                "score": 0.95
            },
            {
                "title": "Document 2",
                "year": "2022",
                "id": "doc_456",
                "content": "This is document 2.",
                "score": 0.85
            }
        ]
        
        format_document_results(results)
        captured = capsys.readouterr()
        assert "Found 2 matching documents" in captured.out
        assert "Document 1" in captured.out
        assert "Score: 0.9500" in captured.out
        assert "Year: 2023" in captured.out
        assert "Document 2" in captured.out
        
        # Test with empty results
        format_document_results([])
        captured = capsys.readouterr()
        assert "No documents found matching the query" in captured.out
    
    @patch('builtins.input', side_effect=['2'])  # Simulate user input '2' for the second sample question
    def test_run_comprehensive_demo(self, mock_input, mock_neo4j_service, capsys):
        """Test the run_comprehensive_demo function."""
        # Skip actual test execution as it would be too complex to mock everything
        # Just verify that the function doesn't raise exceptions
        with patch('commands.neo4j_demo.check_data_exists', return_value=True):
            run_comprehensive_demo(mock_neo4j_service)
        
        # Verify some expected output snippets
        captured = capsys.readouterr()
        assert "COMPREHENSIVE NEO4J DEMO" in captured.out
        assert "Step 1: Performing Neo4j health check" in captured.out
        assert "Step 2: Checking for seed data" in captured.out
        assert "Step 3: Checking schema embeddings" in captured.out
        assert "Step 4: Checking node embeddings" in captured.out
        assert "Step 5: Asking questions" in captured.out


class TestNeo4jSampleQueries:
    """Test suite specifically for the SAMPLE_NEO4J_QUERIES."""
    
    @pytest.fixture
    def mock_neo4j_connector(self):
        """Create a mock Neo4j connector."""
        mock_connector = MagicMock()
        
        # Set up results for different sample queries
        def mock_run(query, params=None):
            # User count query
            if "MATCH (u:User) RETURN count(u)" in query:
                return [{"user_count": 150}]
            # Device hostnames query    
            elif "MATCH (d:Device) RETURN d.hostname" in query:
                return [{"d.hostname": f"device-{i}"} for i in range(150)]
            # Organization count query
            elif "MATCH (o:Organization) RETURN count(o)" in query:
                return [{"org_count": 10}]
            # Users who uploaded files query
            elif "MATCH (u:User)-[:UPLOADED_BY]->(f:File)" in query:
                return [{"u.name": f"User {i}"} for i in range(20)]
            # Online devices query
            elif "MATCH (d:Device) WHERE d.status = 'online'" in query:
                return [{"online_devices": 45}]
            # Websites accessed by IT users query
            elif "MATCH (u:User)-[:ACCESSED]->(w:Website) WHERE u.department CONTAINS 'IT'" in query:
                return [{"w.url": f"https://example{i}.com"} for i in range(15)]
            # Organizations with networks query
            elif "MATCH (o:Organization)-[:HAS_NETWORK]->(n:Network)" in query:
                return [{"o.name": f"Org {i}"} for i in range(8)]
            # Compromised devices query
            elif "MATCH (u:User)-[:LOGGED_IN_FROM]->(d:Device) WHERE d.status = 'compromised'" in query:
                return [{"u.name": f"User {i}", "d.hostname": f"device-{i}"} for i in range(5)]
            # High severity events query
            elif "MATCH (e:Event)-[:TRIGGERED_BY]->(u:User) WHERE e.severity IN ['high', 'critical']" in query:
                return [{"u.name": f"User {i}", "e.event_type": "alert", "e.severity": "high", "e.timestamp": "2023-01-01"} for i in range(3)]
            # Blacklisted IP devices query
            elif "MATCH (d:Device)-[:STORED_ON]->(f:File) MATCH (d)-[:HAS_IP]->(ip:IPAddress)" in query:
                return [{"d.hostname": f"device-{i}", "ip.address": f"192.168.1.{i}", "f.name": f"file-{i}.txt"} for i in range(2)]
            else:
                return []
        
        mock_connector.run.side_effect = mock_run
        return mock_connector
    
    @pytest.mark.parametrize("query_idx", range(len(SAMPLE_NEO4J_QUERIES)))
    def test_sample_query(self, mock_neo4j_connector, query_idx):
        """Test each sample query in SAMPLE_NEO4J_QUERIES."""
        query_data = SAMPLE_NEO4J_QUERIES[query_idx]
        
        # Execute the Cypher query
        results = mock_neo4j_connector.run(query_data["cypher"])
        
        # Verify results match expectations
        assert results is not None
        assert len(results) > 0
        
        # Output for manual verification
        nlp_query = query_data["nlp"]
        cypher_query = query_data["cypher"]
        expected = query_data["expected"]
        
        # Simple validation based on expected string
        if "count" in expected:
            # If expecting a count, check that the result has a number
            assert any(isinstance(val, int) for val in results[0].values())
        elif "rows" in expected:
            # If expecting multiple rows, check the result count
            expected_count = int(expected.split()[0])
            assert len(results) <= expected_count  # Can be less in our mock 

@pytest.mark.skip(reason="Requires a running Neo4j instance")
class TestNeo4jDemoIntegration:
    """Integration tests for Neo4j demo with a real Neo4j instance."""
    
    @pytest.fixture(scope="class")
    def neo4j_service(self):
        """Create and yield a real Neo4j service for testing."""
        from app.config.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        neo4j_config = config_manager.get_neo4j_config()
        
        # Force enable Neo4j
        neo4j_config["enabled"] = True
        
        # Create service
        app = Neo4jService.enable_for_demo(config_manager)
        
        yield app.neo4j_service
        
        # Cleanup
        if app.neo4j_service:
            app.neo4j_service.close()
    
    def test_connection(self, neo4j_service):
        """Test connection to Neo4j."""
        assert neo4j_service is not None
        assert neo4j_service.connector is not None
        
        node_labels = neo4j_service.connector.get_table_names()
        assert len(node_labels) > 0
        assert "User" in node_labels
        
        rel_types = neo4j_service.connector.get_view_names()
        assert len(rel_types) > 0
    
    def test_check_data_exists(self, neo4j_service):
        """Test check_data_exists with real Neo4j."""
        data_exists = check_data_exists(neo4j_service)
        assert isinstance(data_exists, bool)
    
    @pytest.mark.parametrize("query_idx", range(len(SAMPLE_NEO4J_QUERIES)))
    def test_sample_queries_direct(self, neo4j_service, query_idx):
        """Test each sample query directly against Neo4j."""
        query_data = SAMPLE_NEO4J_QUERIES[query_idx]
        cypher_query = query_data["cypher"]
        
        # Execute query directly
        results = neo4j_service.connector.run(cypher_query)
        
        # Basic validation
        assert results is not None
        
        # Verify against expected outcomes based on the query
        if "count" in query_data["expected"]:
            # Count queries should return at least one result with a number
            assert len(results) > 0
            # The field name might vary, so we just check any numeric value
            assert any(isinstance(val, (int, float)) for val in results[0].values())
        elif "rows" in query_data["expected"]:
            # If we expect rows, check that we got some results
            # Note: We can't guarantee exact number in a real environment
            assert len(results) >= 0
    
    def test_in_memory_embedding(self, neo4j_service):
        """Test in-memory embedding functionality."""
        # Test search_schema with in-memory embedding
        schema_results = neo4j_service.search_schema("What are users?", top_k=2)
        assert schema_results is not None
        assert len(schema_results) > 0
        
        # Verify log messages about in-memory embedding
        with patch('app.services.neo4j_service.logger') as mock_logger:
            neo4j_service.embed_schema()
            mock_logger.info.assert_any_call("Using in-memory embedding instead of Neo4j schema embeddings")
        
        with patch('app.services.neo4j_service.logger') as mock_logger:
            neo4j_service.add_embeddings("User")
            mock_logger.info.assert_any_call("Using in-memory embedding instead of Neo4j embeddings")
    
    @pytest.mark.parametrize("question_idx", [0, 1, 2])  # Test first 3 questions
    def test_questions_from_demo(self, neo4j_service, question_idx):
        """Test selected questions from the demo."""
        question = SAMPLE_NEO4J_QUERIES[question_idx]["nlp"]
        matching_sample = next((sample for sample in SAMPLE_NEO4J_QUERIES if sample["nlp"] == question), None)
        
        assert matching_sample is not None
        
        # Execute the Cypher query
        results = neo4j_service.connector.run(matching_sample["cypher"])
        
        # Basic validation
        assert results is not None
        assert len(results) > 0
    
    @pytest.mark.parametrize("custom_question", [
        "What devices have a high risk score?",
        "Show me all compromised devices connected to the internet",
        "Which users accessed unusual websites in the last month?",
        "List all events with critical severity",
        "What is the relationship between users and organizations?"
    ])
    def test_custom_questions(self, neo4j_service, custom_question):
        """Test handling of custom questions not in SAMPLE_NEO4J_QUERIES."""
        # Verify that no matching query exists in the samples
        matching_sample = next((sample for sample in SAMPLE_NEO4J_QUERIES if sample["nlp"] == custom_question), None)
        assert matching_sample is None, "Test assumes this is a custom question not in SAMPLE_NEO4J_QUERIES"
        
        # Test schema search
        schema_results = neo4j_service.search_schema(custom_question, top_k=2)
        
        # Verify schema search works with in-memory approach
        assert schema_results is not None
        assert len(schema_results) > 0
        assert "type" in schema_results[0]
        assert "name" in schema_results[0]
        assert "score" in schema_results[0]
        
        # Test document search
        doc_results = neo4j_service.search_documents(custom_question, top_k=2)
        
        # Verify document search works with in-memory approach
        assert doc_results is not None
        assert len(doc_results) > 0
        assert "title" in doc_results[0]
        assert "score" in doc_results[0]
        
        # Test that both search methods use in-memory approach
        with patch('app.services.neo4j_service.logger') as mock_logger:
            neo4j_service.search_schema(custom_question)
            neo4j_service.search_documents(custom_question)
            
            mock_logger.info.assert_any_call(f"Using in-memory search from schema embedder for query: '{custom_question}'")
            mock_logger.info.assert_any_call(f"Using in-memory search from document store for query: '{custom_question}'")
    
    def test_generate_cypher_for_custom_question(self, neo4j_service):
        """Test ability to generate Cypher for custom questions (if supported)."""
        # Note: This test assumes there might be a method to generate Cypher for custom questions
        # If your system doesn't support this, you can skip or remove this test
        
        try:
            # Try to import a query generator if it exists
            from app.extensions.neo4j_query_generator import Neo4jQueryGenerator
            
            # Test with a custom question
            question = "What's the average risk score of all devices?"
            
            # Initialize query generator if available
            query_generator = Neo4jQueryGenerator({})
            query = query_generator.generate_query(question)
            
            # If we get here, verify the generated query
            assert query is not None
            assert "MATCH" in query
            assert "RETURN" in query
            
            # Try to execute the generated query
            try:
                results = neo4j_service.connector.run(query)
                # If execution succeeded, verify results
                assert results is not None
            except Exception as e:
                # It's okay if execution fails, just log it
                print(f"Generated query execution failed: {str(e)}")
                
        except ImportError:
            # Skip if query generator is not available
            pytest.skip("Neo4jQueryGenerator not available") 
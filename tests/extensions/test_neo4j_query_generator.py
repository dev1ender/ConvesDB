"""
Tests for Neo4j query generator.
"""
import pytest
from unittest.mock import MagicMock, patch
import json

from app.extensions.neo4j_query_generator import Neo4jQueryGenerator
from app.extensions.neo4j_prompt_generator import Neo4jPromptGenerator

class TestNeo4jQueryGenerator:
    """Test suite for Neo4jQueryGenerator class."""
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LLM client for testing."""
        mock = MagicMock()
        mock.chat_completion.return_value = {
            "content": "MATCH (u:User)-[:LOGGED_IN]->(l:LoginEvent) WHERE l.timestamp > datetime('2023-01-01') RETURN u.name, COUNT(l) as login_count",
            "finish_reason": "stop"
        }
        return mock
    
    @pytest.fixture
    def query_generator(self, mock_llm):
        """Create a query generator for testing."""
        with patch('app.llm.factory.LLMFactory.create_chat_client', return_value=mock_llm):
            config = {
                "llm": {
                    "model": "test-model"
                },
                "prompt_generator": {
                    "max_schema_items": 5
                }
            }
            return Neo4jQueryGenerator(config)
    
    def test_init(self, query_generator, mock_llm):
        """Test initialization of query generator."""
        assert query_generator is not None
        assert query_generator.llm_model is mock_llm
        assert isinstance(query_generator.prompt_generator, Neo4jPromptGenerator)
    
    def test_generate_query(self, query_generator, mock_llm):
        """Test generating a Cypher query."""
        question = "Find users who logged in after January 1st, 2023"
        
        schema_items = [
            {
                "type": "node_label",
                "name": "User",
                "description": "Node Label: User\nProperties:\n  - name (STRING)\n  - email (STRING)"
            },
            {
                "type": "node_label",
                "name": "LoginEvent",
                "description": "Node Label: LoginEvent\nProperties:\n  - timestamp (DATETIME)\n  - successful (BOOLEAN)"
            },
            {
                "type": "relationship_type",
                "name": "LOGGED_IN",
                "description": "Relationship Type: LOGGED_IN\nFrom: User\nTo: LoginEvent"
            }
        ]
        
        # Test without document context
        cypher_query, confidence = query_generator.generate_query(question, schema_items)
        
        # Verify LLM was called with the right prompt
        mock_llm.chat_completion.assert_called_once()
        call_args = mock_llm.chat_completion.call_args[0][0]
        
        # Check system message contains schema information
        system_msg = call_args[0]["content"]
        assert "User" in system_msg
        assert "LoginEvent" in system_msg
        assert "LOGGED_IN" in system_msg
        
        # Check user message contains the question
        user_msg = call_args[1]["content"]
        assert question in user_msg
        
        # Check the returned query matches what the LLM returned
        expected_query = "MATCH (u:User)-[:LOGGED_IN]->(l:LoginEvent) WHERE l.timestamp > datetime('2023-01-01') RETURN u.name, COUNT(l) as login_count"
        assert cypher_query == expected_query
        assert confidence > 0.5
    
    def test_generate_query_with_docs(self, query_generator, mock_llm):
        """Test generating a Cypher query with document context."""
        question = "Find users who logged in after January 1st, 2023"
        
        schema_items = [
            {
                "type": "node_label",
                "name": "User",
                "description": "Node Label: User\nProperties:\n  - name (STRING)"
            }
        ]
        
        context_docs = [
            {
                "content": "Document context about logins",
                "source": "Source 1"
            }
        ]
        
        # Reset the mock
        mock_llm.reset_mock()
        
        # Test with document context
        cypher_query, confidence = query_generator.generate_query(question, schema_items, context_docs)
        
        # Verify LLM was called with the right prompt including document context
        mock_llm.chat_completion.assert_called_once()
        call_args = mock_llm.chat_completion.call_args[0][0]
        
        # Check system message contains document context
        system_msg = call_args[0]["content"]
        assert "Document context about logins" in system_msg
        assert "Source 1" in system_msg
    
    def test_extract_query_from_response(self, query_generator):
        """Test extracting query from LLM response."""
        # Test with plain text
        response = {"content": "MATCH (n) RETURN n"}
        query = query_generator._extract_query_from_response(response)
        assert query == "MATCH (n) RETURN n"
        
        # Test with code block
        response = {"content": "```cypher\nMATCH (n) RETURN n\n```"}
        query = query_generator._extract_query_from_response(response)
        assert query == "MATCH (n) RETURN n"
        
        # Test with language marker
        response = {"content": "```cypher\nMATCH (n) RETURN n\n```"}
        query = query_generator._extract_query_from_response(response)
        assert query == "MATCH (n) RETURN n"
    
    def test_calculate_confidence(self, query_generator):
        """Test confidence calculation."""
        # Test with 'stop' finish reason (high confidence)
        response = {"finish_reason": "stop", "content": "MATCH (n) RETURN n"}
        confidence = query_generator._calculate_confidence(response)
        assert confidence > 0.8
        
        # Test with 'length' finish reason (lower confidence)
        response = {"finish_reason": "length", "content": "MATCH (n) RETURN n"}
        confidence = query_generator._calculate_confidence(response)
        assert confidence < 0.7
        
        # Test with unknown finish reason (default confidence)
        response = {"finish_reason": "unknown", "content": "MATCH (n) RETURN n"}
        confidence = query_generator._calculate_confidence(response)
        assert 0.6 < confidence < 0.8
    
    def test_fix_query_errors(self, query_generator, mock_llm):
        """Test fixing errors in a Cypher query."""
        # Set up the mock to return a fixed query
        mock_llm.chat_completion.return_value = {
            "content": "MATCH (u:User)-[:LOGGED_IN]->(l:LoginEvent) RETURN u.name, l.timestamp",
            "finish_reason": "stop"
        }
        
        cypher_query = "MATCH (u:User)-[:LOGGED_IN]->(l:LoginEvnt) RETURN u.name, l.timestamp"
        error_message = "Node label 'LoginEvnt' does not exist"
        schema_context = "Node Label: User\nNode Label: LoginEvent"
        
        # Reset the mock
        mock_llm.reset_mock()
        
        fixed_query, confidence = query_generator.fix_query_errors(cypher_query, error_message, schema_context)
        
        # Verify LLM was called with the right prompt
        mock_llm.chat_completion.assert_called_once()
        call_args = mock_llm.chat_completion.call_args[0][0]
        
        # Check system message contains error information
        system_msg = call_args[0]["content"]
        assert cypher_query in system_msg
        assert error_message in system_msg
        assert schema_context in system_msg
        
        # Check the returned fixed query
        expected_fixed_query = "MATCH (u:User)-[:LOGGED_IN]->(l:LoginEvent) RETURN u.name, l.timestamp"
        assert fixed_query == expected_fixed_query
        assert confidence > 0.7 
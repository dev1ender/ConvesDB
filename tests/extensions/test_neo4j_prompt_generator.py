"""
Tests for Neo4j prompt generator.
"""
import pytest
from unittest.mock import MagicMock, patch
import json

from app.extensions.neo4j_prompt_generator import Neo4jPromptGenerator

class TestNeo4jPromptGenerator:
    """Test suite for Neo4jPromptGenerator class."""
    
    @pytest.fixture
    def prompt_generator(self):
        """Create a prompt generator for testing."""
        config = {
            "schema_types": ["node_labels", "relationship_types"],
            "max_schema_items": 5
        }
        return Neo4jPromptGenerator(config)
    
    def test_init(self, prompt_generator):
        """Test initialization of prompt generator."""
        assert prompt_generator is not None
        assert prompt_generator.schema_types == ["node_labels", "relationship_types"]
        assert prompt_generator.max_schema_items == 5
        assert prompt_generator.system_template != ""
        assert prompt_generator.user_template != ""
    
    def test_load_default_templates(self, prompt_generator):
        """Test loading default templates."""
        # Save original templates
        original_system = prompt_generator.system_template
        original_user = prompt_generator.user_template
        
        # Reset templates
        prompt_generator.system_template = ""
        prompt_generator.user_template = ""
        
        # Load defaults
        prompt_generator._load_default_templates()
        
        # Verify templates are loaded
        assert prompt_generator.system_template != ""
        assert prompt_generator.user_template != ""
        assert "SCHEMA INFORMATION:" in prompt_generator.system_template
        assert "{user_question}" in prompt_generator.user_template
        
        # Restore original templates for other tests
        prompt_generator.system_template = original_system
        prompt_generator.user_template = original_user
    
    def test_build_prompt_with_schema_only(self, prompt_generator):
        """Test building prompt with schema items only."""
        user_question = "Find all users who logged in last week"
        
        schema_items = [
            {
                "type": "node_label",
                "name": "User",
                "description": "Node Label: User\nProperties:\n  - name (STRING)\n  - email (STRING)\n  - created_at (DATETIME)"
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
        
        prompt = prompt_generator.build_prompt(user_question, schema_items)
        
        # Check prompt structure
        assert isinstance(prompt, dict)
        assert "system" in prompt
        assert "user" in prompt
        
        # Check content
        assert "NODE LABELS:" in prompt["system"]
        assert "RELATIONSHIP TYPES:" in prompt["system"]
        assert "User" in prompt["system"]
        assert "LoginEvent" in prompt["system"]
        assert "LOGGED_IN" in prompt["system"]
        assert user_question in prompt["user"]
    
    def test_build_prompt_with_schema_and_docs(self, prompt_generator):
        """Test building prompt with schema items and document context."""
        user_question = "Find all users who logged in last week"
        
        schema_items = [
            {
                "type": "node_label",
                "name": "User",
                "description": "Node Label: User\nProperties:\n  - name (STRING)\n  - email (STRING)"
            }
        ]
        
        context_docs = [
            {
                "content": "Users can log in using the login API endpoint which creates a LoginEvent node.",
                "source": "API Documentation"
            },
            {
                "content": "Each login event is timestamped and linked to the user who initiated it.",
                "source": "System Design"
            }
        ]
        
        prompt = prompt_generator.build_prompt(user_question, schema_items, context_docs)
        
        # Check content
        assert "NODE LABELS:" in prompt["system"]
        assert "DOCUMENT CONTEXT:" in prompt["system"]
        assert "API Documentation" in prompt["system"]
        assert "System Design" in prompt["system"]
        assert "login API endpoint" in prompt["system"]
    
    def test_format_schema_context_limit(self, prompt_generator):
        """Test schema context formatting with limit."""
        # Create more schema items than the limit
        schema_items = []
        for i in range(10):
            schema_items.append({
                "type": "node_label",
                "name": f"Label{i}",
                "description": f"Node Label: Label{i}\nProperties:\n  - prop{i} (STRING)"
            })
        
        # Set low limit
        prompt_generator.max_schema_items = 3
        
        context = prompt_generator._format_schema_context(schema_items)
        
        # Verify only the first 3 items are included
        assert "Label0" in context
        assert "Label1" in context
        assert "Label2" in context
        assert "Label9" not in context
    
    def test_format_document_context(self, prompt_generator):
        """Test document context formatting."""
        context_docs = [
            {
                "content": "Document content 1",
                "source": "Source 1"
            },
            {
                "content": "Document content 2",
                "source": "Source 2"
            }
        ]
        
        context = prompt_generator._format_document_context(context_docs)
        
        # Verify document content is properly formatted
        assert "DOCUMENT CONTEXT:" in context
        assert "--- Source 1 ---" in context
        assert "Document content 1" in context
        assert "--- Source 2 ---" in context
        assert "Document content 2" in context
    
    def test_build_error_correction_prompt(self, prompt_generator):
        """Test building error correction prompt."""
        cypher_query = "MATCH (u:User)-[:LOGGED_IN]->(l:LoginEvnt) RETURN u.name, l.timestamp"
        error = "Node label 'LoginEvnt' does not exist"
        schema_context = "Node Label: User\nNode Label: LoginEvent"
        
        prompt = prompt_generator.build_error_correction_prompt(cypher_query, error, schema_context)
        
        # Check prompt structure
        assert isinstance(prompt, dict)
        assert "system" in prompt
        assert "user" in prompt
        
        # Check content
        assert cypher_query in prompt["system"]
        assert error in prompt["system"]
        assert schema_context in prompt["system"]
        assert "Fix the Cypher query" in prompt["user"] 
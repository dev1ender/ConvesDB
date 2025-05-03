"""
Tests for the agents module.
"""

import unittest
from unittest.mock import MagicMock, patch
import json

from app.agents.schema_agent import SchemaAgent
from app.agents.prompt_agent import PromptAgent
from app.agents.query_generator import QueryGenerator
from app.agents.query_executor import QueryExecutor


class TestSchemaAgent(unittest.TestCase):
    """Tests for the SchemaAgent class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock database connector
        self.mock_db = MagicMock()
        
        # Set up mock table names
        self.mock_db.get_table_names.return_value = ["test_table"]
        
        # Set up mock table schema
        self.mock_db.get_table_schema.return_value = [
            {"name": "id", "type": "INTEGER", "pk": 1},
            {"name": "name", "type": "TEXT"},
            {"name": "value", "type": "INTEGER"}
        ]
        
        # Set up mock query results
        self.mock_db.run.return_value = [
            {"id": 1, "name": "test1", "value": 100},
            {"id": 2, "name": "test2", "value": 200}
        ]
        
        # Create schema agent
        self.schema_agent = SchemaAgent(self.mock_db)
    
    def test_extract_schema(self):
        """Test extracting schema."""
        schema = self.schema_agent.extract_schema()
        
        # Check that schema has tables
        self.assertIn("tables", schema)
        self.assertIn("test_table", schema["tables"])
        
        # Check table schema
        test_table = schema["tables"]["test_table"]
        self.assertIn("columns", test_table)
        self.assertIn("sample_data", test_table)
        
        # Check columns
        columns = test_table["columns"]
        self.assertEqual(len(columns), 3)
        
        # Check column names
        column_names = [col["name"] for col in columns]
        self.assertIn("id", column_names)
        self.assertIn("name", column_names)
        self.assertIn("value", column_names)
    
    def test_get_schema_as_json(self):
        """Test getting schema as JSON."""
        schema_json = self.schema_agent.get_schema_as_json()
        
        # Check that it's valid JSON
        schema = json.loads(schema_json)
        self.assertIn("tables", schema)
    
    def test_get_relevant_tables_with_keywords(self):
        """Test getting relevant tables with keywords."""
        # Ensure we use keyword matching
        self.schema_agent.use_embeddings = False
        
        # Test with table name in question
        tables = self.schema_agent.get_relevant_tables("Show me data from test_table")
        self.assertIn("test_table", tables)


class TestPromptAgent(unittest.TestCase):
    """Tests for the PromptAgent class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock schema agent
        self.mock_schema_agent = MagicMock()
        
        # Set up mock table schema
        self.mock_schema_agent.get_table_schema.return_value = {
            "columns": [
                {"name": "id", "type": "INTEGER", "primary_key": True},
                {"name": "name", "type": "TEXT"},
                {"name": "value", "type": "INTEGER"}
            ]
        }
        
        # Create prompt agent
        self.prompt_agent = PromptAgent(self.mock_schema_agent)
    
    def test_build_prompt(self):
        """Test building a prompt."""
        prompt = self.prompt_agent.build_prompt("How many items are there?", ["test_table"])
        
        # Check that the prompt includes instructions
        self.assertIn("You are a SQL expert", prompt)
        
        # Check that the prompt includes the schema
        self.assertIn("Table: test_table", prompt)
        self.assertIn("Columns:", prompt)
        
        # Check that the prompt includes the question
        self.assertIn("How many items are there?", prompt)
    
    def test_build_error_correction_prompt(self):
        """Test building an error correction prompt."""
        prompt = self.prompt_agent.build_error_correction_prompt(
            "SELECT * FROM non_existent_table",
            "Table 'non_existent_table' not found",
            "Table: test_table\nColumns:\n  - id (INTEGER) (Primary Key)\n  - name (TEXT)\n  - value (INTEGER)"
        )
        
        # Check that the prompt includes the SQL query
        self.assertIn("SELECT * FROM non_existent_table", prompt)
        
        # Check that the prompt includes the error
        self.assertIn("Table 'non_existent_table' not found", prompt)
        
        # Check that the prompt includes instructions to fix
        self.assertIn("Please fix the query", prompt)


class TestQueryExecutor(unittest.TestCase):
    """Tests for the QueryExecutor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock database connector
        self.mock_db = MagicMock()
        
        # Set up mock query results
        self.mock_db.run.return_value = [
            {"id": 1, "name": "test1", "value": 100},
            {"id": 2, "name": "test2", "value": 200}
        ]
        
        # Create query executor
        self.query_executor = QueryExecutor(self.mock_db)
    
    def test_execute_query_select(self):
        """Test executing a SELECT query."""
        results = self.query_executor.execute_query("SELECT * FROM test_table")
        
        # Check that run was called
        self.mock_db.run.assert_called_once_with("SELECT * FROM test_table")
        
        # Check results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["name"], "test1")
    
    def test_execute_query_update_read_only(self):
        """Test executing an UPDATE query in read-only mode."""
        # Set read-only mode
        self.query_executor.read_only = True
        
        # Try to execute an UPDATE query
        with self.assertRaises(Exception):
            self.query_executor.execute_query("UPDATE test_table SET value = 300 WHERE id = 1")
    
    def test_execute_query_update_not_read_only(self):
        """Test executing an UPDATE query when not in read-only mode."""
        # Disable read-only mode
        self.query_executor.read_only = False
        
        # Execute an UPDATE query
        self.query_executor.execute_query("UPDATE test_table SET value = 300 WHERE id = 1")
        
        # Check that run was called
        self.mock_db.run.assert_called_once_with("UPDATE test_table SET value = 300 WHERE id = 1")


if __name__ == "__main__":
    unittest.main() 
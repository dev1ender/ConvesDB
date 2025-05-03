"""
Tests for the database module.
"""

import unittest
import os
import tempfile
from app.database.sqlite_connector import SQLiteConnector


class TestSQLiteConnector(unittest.TestCase):
    """Tests for the SQLiteConnector class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary database file
        fd, self.db_file = tempfile.mkstemp(suffix=".sqlite")
        os.close(fd)
        
        # Create database connector
        self.db_connector = SQLiteConnector(self.db_file)
        self.db_connector.connect()
        
        # Create test tables
        self.db_connector.run("""
        CREATE TABLE test_table (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            value INTEGER
        );
        
        INSERT INTO test_table (name, value) VALUES
            ('test1', 100),
            ('test2', 200),
            ('test3', 300);
        """)
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.db_connector.close()
        os.unlink(self.db_file)
    
    def test_get_table_names(self):
        """Test getting table names."""
        tables = self.db_connector.get_table_names()
        self.assertIn("test_table", tables)
    
    def test_get_table_schema(self):
        """Test getting table schema."""
        schema = self.db_connector.get_table_schema("test_table")
        
        # Check column count
        self.assertEqual(len(schema), 3)
        
        # Check column names
        column_names = [col["name"] for col in schema]
        self.assertIn("id", column_names)
        self.assertIn("name", column_names)
        self.assertIn("value", column_names)
        
        # Check primary key
        pk_col = next((col for col in schema if col["name"] == "id"), None)
        self.assertEqual(pk_col["pk"], 1)
    
    def test_run_select(self):
        """Test running a SELECT query."""
        results = self.db_connector.run("SELECT * FROM test_table ORDER BY id")
        
        # Check result count
        self.assertEqual(len(results), 3)
        
        # Check first result
        self.assertEqual(results[0]["name"], "test1")
        self.assertEqual(results[0]["value"], 100)
    
    def test_run_update(self):
        """Test running an UPDATE query."""
        # Update a value
        self.db_connector.run("UPDATE test_table SET value = 400 WHERE name = 'test1'")
        
        # Check the updated value
        results = self.db_connector.run("SELECT value FROM test_table WHERE name = 'test1'")
        self.assertEqual(results[0]["value"], 400)
    
    def test_run_error(self):
        """Test handling errors in queries."""
        with self.assertRaises(Exception):
            self.db_connector.run("SELECT * FROM non_existent_table")


if __name__ == "__main__":
    unittest.main() 
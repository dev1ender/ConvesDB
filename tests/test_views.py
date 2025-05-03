import unittest
import sqlite3
import os
import sys
import json

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.seed_data import create_database_schema, create_database_schema_part2, create_aggregated_views
from app.database import SQLiteConnector
from app.schema_agent import SchemaAgent

class TestViews(unittest.TestCase):
    """Test the database views implementation."""
    
    def setUp(self):
        """Set up the test database."""
        # Use in-memory database for tests with shared cache
        self.db_path = ":memory:"
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Set row factory for the connection
        
        # Just create schema and views, without seeding data
        create_database_schema(self.conn)
        create_database_schema_part2(self.conn)
        create_aggregated_views(self.conn)
        
        # Create a custom simple function to list tables and views
        def get_tables_and_views(conn, show_views=True):
            cursor = conn.cursor()
            types = "'table'" if not show_views else "'table', 'view'"
            cursor.execute(f"""
            SELECT name, type FROM sqlite_master 
            WHERE type IN ({types}) 
            AND name NOT LIKE 'sqlite_%'
            """)
            return [(row['name'], row['type']) for row in cursor.fetchall()]
        
        # Get the list of tables and views
        self.tables_and_views = get_tables_and_views(self.conn)
        
        # Create an independent connector for the schema agent
        self.db_connector = SQLiteConnector(self.db_path)
        self.db_connector.connect()
        
        # Create schema agent
        self.schema_agent = SchemaAgent(self.db_connector)
        self.schema_agent.extract_schema()
    
    def tearDown(self):
        """Clean up resources."""
        if self.conn:
            self.conn.close()
        
        if self.db_connector:
            self.db_connector.close()
    
    def test_view_existence(self):
        """Test that views were created successfully."""
        # Extract views from tables_and_views
        views = [name for name, type_ in self.tables_and_views if type_ == 'view']
        
        # Check if views exist
        view_names = [
            "vw_product_sales_summary",
            "vw_customer_purchase_summary",
            "vw_inventory_status_summary",
            "vw_monthly_sales_trends",
            "vw_office_performance_summary",
            "vw_product_review_stats",
            "vw_customer_activity_summary",
            "vw_employee_performance_metrics"
        ]
        
        for view_name in view_names:
            self.assertIn(view_name, views, f"View {view_name} should exist in the database")
    
    def test_schema_agent_view_recognition(self):
        """Test that the SchemaAgent correctly recognizes views."""
        schema = self.schema_agent.schema_cache
        
        # Check that views are stored in the views section
        self.assertIn("views", schema, "Schema should have a 'views' section")
        
        view_names = [
            "vw_product_sales_summary",
            "vw_customer_purchase_summary",
            "vw_inventory_status_summary",
            "vw_monthly_sales_trends",
            "vw_office_performance_summary",
            "vw_product_review_stats",
            "vw_customer_activity_summary",
            "vw_employee_performance_metrics"
        ]
        
        for view_name in view_names:
            self.assertIn(view_name, schema["views"], f"View {view_name} should be in schema 'views' section")

    def test_table_exists_includes_views(self):
        """Test that table_exists includes views."""
        view_names = [
            "vw_product_sales_summary",
            "vw_customer_purchase_summary",
            "vw_inventory_status_summary"
        ]
        
        for view_name in view_names:
            self.assertTrue(self.schema_agent.table_exists(view_name),
                           f"table_exists should return True for view {view_name}")

if __name__ == '__main__':
    unittest.main() 
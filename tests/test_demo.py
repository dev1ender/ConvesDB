import pytest
import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the application factory
from app.factory import ApplicationFactory
from app.config.config_manager import ConfigManager

class TestNLToSQLDemo:
    
    @pytest.fixture(scope="class")
    def app(self, setup_large_test_db):
        """Create the application instance for testing"""
        # Update config to use the test database
        config_manager = ConfigManager("config.yml")
        config_manager.config["database"]["db_path"] = setup_large_test_db
        
        # Initialize app
        app = ApplicationFactory.create_app(config_manager=config_manager)
        yield app
        app.close()
    
    @pytest.mark.parametrize("question,expected_columns", [
        # Product revenue questions
        (
            "Which products have generated the highest total revenue in the last 6 months?",
            ["product_name", "category", "brand", "total_revenue"]
        ),
        # Customer spending questions
        (
            "List the top 5 customers by total spending, including their email and number of completed orders.",
            ["customer_name", "email", "total_spent", "completed_orders"]
        ),
        # Monthly sales trends
        (
            "Show the monthly sales trends for the past year, including total revenue and unique customers per month.",
            ["month", "total_revenue", "unique_customers"]
        ),
        # Office inventory questions
        (
            "Which offices have the highest inventory turnover (sales count vs. inventory units)?",
            ["office_name", "city", "turnover_ratio"]
        ),
        # Employee performance questions
        (
            "Find all employees who have handled more than 10 inventory movements and have an average customer review rating above 4.",
            ["employee_name", "position", "department", "inventory_movements", "avg_rating"]
        ),
        # Out of stock products
        (
            "List all products that are out of stock in at least 3 locations.",
            ["product_name", "category", "out_of_stock_locations"]
        ),
        # Order value by account type
        (
            "Show the average order value and total number of orders for each account type (standard, premium, enterprise).",
            ["account_type", "avg_order_value", "total_orders"]
        ),
        # Product reviews
        (
            "Which products have received the most positive reviews (rating >= 4) in the last 3 months?",
            ["product_name", "category", "positive_review_count"]
        ),
        # Inactive customers with loyalty points
        (
            "Find customers who have not placed any orders in the last year but have a high loyalty points balance.",
            ["customer_name", "email", "loyalty_points", "days_since_last_order"]
        ),
        # Office performance summary
        (
            "Show the performance summary for each office, including employee count, average salary, and sales count.",
            ["office_name", "employee_count", "avg_salary", "sales_count"]
        ),
        # Additional complex questions
        (
            "What is the average order value by day of week?",
            ["day_of_week", "avg_order_value", "order_count"]
        ),
        (
            "Which product categories have seen the biggest growth in sales compared to the previous quarter?",
            ["category", "current_quarter_sales", "previous_quarter_sales", "growth_percentage"]
        ),
        (
            "List employees with the highest customer satisfaction ratings who have also processed over $10,000 in sales.",
            ["employee_name", "position", "avg_satisfaction", "total_sales"]
        ),
        (
            "Which customers have purchased products from all available categories?",
            ["customer_name", "email", "category_count", "total_categories"]
        ),
        (
            "Find products that are frequently purchased together in the same order.",
            ["product1_name", "product2_name", "co_purchase_count"]
        )
    ])
    def test_process_question(self, app, question, expected_columns):
        """Test that the application can process questions and return expected column structure"""
        # Process the question
        response = app.process_question(question)
        
        # Check that the response contains required fields
        assert "sql_query" in response
        assert "results" in response
        assert "error" in response
        
        # Print the SQL for debugging
        print(f"\nQuestion: {question}")
        print(f"SQL: {response['sql_query']}")
        
        # Check for errors
        assert not response["error"], f"Error processing question: {response['error']}"
        
        # Verify we got results
        assert len(response["results"]) > 0, "No results returned from query"
        
        # If we have results, check the first result has the expected structure
        if len(response["results"]) > 0:
            first_result = response["results"][0]
            
            # Convert result to dict if it's in another format
            if not isinstance(first_result, dict):
                # Try to parse if it's JSON string
                try:
                    if isinstance(first_result, str) and first_result.strip().startswith('{'):
                        first_result = json.loads(first_result)
                except:
                    pass
            
            # Check that at least some of the expected columns are present
            # We don't require exact column names as the NLP-to-SQL might generate variations
            result_keys = list(first_result.keys()) if isinstance(first_result, dict) else []
            
            # Check for semantic similarity rather than exact match
            # For each expected column, see if there's a similar column in the results
            found_columns = 0
            for expected_col in expected_columns:
                for result_col in result_keys:
                    if (expected_col.lower() in result_col.lower() or 
                        result_col.lower() in expected_col.lower()):
                        found_columns += 1
                        break
            
            # At least half of the expected columns should be present or similar
            min_columns = max(1, len(expected_columns) // 2)
            assert found_columns >= min_columns, (
                f"Expected at least {min_columns} of these columns: {expected_columns}, "
                f"but got: {result_keys}"
            )

    def test_schema_info(self, app):
        """Test that the application returns valid schema information"""
        schema_info = json.loads(app.get_schema_info())
        
        assert "tables" in schema_info
        assert len(schema_info["tables"]) > 0
        
        # Check for some expected tables
        expected_tables = ["customers", "products", "orders", "employees", "inventory"]
        for table in expected_tables:
            assert table in schema_info["tables"], f"Expected table '{table}' in schema"
            
            # Check that table has columns
            table_info = schema_info["tables"][table]
            assert "columns" in table_info
            assert len(table_info["columns"]) > 0
            
            # Each column should have name and type attributes
            for column in table_info["columns"]:
                assert "name" in column
                assert "type" in column 
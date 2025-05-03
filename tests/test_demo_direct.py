#!/usr/bin/env python3
"""
Direct test runner for the demo.py file without using pytest.
This lets us test the NLP-to-SQL functionality with the large seed database.
"""
import os
import sys
import json
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import required components
from app.factory import ApplicationFactory
from app.config.config_manager import ConfigManager
from app.utils.logging_setup import setup_logging, get_logger

# Set up logger
setup_logging()
logger = get_logger(__name__)

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "large_test.sqlite")

# Test questions with expected column patterns
TEST_QUESTIONS = [
    {
        "question": "Show a list of all customers with their email addresses and account types",
        "expected_columns": ["customer", "email", "account"],
        "min_results": 3,
        "description": "Basic customer listing"
    },
    {
        "question": "List all products sorted by price",
        "expected_columns": ["product", "name", "price"],
        "min_results": 3,
        "description": "Basic product listing"
    },
    {
        "question": "How many orders were placed in the last 12 months?",
        "expected_columns": ["count", "orders"],
        "min_results": 1,
        "description": "Order count summary"
    },
    {
        "question": "What is the total amount of all orders?",
        "expected_columns": ["total", "sum", "amount"],
        "min_results": 1,
        "description": "Total order amount"
    },
    {
        "question": "Which customer has placed the most orders?",
        "expected_columns": ["customer", "name", "count", "orders"],
        "min_results": 1,
        "description": "Top customer by order count"
    },
    {
        "question": "List the top 5 most expensive products",
        "expected_columns": ["product", "name", "price"],
        "min_results": 1,
        "description": "Most expensive products"
    },
    {
        "question": "What is the average price of products in the Electronics category?",
        "expected_columns": ["average", "price", "electronics"],
        "min_results": 1,
        "description": "Average price by category"
    },
    {
        "question": "Show the total number of customers by account type",
        "expected_columns": ["account", "type", "count"],
        "min_results": 1,
        "description": "Customer count by account type"
    },
    {
        "question": "Which customers have placed orders in every month of the past year?",
        "expected_columns": ["customer", "order", "month"],
        "min_results": 1,
        "description": "Customers with orders in every month of the past year"
    },
    {
        "question": "List employees who have managed inventory in more than 3 offices and have an average order value above $500.",
        "expected_columns": ["employee", "office", "average_order_value"],
        "min_results": 1,
        "description": "Employees managing inventory in >3 offices and high avg order value"
    },
    {
        "question": "Show the top 10 products by revenue growth compared to the previous quarter.",
        "expected_columns": ["product", "revenue_growth", "quarter"],
        "min_results": 1,
        "description": "Top 10 products by revenue growth vs previous quarter"
    },
    {
        "question": "Which offices have the highest average customer satisfaction scores, and what are their top 3 selling products?",
        "expected_columns": ["office", "satisfaction_score", "product", "sales"],
        "min_results": 1,
        "description": "Offices with highest satisfaction and their top 3 products"
    },
    {
        "question": "Find customers who have purchased from all available product categories and have not returned any products.",
        "expected_columns": ["customer", "category", "returns"],
        "min_results": 1,
        "description": "Customers with purchases in all categories and no returns"
    },
    {
        "question": "Show the monthly trend of total sales, broken down by product category, for the last 2 years.",
        "expected_columns": ["month", "category", "total_sales"],
        "min_results": 1,
        "description": "Monthly sales trend by category for last 2 years"
    },
    {
        "question": "Which employees have processed orders for both premium and standard account types, and what is their total sales volume?",
        "expected_columns": ["employee", "account_type", "total_sales"],
        "min_results": 1,
        "description": "Employees with orders for both premium and standard accounts"
    },
    {
        "question": "List all products that have never been out of stock in any location.",
        "expected_columns": ["product", "stock", "location"],
        "min_results": 1,
        "description": "Products never out of stock in any location"
    },
    {
        "question": "Which customers have increased their order frequency by at least 50% compared to the previous year?",
        "expected_columns": ["customer", "order_frequency", "year"],
        "min_results": 1,
        "description": "Customers with 50%+ increase in order frequency vs last year"
    },
    {
        "question": "Show the correlation between employee tenure and average sales per employee.",
        "expected_columns": ["employee", "tenure", "average_sales", "correlation"],
        "min_results": 1,
        "description": "Correlation between employee tenure and average sales"
    }
]

def setup_app():
    """Set up the application with the test database"""
    # Create config manager and use test database
    config_manager = ConfigManager("config.yml")
    config_manager.config["database"]["db_path"] = DB_PATH
    
    # Create a temporary config file with the updated settings
    temp_config_path = os.path.join(os.path.dirname(__file__), "temp_config.yml")
    with open(temp_config_path, "w") as f:
        json.dump(config_manager.config, f)
    
    # Create app instance with config path
    app = ApplicationFactory.create_app(config_path=temp_config_path)
    
    # Clean up temp config file
    if os.path.exists(temp_config_path):
        os.remove(temp_config_path)
        
    return app

def run_tests():
    """Run all the NLP-to-SQL test questions"""
    # Initialize app
    print(f"\nInitializing application with database: {DB_PATH}")
    app = setup_app()
    
    # Print schema tables for reference
    schema_info = json.loads(app.get_schema_info())
    print(f"\nDatabase contains {len(schema_info['tables'])} tables:")
    for table_name in schema_info["tables"].keys():
        print(f"  - {table_name}")
    
    # Run tests
    total = len(TEST_QUESTIONS)
    passed = 0
    failed = 0
    failures = []
    
    print(f"\nRunning {total} test questions...\n")
    print("=" * 70)
    
    for idx, test in enumerate(TEST_QUESTIONS, 1):
        question = test["question"]
        expected_columns = test["expected_columns"]
        description = test["description"]
        min_results = test.get("min_results", 1)
        
        print(f"TEST {idx}/{total}: {description}")
        print(f"Question: '{question}'")
        
        # Process the question
        start_time = time.time()
        response = app.process_question(question)
        processing_time = time.time() - start_time
        
        print(f"SQL: {response['sql_query']}")
        
        # Check for errors
        if response["error"]:
            print(f"ERROR: {response['error']}")
            failed += 1
            failures.append((question, f"Error processing: {response['error']}"))
            print("FAILED")
            print("=" * 70)
            continue
        
        # Check for results
        result_count = len(response["results"])
        if result_count < min_results:
            print(f"Expected at least {min_results} results, but got {result_count}")
            failed += 1
            failures.append((question, f"Insufficient results: {result_count} < {min_results}"))
            print("FAILED")
            print("=" * 70)
            continue
        
        # Check column structure if we have results
        if result_count > 0:
            first_result = response["results"][0]
            
            # Convert result to dict if it's in another format
            if not isinstance(first_result, dict):
                try:
                    if isinstance(first_result, str) and first_result.strip().startswith('{'):
                        first_result = json.loads(first_result)
                except:
                    pass
            
            # Get result keys
            result_keys = list(first_result.keys()) if isinstance(first_result, dict) else []
            print(f"Result columns: {result_keys}")
            
            # Check for semantic similarity with expected columns
            found_columns = 0
            matching_columns = []
            
            for expected_col in expected_columns:
                for result_col in result_keys:
                    if (expected_col.lower() in result_col.lower() or 
                        result_col.lower() in expected_col.lower()):
                        found_columns += 1
                        matching_columns.append(result_col)
                        break
            
            # At least half of the expected columns should be present
            min_columns = max(1, len(expected_columns) // 2)
            if found_columns < min_columns:
                print(f"Expected at least {min_columns} of these columns: {expected_columns}")
                print(f"But only found these matching columns: {matching_columns}")
                failed += 1
                failures.append((
                    question, 
                    f"Column mismatch: found {found_columns}/{len(expected_columns)}"
                ))
                print("FAILED")
                print("=" * 70)
                continue
        
        # If we get here, test passed
        print(f"Results: {result_count} rows returned in {processing_time:.2f}s")
        print("PASSED")
        passed += 1
        print("=" * 70)
    
    # Print summary
    print("\nTEST SUMMARY")
    print(f"RESULTS: {passed} passed, {failed} failed, {total} total")
    
    if failures:
        print("\nFAILURES:")
        for idx, (question, reason) in enumerate(failures, 1):
            print(f"{idx}. '{question[:50]}{'...' if len(question) > 50 else ''}'")
            print(f"   Reason: {reason}")
    
    # Close app
    app.close()
    
    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1) 
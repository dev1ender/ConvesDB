#!/usr/bin/env python3

"""
Demo questions runner for the NL-to-SQL system.
This script demonstrates various natural language questions and their corresponding SQL queries.
"""

import sys
import os
import json
import time
from typing import Dict, List, Any

# Add parent directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import NLToSQLApp
from app.logging_setup import setup_logging, get_logger

# Set up logger
setup_logging("INFO")
logger = get_logger(__name__)

# Define a set of test questions with expected table usage and descriptions
TEST_QUESTIONS = [
    {
        "question": "How many customers are there?",
        "description": "Simple COUNT query",
        "expected_tables": ["customers"],
        "expected_output": "Count of total customers"
    },
    {
        "question": "List all products that cost more than $500",
        "description": "Table filter query",
        "expected_tables": ["products"],
        "expected_output": "Expensive products (laptop, smartphone)"
    },
    {
        "question": "What products did John Doe order?",
        "description": "Join query across customers, orders, and products",
        "expected_tables": ["customers", "orders", "products"],
        "expected_output": "Laptop, Headphones"
    },
    {
        "question": "What is the total value of all orders?",
        "description": "Aggregation query (SUM)",
        "expected_tables": ["orders"],
        "expected_output": "2320.00 (sum of all order total_amount values)"
    },
    {
        "question": "How many orders has each customer made?",
        "description": "GROUP BY query",
        "expected_tables": ["customers", "orders"],
        "expected_output": "John: 2, Jane: 1"
    },
    {
        "question": "What is the average price of products?",
        "description": "Simple average calculation",
        "expected_tables": ["products"],
        "expected_output": "Average product price"
    },
    {
        "question": "Which customer placed the most recent order?",
        "description": "Date ordering query",
        "expected_tables": ["customers", "orders"],
        "expected_output": "John Doe (May 10, 2023)"
    },
    {
        "question": "What is the total value of all products purchased by John Doe?",
        "description": "Complex join with multiple tables",
        "expected_tables": ["customers", "orders", "order_items", "products"],
        "expected_output": "1520.00"
    },
    {
        "question": "What is the most popular product by quantity ordered?",
        "description": "Aggregation and ordering",
        "expected_tables": ["products", "order_items"],
        "expected_output": "Headphones (ordered twice)"
    },
    {
        "question": "Which customer spent the most money on orders?",
        "description": "Customer spending analysis",
        "expected_tables": ["customers", "orders"],
        "expected_output": "John Doe (1520.00)"
    },
    {
        "question": "How many products are in each category?",
        "description": "Category distribution",
        "expected_tables": ["products"],
        "expected_output": "Electronics: 2, Accessories: 1, Office Supplies: 1"
    },
    {
        "question": "What orders were placed between January and April 2023?",
        "description": "Date range filtering",
        "expected_tables": ["orders"],
        "expected_output": "Orders from Q1 2023"
    }
]

def print_header(text: str):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def check_tables_in_query(sql_query: str, expected_tables: List[str]) -> bool:
    """Check if all expected tables appear in the SQL query."""
    sql_query = sql_query.lower()
    missing_tables = []
    
    for table in expected_tables:
        if table.lower() not in sql_query:
            missing_tables.append(table)
    
    return len(missing_tables) == 0, missing_tables

def run_demo_questions():
    """Run all demo questions and show results."""
    print_header("NL-to-SQL Demo Questions")
    print("This demo runs various natural language questions through the NL-to-SQL system")
    print("and shows the generated SQL queries and results.")
    
    # Initialize app
    app = NLToSQLApp(config_path="config.yml")
    
    # Seed database
    print("\nSeeding database with sample data...")
    app.seed_database()
    
    # Display schema
    print_header("Database Schema")
    schema_info = json.loads(app.get_schema_info())
    
    for table_name, table_info in schema_info["tables"].items():
        print(f"Table: {table_name}")
        print("Columns:")
        for column in table_info["columns"]:
            primary_key = " (PRIMARY KEY)" if column.get("primary_key") else ""
            print(f"  - {column['name']} ({column['type']}){primary_key}")
        print()

    # Run all test questions
    print_header("Running Test Questions")
    print(f"Running {len(TEST_QUESTIONS)} test questions...\n")
    
    results = []
    for i, test in enumerate(TEST_QUESTIONS, 1):
        question = test["question"]
        description = test["description"]
        expected_tables = test["expected_tables"]
        expected_output = test["expected_output"]
        
        print(f"Question {i}: {question}")
        print(f"Description: {description}")
        print(f"Expected to use tables: {', '.join(expected_tables)}")
        print(f"Expected output: {expected_output}")
        
        # Process the question
        start_time = time.time()
        response = app.process_question(question)
        processing_time = time.time() - start_time
        
        # Display SQL query
        sql_query = response["sql_query"]
        print(f"\nGenerated SQL ({processing_time:.2f}s):")
        print(f"  {sql_query}")
        
        # Check if all expected tables were used
        tables_match, missing_tables = check_tables_in_query(sql_query, expected_tables)
        if tables_match:
            print("\n✅ All expected tables found in query")
        else:
            print(f"\n❌ Missing tables in query: {', '.join(missing_tables)}")
        
        # Display results
        if response["error"]:
            print(f"\nError: {response['error']}")
            results.append({"question": question, "success": False, "error": response["error"]})
        else:
            print("\nResults:")
            if not response["results"]:
                print("  No results returned.")
            else:
                for j, result in enumerate(response["results"], 1):
                    print(f"  {j}. {result}")
            
            results.append({
                "question": question, 
                "success": True, 
                "tables_match": tables_match,
                "result_count": len(response["results"])
            })
        
        print("\n" + "-" * 80)
    
    # Display summary
    print_header("Test Summary")
    success_count = sum(1 for r in results if r["success"])
    tables_match_count = sum(1 for r in results if r.get("tables_match", False))
    
    print(f"Total questions: {len(TEST_QUESTIONS)}")
    print(f"Successful queries: {success_count} ({success_count/len(TEST_QUESTIONS)*100:.1f}%)")
    print(f"Queries using expected tables: {tables_match_count} ({tables_match_count/len(TEST_QUESTIONS)*100:.1f}%)")
    
    # Clean up
    app.close()
    print("\nDemo completed.")

if __name__ == "__main__":
    run_demo_questions() 
#!/usr/bin/env python3

"""
Test script to demonstrate the different SQL validation modes.
"""

import sys
import os
import json
from typing import Dict, List, Any

# Add parent directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import NLToSQLApp
from app.logging_setup import setup_logging, get_logger
import yaml

# Set up logger
setup_logging("INFO")
logger = get_logger(__name__)

def test_validation_mode(mode: str):
    """Test a specific validation mode."""
    print(f"\n{'='*80}")
    print(f"  Testing validation mode: {mode}")
    print(f"{'='*80}")
    
    # Create a temporary config file with the specified validation mode
    config = {
        "query_generator": {
            "validation_enabled": True,
            "validation_mode": mode,
            "max_retries": 2
        }
    }
    
    # Save the config to a temporary file
    temp_config_path = "temp_config.yml"
    with open(temp_config_path, "w") as f:
        yaml.dump(config, f)
    
    try:
        # Create app with the temporary config
        app = NLToSQLApp(config_path=temp_config_path)
        
        # Test with a valid query
        print("\nTesting with valid SQL:")
        question = "How many customers are there?"
        print(f"Question: {question}")
        response = app.process_question(question)
        print(f"SQL: {response['sql_query']}")
        print(f"Success: {response['success']}")
        print(f"Error: {response['error']}")
        
        # Test with an invalid SQL query (by manipulating the QueryGenerator output)
        print("\nTesting with invalid SQL:")
        # Override the generate method temporarily with a broken SQL query
        original_generate = app.query_generator.generate
        
        def mock_generate(question):
            if mode == "none":
                # With validation mode 'none', this should still execute but fail at the database level
                return "SELECT * FROMM customers WHERE name='INVALID"
            elif mode == "syntax_only":
                # With validation mode 'syntax_only', this should be caught at the validation step
                # but a query with invalid column should pass validation
                return "SELECT nonexistent_column FROM customers"
            else:  # full validation
                # With full validation, this query uses a column that doesn't exist, so it should be caught
                # The 'id' column exists, 'name' exists, but 'nonexistent_column' doesn't exist
                return "SELECT customer_id, name, nonexistent_column FROM customers"
        
        app.query_generator.generate = mock_generate
        
        question = "List all invalid queries"
        print(f"Question: {question}")
        response = app.process_question(question)
        print(f"SQL: {response['sql_query']}")
        print(f"Success: {response['success']}")
        print(f"Error: {response['error'] or 'None'}")
        
        # Restore original generate method
        app.query_generator.generate = original_generate
        
    finally:
        # Clean up
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)

def main():
    """Run validation mode tests."""
    # Test the different validation modes
    test_validation_mode("none")      # No validation
    test_validation_mode("syntax_only")  # Only syntax check
    test_validation_mode("full")      # Full validation (syntax + schema)

if __name__ == "__main__":
    main() 
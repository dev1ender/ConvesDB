"""
Main entry point for the RAG-POC application.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

from app.factory import ApplicationFactory
from app.logging_setup import setup_logging, get_logger

# Load environment variables
load_dotenv()

# Setup application logger
logger = get_logger(__name__)

def main():
    """Main function for CLI application."""
    # Set up logging
    setup_logging("INFO")
    logger.info("Starting NLToSQL CLI application")
    
    # Set up the application with configuration
    app = ApplicationFactory.create_app()
    logger.info("Application initialized")
    
    # Seed the database with sample data
    app.seed_database()
    
    # Print schema information
    logger.info("Retrieving database schema")
    print("Database Schema:")
    schema_info = json.loads(app.get_schema_info())
    for table_name, table_info in schema_info["tables"].items():
        print(f"\nTable: {table_name}")
        print("Columns:")
        for column in table_info["columns"]:
            print(f"  - {column['name']} ({column['type']})")
    
    # Process a sample question
    question = "How many orders did John Doe make?"
    logger.info(f"Processing sample question: '{question}'")
    print(f"\nQuestion: {question}")
    
    response = app.process_question(question)
    
    print(f"\nGenerated SQL: {response['sql_query']}")
    
    if response["error"]:
        logger.error(f"Query error: {response['error']}")
        print(f"Error: {response['error']}")
    else:
        print("\nResults:")
        if response["results"]:
            # Print headers
            headers = response["results"][0].keys()
            header_row = " | ".join(headers)
            print(header_row)
            print("-" * len(header_row))
            
            # Print rows
            for row in response["results"]:
                print(" | ".join(str(row[col]) for col in headers))
        else:
            print("No results")
    
    # Enter interactive mode if requested
    if "--interactive" in os.sys.argv:
        print("\nEntering interactive mode. Type 'exit' to quit.")
        while True:
            try:
                question = input("\nEnter a question: ")
                if question.lower() in ["exit", "quit"]:
                    break
                    
                response = app.process_question(question)
                
                print(f"\nGenerated SQL: {response['sql_query']}")
                
                if response["error"]:
                    print(f"Error: {response['error']}")
                else:
                    print("\nResults:")
                    if response["results"]:
                        # Print headers
                        headers = response["results"][0].keys()
                        header_row = " | ".join(headers)
                        print(header_row)
                        print("-" * len(header_row))
                        
                        # Print rows
                        for row in response["results"]:
                            print(" | ".join(str(row[col]) for col in headers))
                    else:
                        print("No results")
            except KeyboardInterrupt:
                print("\nExiting interactive mode.")
                break
            except Exception as e:
                print(f"Error: {str(e)}")
    
    # Close connections
    app.close()
    logger.info("Application shutdown")


if __name__ == "__main__":
    main() 
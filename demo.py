#!/usr/bin/env python3
"""
Demo script for the NLP-to-SQL system.
This script demonstrates how to use the system programmatically.
"""

import sys
import json
import argparse
import time
import os
from app.main import NLToSQLApp
from app.config_manager import ConfigManager
from app.logging_setup import setup_logging, get_logger, setup_logging_from_config
from dotenv import load_dotenv

load_dotenv()
# Set up logger for this module
logger = get_logger(__name__)

def print_header(text):
    """Print a header with the given text."""
    header = "\n" + "=" * 50 + f"\n  {text}\n" + "=" * 50 + "\n"
    print(header)
    logger.info(f"SECTION: {text}")
    return header

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="NLP-to-SQL Demo")
    parser.add_argument('-c', '--config', default="config.yml", help="Path to configuration file")
    parser.add_argument('-q', '--question', help="Question to process")
    parser.add_argument('--show-config', action='store_true', help="Display configuration")
    args, remaining_args = parser.parse_known_args()
    
    # Load configuration
    config_manager = ConfigManager(args.config)
    
    # Set up logging from configuration
    setup_logging_from_config(config_manager.config)
    
    # Now we can start logging
    logger.info("=" * 50)
    logger.info("Starting NLP-to-SQL DEMO application")
    logger.info("=" * 50)
    
    logger.debug("Command line arguments parsed")
    logger.info(f"Using configuration file: {args.config}")
    
    # Initialize the app with configuration
    print_header("Initializing NLToSQLApp")
    logger.debug("Creating NLToSQLApp instance")
    app = NLToSQLApp(config_path=args.config)
    
    # Show configuration if requested
    if args.show_config:
        logger.info("Displaying configuration as requested")
        print_header("Configuration")
        config = app.config_manager.config
        config_json = json.dumps(config, indent=2)
        print(config_json)
        logger.debug(f"Configuration displayed: {len(config_json)} chars")
    
    # Seed the database with sample data
    logger.info("Seeding database")
    print("Seeding database with sample data...")
    start_time = time.time()
    app.seed_database()
    logger.debug(f"Database seeding completed in {time.time() - start_time:.2f}s")
    
    # Get and display schema information
    print_header("Database Schema")
    logger.info("Retrieving and displaying database schema")
    start_time = time.time()
    schema_info = json.loads(app.get_schema_info())
    logger.debug(f"Schema retrieved in {time.time() - start_time:.2f}s")
    
    # Display schema in console
    for table_name, table_info in schema_info["tables"].items():
        print(f"Table: {table_name}")
        print("Columns:")
        for column in table_info["columns"]:
            primary_key = " (PRIMARY KEY)" if column.get("primary_key") else ""
            print(f"  - {column['name']} ({column['type']}){primary_key}")
        print()
    
    # Process a user question
    logger.info("Determining question to process")
    if args.question:
        # Use question from command line arguments
        question = args.question
        logger.info(f"Using question from command line argument: '{question}'")
    elif len(remaining_args) > 0:
        # Use question from remaining arguments
        question = " ".join(remaining_args)
        logger.info(f"Using question from remaining arguments: '{question}'")
    else:
        # Default questions
        questions = [
            "How many orders did John Doe make?",
            "What is the most expensive product?",
            "List all customers who ordered headphones",
            "What is the total value of all orders?",
            "How many products cost more than $500?"
        ]
        
        print_header("Example Questions")
        for i, q in enumerate(questions, 1):
            print(f"{i}. {q}")
        
        # Get user choice
        logger.info("Prompting user to select a question")
        try:
            choice = int(input("\nEnter question number (1-5) or 0 to enter your own: "))
            logger.debug(f"User selected choice: {choice}")
            
            if choice == 0:
                question = input("\nEnter your question: ")
                logger.info(f"User entered custom question: '{question}'")
            elif 1 <= choice <= len(questions):
                question = questions[choice-1]
                logger.info(f"User selected predefined question {choice}: '{question}'")
            else:
                question = questions[0]
                logger.info(f"Invalid choice, using default question: '{question}'")
        except (ValueError, IndexError):
            question = questions[0]
            logger.info(f"Error in choice input, using default question: '{question}'")
    
    print_header(f"Processing Question: {question}")
    
    # Process the question
    logger.info(f"Processing question: '{question}'")
    start_time = time.time()
    response = app.process_question(question)
    processing_time = time.time() - start_time
    logger.info(f"Question processed in {processing_time:.2f}s")
    
    # Display the results
    print(f"Generated SQL: {response['sql_query']}")
    print()
    
    if response["error"]:
        logger.error(f"Error processing question: {response['error']}")
        print(f"Error: {response['error']}")
    else:
        result_count = len(response["results"])
        logger.info(f"Query successful with {result_count} results")
        
        print("Results:")
        if not response["results"]:
            logger.info("No results returned from query")
            print("  No results returned.")
        else:
            for i, result in enumerate(response["results"], 1):
                print(f"  {i}. {result}")
    
    # Clean up
    logger.info("Demo completed, closing application")
    app.close()
    print("\nDemo completed.")
    logger.info("=" * 50)

if __name__ == "__main__":
    main() 
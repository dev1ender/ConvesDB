#!/usr/bin/env python3

"""
Test script to verify schema embeddings functionality.
This compares keyword-based vs. embedding-based table relevance detection.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SQLiteConnector
from app.schema_agent import SchemaAgent
from app.config_manager import ConfigManager
from app.logging_setup import setup_logging, get_logger

def print_header(text):
    """Print a header with the given text."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def main():
    # Set up logging
    setup_logging("INFO")
    logger = get_logger(__name__)
    logger.info("Testing schema agent embeddings")
    
    # Load configuration
    config_manager = ConfigManager("config.yml")
    
    # Connect to the database
    logger.info("Connecting to database")
    db_connector = SQLiteConnector("example.sqlite")
    db_connector.connect()
    
    # Make sure database has data
    db_connector.seed_database()
    
    # Create schema agent without embeddings
    logger.info("Creating schema agent without embeddings")
    schema_agent_keyword = SchemaAgent(db_connector)
    schema_agent_keyword.extract_schema()
    
    # Create schema agent with embeddings
    logger.info("Creating schema agent with embeddings")
    schema_agent_embedding = SchemaAgent(db_connector)
    schema_config = config_manager.get_schema_agent_config()
    embedding_model = schema_config.get("embedding_model", "local")
    schema_agent_embedding.set_embedding_model(embedding_model, schema_config)
    schema_agent_embedding.extract_schema()
    schema_agent_embedding.compute_embeddings()
    
    # Test queries to compare
    test_queries = [
        "How many orders did John Doe make?",
        "List all customers and their emails",
        "What is the most expensive product?",
        "Show me total sales by customer",
        "Which product has generated the most revenue?",
        "List all orders with their items",
        "What items were purchased by Jane Smith?"
    ]
    
    # Compare results
    print_header("COMPARING KEYWORD VS EMBEDDING TABLE MATCHING")
    
    for query in test_queries:
        print(f"\nQuery: \"{query}\"")
        
        # Get tables using keyword matching
        keyword_tables = schema_agent_keyword._get_relevant_tables_keyword(query)
        
        # Get tables using embedding matching
        embedding_tables = schema_agent_embedding._get_relevant_tables_semantic(query)
        
        print(f"  Keyword matching: {', '.join(keyword_tables) if keyword_tables else 'None'}")
        print(f"  Embedding matching: {', '.join(embedding_tables) if embedding_tables else 'None'}")
    
    # Clean up
    db_connector.close()
    logger.info("Test completed")

if __name__ == "__main__":
    main() 
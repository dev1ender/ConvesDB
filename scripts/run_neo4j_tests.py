#!/usr/bin/env python3
"""
Script to test Neo4j queries from questions_neo4j.py
"""

import os
import sys
import json
import datetime
import argparse
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.neo4j_connector import Neo4jConnector
from app.utils.logging_setup import setup_logging, get_logger
from scripts.questions_neo4j import questions

# Setup logger
setup_logging()
logger = get_logger(__name__)

def save_result_to_json(result, filename="neo4j_query_result.json"):
    """
    Save the query result to a JSON file.
    
    Args:
        result: The query result to save
        filename: The name of the file to save to
    """
    try:
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        filepath = os.path.join("logs", filename)
        
        with open(filepath, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"✅ Query result saved to {filepath}")
        return True
    except Exception as e:
        print(f"❌ Failed to save query result: {str(e)}")
        return False

def normalize_cypher(cypher_query):
    """
    Normalize Cypher query for comparison by removing extra whitespace
    and making it lowercase.
    
    Args:
        cypher_query: Cypher query string to normalize
        
    Returns:
        str: Normalized Cypher query
    """
    if not cypher_query:
        return ""
    
    # Convert to lowercase
    normalized = cypher_query.lower()
    
    # Normalize whitespace (replace multiple spaces with single space)
    normalized = ' '.join(normalized.split())
    
    return normalized

def verify_query_result(question_data, actual_result):
    """
    Verify the actual result against expected data and log the comparison.
    
    Args:
        question_data: Dictionary containing the question, expected Cypher, and expected result
        actual_result: The actual result returned by the application
        
    Returns:
        dict: Verification results including match status and comparison details
    """
    verification = {
        "question": question_data["question"],
        "expected_cypher": question_data.get("cypher", "Not provided"),
        "actual_cypher": actual_result.get("cypher_query", "Not provided"),
        "expected_result": question_data.get("expected_result", "Not provided"),
        "actual_result": actual_result.get("results", "Not provided"),
        "cypher_match": False,
        "result_match": False
    }
    
    # Compare Cypher queries using the normalize_cypher function
    expected_cypher = question_data.get("cypher", "")
    actual_cypher = actual_result.get("cypher_query", "")
    
    # Normalize both queries for comparison
    cypher_normalized_expected = normalize_cypher(expected_cypher)
    cypher_normalized_actual = normalize_cypher(actual_cypher)
    
    # Compare normalized queries
    verification["cypher_match"] = cypher_normalized_expected == cypher_normalized_actual
    
    # Compare results (basic comparison, may need refinement)
    expected_result = str(question_data.get("expected_result", "")).strip()
    actual_result_str = str(actual_result.get("results", "")).strip()
    
    # Simplified verification - check if expected result is contained in actual
    # This is a basic approach and might need to be improved for real use
    verification["result_match"] = expected_result in actual_result_str
    
    # Log verification results
    if verification["cypher_match"]:
        print(f"✅ Cypher Query matches expected")
    else:
        print(f"❌ Cypher Query mismatch:")
        print(f"  Expected: {expected_cypher}")
        print(f"  Actual:   {actual_cypher}")
    
    if verification["result_match"]:
        print(f"✅ Result matches expected")
    else:
        print(f"❌ Result mismatch:")
        print(f"  Expected: {expected_result}")
        print(f"  Actual:   {actual_result_str}")
    
    return verification

def save_verification_to_json(verification, filename="neo4j_verification_result.json"):
    """
    Save the verification result to a JSON file.
    
    Args:
        verification: The verification result to save
        filename: The name of the file to save to
    """
    try:
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        filepath = os.path.join("logs", filename)
        
        with open(filepath, 'w') as f:
            json.dump(verification, f, indent=2, default=str)
        
        print(f"✅ Verification result saved to {filepath}")
        return True
    except Exception as e:
        print(f"❌ Failed to save verification result: {str(e)}")
        return False

def execute_cypher_query(connector, cypher_query):
    """
    Execute a Cypher query using the Neo4j connector.
    
    Args:
        connector: Neo4j connector instance
        cypher_query: Cypher query to execute
        
    Returns:
        dict: The query result
    """
    start_time = datetime.datetime.now()
    try:
        results = connector.run(cypher_query)
        end_time = datetime.datetime.now()
        execution_time = (end_time - start_time).total_seconds() * 1000  # Convert to milliseconds
        
        return {
            "cypher_query": cypher_query,
            "results": results,
            "execution_time_ms": execution_time,
            "success": True
        }
    except Exception as e:
        end_time = datetime.datetime.now()
        execution_time = (end_time - start_time).total_seconds() * 1000
        
        return {
            "cypher_query": cypher_query,
            "error": str(e),
            "execution_time_ms": execution_time,
            "success": False
        }

def main():
    parser = argparse.ArgumentParser(description='Run Neo4j test queries')
    parser.add_argument('--uri', type=str, default='bolt://localhost:7687', help='Neo4j URI')
    parser.add_argument('--username', type=str, default='neo4j', help='Neo4j username')
    parser.add_argument('--password', type=str, default='password', help='Neo4j password')
    parser.add_argument('--database', type=str, default='neo4j', help='Neo4j database name')
    parser.add_argument('--question-index', type=int, default=0, help='Index of the question to test (default: 0)')
    parser.add_argument('--test-all', action='store_true', help='Test all questions')
    args = parser.parse_args()
    
    config = {
        "uri": args.uri,
        "username": args.username,
        "password": args.password,
        "database": args.database
    }
    
    # Initialize Neo4j connector
    connector = Neo4jConnector(config)
    connector.connect()
    
    try:
        if args.test_all:
            print("\n--- Running All Neo4j Test Questions ---")
            all_verifications = []
            
            for i, question_data in enumerate(questions):
                print(f"\n[{i+1}/{len(questions)}] Testing: {question_data['question']}")
                try:
                    # Execute the query
                    result = execute_cypher_query(connector, question_data["cypher"])
                    
                    # Verify the result
                    verification = verify_query_result(question_data, result)
                    all_verifications.append({
                        "index": i,
                        "verification": verification
                    })
                except Exception as e:
                    print(f"❌ Error processing question: {str(e)}")
                    all_verifications.append({
                        "index": i,
                        "error": str(e)
                    })
            
            # Save all verifications to a single file
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            save_verification_to_json(all_verifications, f"neo4j_all_verifications_{timestamp}.json")
            
            # Print summary
            success_count = sum(1 for v in all_verifications if "verification" in v and 
                              v["verification"]["cypher_match"] and v["verification"]["result_match"])
            print(f"\nVerification Summary: {success_count}/{len(questions)} tests passed")
        else:
            # Test a single question
            question_idx = args.question_index
            if question_idx < 0 or question_idx >= len(questions):
                print(f"❌ Invalid question index: {question_idx}. Must be between 0 and {len(questions)-1}")
                return
            
            question_data = questions[question_idx]
            print(f"\nProcessing question: {question_data['question']}\n")
            
            # Execute the query
            result = execute_cypher_query(connector, question_data["cypher"])
            
            # Verify the result
            print("\n--- Verification Results ---")
            verification = verify_query_result(question_data, result)
            
            # Save both the result and verification to JSON files
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            save_result_to_json(result, f"neo4j_query_result_{timestamp}.json")
            save_verification_to_json(verification, f"neo4j_verification_result_{timestamp}.json")
    
    finally:
        # Close the connector
        connector.close()

if __name__ == "__main__":
    main() 
import logging
import sys
import json
import os
import time
import datetime
import argparse
from app.factory import ApplicationFactory
from app.core.exceptions import InitializationError
from app.llm.factory import LLMFactory
from app.components.embedding.document_embedder import DocumentEmbedder
from app.core.component_registry import ComponentRegistry

def save_result_to_json(result, filename="query_result.json"):
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

def normalize_sql(sql_query):
    """
    Normalize SQL query for comparison by removing extra whitespace,
    making it lowercase, and removing trailing semicolons.
    
    Args:
        sql_query: SQL query string to normalize
        
    Returns:
        str: Normalized SQL query
    """
    if not sql_query:
        return ""
    
    # Convert to lowercase
    normalized = sql_query.lower()
    
    # Remove trailing semicolons
    normalized = normalized.rstrip(';')
    
    # Normalize whitespace (replace multiple spaces with single space)
    normalized = ' '.join(normalized.split())
    
    return normalized

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

def verify_query_result(question_data, actual_result, query_type="sql"):
    """
    Verify the actual result against expected data and log the comparison.
    
    Args:
        question_data: Dictionary containing the question and expected data
        actual_result: The actual result returned by the application
        query_type: Type of query, either "sql" or "cypher"
        
    Returns:
        dict: Verification results including match status and comparison details
    """
    if query_type == "sql":
        verification = {
            "question": question_data["question"],
            "expected_sql": question_data.get("sql", "Not provided"),
            "actual_sql": actual_result.get("sql_query", "Not provided"),
            "expected_result": question_data.get("expected_result", "Not provided"),
            "actual_result": actual_result.get("results", "Not provided"),
            "sql_match": False,
            "result_match": False
        }
        
        # Compare SQL queries using the normalize_sql function
        expected_sql = question_data.get("sql", "")
        actual_sql = actual_result.get("sql_query", "")
        
        # Normalize both queries for comparison
        sql_normalized_expected = normalize_sql(expected_sql)
        sql_normalized_actual = normalize_sql(actual_sql)
        
        # Compare normalized queries
        verification["sql_match"] = sql_normalized_expected == sql_normalized_actual
        
        # Compare results
        expected_result = str(question_data.get("expected_result", "")).strip()
        actual_result_str = str(actual_result.get("results", "")).strip()
        
        # Use actual_result field from questions if available for more exact comparison
        verification["result_match"] = expected_result in actual_result_str or question_data.get("actual_result", "") in actual_result_str
        
        # Log verification results
        if verification["sql_match"]:
            print(f"✅ SQL Query matches expected")
        else:
            print(f"❌ SQL Query mismatch:")
            print(f"  Expected: {expected_sql}")
            print(f"  Actual:   {actual_sql}")
            print(f"  Normalized expected: {sql_normalized_expected}")
            print(f"  Normalized actual:   {sql_normalized_actual}")
        
        if verification["result_match"]:
            print(f"✅ Result matches expected")
        else:
            print(f"❌ Result mismatch:")
            print(f"  Expected: {expected_result}")
            print(f"  Actual:   {actual_result_str}")
        
        return verification
    
    elif query_type == "cypher":
        verification = {
            "question": question_data["question"],
            "expected_cypher": question_data.get("cypher", "Not provided"),
            "actual_cypher": actual_result.get("cypher_query", "Not provided"),
            "expected_result": question_data.get("expected_result", "Not provided"),
            "actual_result": actual_result.get("results", "Not provided"),
            "cypher_match": False,
            "result_match": False
        }
        
        # Compare Cypher queries
        expected_cypher = question_data.get("cypher", "")
        actual_cypher = actual_result.get("cypher_query", "")
        
        # Normalize both queries for comparison
        cypher_normalized_expected = normalize_cypher(expected_cypher)
        cypher_normalized_actual = normalize_cypher(actual_cypher)
        
        # Compare normalized queries
        verification["cypher_match"] = cypher_normalized_expected == cypher_normalized_actual
        
        # Compare results
        expected_result = str(question_data.get("expected_result", "")).strip()
        actual_result_str = str(actual_result.get("results", "")).strip()
        
        # Simplified verification - check if expected result is contained in actual
        verification["result_match"] = expected_result in actual_result_str or question_data.get("actual_result", "") in actual_result_str
        
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
    
    else:
        raise ValueError(f"Unsupported query type: {query_type}")

def save_verification_to_json(verification, filename="verification_result.json"):
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

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Run the conversDB application')
    parser.add_argument('--test-all', action='store_true', help='Test all questions')
    parser.add_argument('--db-type', choices=['sqlite', 'neo4j'], default='sqlite', 
                        help='Database type to use (sqlite or neo4j)')
    parser.add_argument('--config-dir', default='config', help='Configuration directory')
    parser.add_argument('--question-index', type=int, default=0, 
                        help='Index of the question to test (default: 0)')
    parser.add_argument('--workflow', help='Specify the workflow to use')
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    try:
        # Set config directory from argument or environment
        config_dir = args.config_dir or os.environ.get("CONFIG_DIR", "config")
        
        # Set environment variables for workflow if specified
        if args.workflow:
            os.environ["DEFAULT_WORKFLOW"] = args.workflow
            print(f"\n✅ Set DEFAULT_WORKFLOW environment variable to: {args.workflow}")
        elif args.db_type == 'neo4j':
            os.environ["DEFAULT_WORKFLOW"] = "neo4j_workflow"
            print(f"\n✅ Set DEFAULT_WORKFLOW environment variable to: neo4j_workflow (based on --db-type)")
        
        # Create the application
        app = ApplicationFactory.create_app(config_dir=config_dir, run_health_checks=False)
        print("\n✅ Application initialized successfully!\n")

        # List available components
        components = ApplicationFactory.get_available_components(app)
        print("Available Components:")
        for comp_type, comp_ids in components.items():
            print(f"  {comp_type}: {comp_ids}")

        # List available workflows
        workflows = ApplicationFactory.get_available_workflows(app)
        print("\nAvailable Workflows:")
        for wf in workflows:
            print(f"  - {wf}")
            
        # Show current active workflow - get from config_loader
        current_workflow = app.config_loader.get_value("default_workflow", "default_workflow")
        if current_workflow in workflows:
            print(f"\n✅ Current active workflow: {current_workflow}")
        else:
            print(f"\n❌ Current workflow '{current_workflow}' not found in available workflows.")
        
        # Load appropriate questions based on db-type
        if args.db_type == 'sqlite':
            from scripts.questions_large_data import questions
            query_type = "sql"
            file_prefix = "sqlite"
        else:  # neo4j
            from scripts.questions_neo4j import questions
            query_type = "cypher"
            file_prefix = "neo4j"
        
        # Process a single question if --test-all is not specified
        if not args.test_all:
            question_idx = args.question_index
            if question_idx < 0 or question_idx >= len(questions):
                print(f"\n❌ Invalid question index: {question_idx}. Must be between 0 and {len(questions)-1}")
                sys.exit(1)
                
            sample_question_data = questions[question_idx]
            sample_question = sample_question_data["question"]
            
            print(f"\nProcessing question: {sample_question}\n")
            result = app.process_query(sample_question)
            
            # Verify the result against expected data
            print("\n--- Verification Results ---")
            verification = verify_query_result(sample_question_data, result, query_type)
            
            # Save both the result and verification to JSON files
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            save_result_to_json(result, f"{file_prefix}_query_result_{timestamp}.json")
            save_verification_to_json(verification, f"{file_prefix}_verification_result_{timestamp}.json")
        else:
            # Run all test questions
            print(f"\n--- Running All {args.db_type.upper()} Test Questions ---")
            all_verifications = []
            
            for i, question_data in enumerate(questions):
                print(f"\n[{i+1}/{len(questions)}] Testing: {question_data['question']}")
                try:
                    result = app.process_query(question_data["question"])
                    verification = verify_query_result(question_data, result, query_type)
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
            save_verification_to_json(all_verifications, f"{file_prefix}_all_verifications_{timestamp}.json")
            
            # Print summary
            if query_type == "sql":
                match_field = "sql_match"
            else:
                match_field = "cypher_match"
                
            success_count = sum(1 for v in all_verifications if "verification" in v and 
                              v["verification"].get(match_field, False) and v["verification"].get("result_match", False))
            print(f"\nVerification Summary: {success_count}/{len(questions)} tests passed")

        # Shutdown the application
        app.shutdown()
        print("\n✅ Application shutdown complete!\n")
    except InitializationError as e:
        print(f"\n❌ Initialization failed: {e}\n")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n") 
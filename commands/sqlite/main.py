import logging
import sys
import json
import os
import time
import datetime
from app.factory import ApplicationFactory
from app.core.exceptions import InitializationError
from app.llm.factory import LLMFactory

def verify_embeddings():
    """
    Verify that the embedding models can be initialized and used.
    """
    print("\nVerifying embedding models...")
    factory = LLMFactory()
    
    try:
        # Verify local huggingface embeddings
        provider = "local_huggingface"
        model = "sentence-transformers/all-MiniLM-L6-v2"
        print(f"Testing {provider} provider with {model}...")
        
        client = factory.get_embedding_client(provider, model_name=model)
        test_text = "This is a test sentence for embedding verification."
        embedding = client.embed_text(test_text)
        
        if embedding and len(embedding) > 0:
            print(f"✅ {provider} embeddings working with {len(embedding)} dimensions")
            return True
        else:
            print(f"❌ {provider} embeddings failed: Empty embedding returned")
            return False
    
    except Exception as e:
        print(f"❌ Embedding verification failed: {str(e)}")
        return False

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

def verify_query_result(question_data, actual_result):
    """
    Verify the actual result against expected data and log the comparison.
    
    Args:
        question_data: Dictionary containing the question, expected SQL, and expected result
        actual_result: The actual result returned by the application
        
    Returns:
        dict: Verification results including match status and comparison details
    """
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
    
    # Compare results (this is a basic comparison and may need refinement)
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
    logging.basicConfig(level=logging.INFO)
    try:
        # Verify embeddings first
        embeddings_ok = verify_embeddings()
        if not embeddings_ok and "--skip-embedding-check" not in sys.argv:
            print("Embedding verification failed. Use --skip-embedding-check to continue anyway.")
            if "--skip-embedding-check" not in sys.argv:
                sys.exit(1)
        
        # Create the application
        app = ApplicationFactory.create_app(run_health_checks=False)
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

        # --- Run a sample question from questions_large_data.py ---
        from scripts.questions_large_data import questions
        sample_question_idx = 0  # Index of the question to test
        sample_question_data = questions[sample_question_idx]
        sample_question = sample_question_data["question"]
        
        print(f"\nProcessing sample question: {sample_question}\n")
        result = app.process_query(sample_question)
        
        # Verify the result against expected data
        print("\n--- Verification Results ---")
        verification = verify_query_result(sample_question_data, result)
        
        # Save both the result and verification to JSON files
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        save_result_to_json(result, f"query_result_{timestamp}.json")
        save_verification_to_json(verification, f"verification_result_{timestamp}.json")
        
        # Run all test questions if --test-all flag is provided
        if "--test-all" in sys.argv:
            print("\n--- Running All Test Questions ---")
            all_verifications = []
            
            for i, question_data in enumerate(questions):
                print(f"\n[{i+1}/{len(questions)}] Testing: {question_data['question']}")
                try:
                    result = app.process_query(question_data["question"])
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
            save_verification_to_json(all_verifications, f"all_verifications_{timestamp}.json")
            
            # Print summary
            success_count = sum(1 for v in all_verifications if "verification" in v and 
                               v["verification"]["sql_match"] and v["verification"]["result_match"])
            print(f"\nVerification Summary: {success_count}/{len(questions)} tests passed")
        # --- End sample question ---

        # Shutdown the application
        app.shutdown()
        print("\n✅ Application shutdown complete!\n")
    except InitializationError as e:
        print(f"\n❌ Initialization failed: {e}\n")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n") 
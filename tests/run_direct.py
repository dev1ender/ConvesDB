#!/usr/bin/env python3
"""
Direct test runner that doesn't rely on pytest.
This is a workaround for the cmd.Cmd import error.
"""
import os
import sys
import sqlite3
import importlib
import traceback
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "large_test.sqlite")

def setup_db():
    """Set up the test database"""
    from scripts.seed_large_data import seed_database
    
    if not os.path.exists(DB_PATH) or os.environ.get("RESEED_DB") == "1":
        print(f"Seeding large test database at {DB_PATH}...")
        seed_database(DB_PATH)
    else:
        print(f"Using existing database at {DB_PATH}")
    
    return DB_PATH

def get_db_connection():
    """Get a database connection with Row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def discover_tests():
    """Discover all test functions in the large_test directory"""
    test_files = []
    for f in os.listdir(os.path.dirname(__file__)):
        if f.startswith("test_") and f.endswith(".py"):
            test_files.append(f[:-3])  # Remove .py extension
    
    test_functions = []
    for module_name in test_files:
        try:
            module = importlib.import_module(f"large_test.{module_name}")
            for name in dir(module):
                if name.startswith("test_") and callable(getattr(module, name)):
                    test_functions.append((module, name))
        except ImportError as e:
            print(f"Error importing {module_name}: {e}")
    
    return test_functions

def run_tests():
    """Run all discovered tests"""
    # Setup the database
    setup_db()
    
    # Create DB connection
    conn = get_db_connection()
    
    # Discover tests
    test_functions = discover_tests()
    
    # Run tests
    total = len(test_functions)
    passed = 0
    failed = 0
    failures = []
    
    print(f"\nRunning {total} tests...\n")
    
    for module, func_name in test_functions:
        func = getattr(module, func_name)
        print(f"Running {module.__name__}.{func_name}... ", end="")
        try:
            func(conn)
            print("PASS")
            passed += 1
        except Exception as e:
            print("FAIL")
            failed += 1
            failures.append((module.__name__, func_name, e))
            traceback.print_exc()
            print()
    
    # Print summary
    print("\n" + "="*60)
    print(f"SUMMARY: {passed} passed, {failed} failed, {total} total")
    
    if failures:
        print("\nFAILURES:")
        for module, func, error in failures:
            print(f"  {module}.{func}: {error}")
    
    # Close connection
    conn.close()
    
    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1) 
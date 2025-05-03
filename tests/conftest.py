import pytest
import sqlite3
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Database path
LARGE_TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "large_test.sqlite")

@pytest.fixture(scope="session")
def setup_large_test_db():
    """Create large test database for all tests"""
    from scripts.seed_large_data import seed_database
    
    # Only seed if database doesn't exist or is forced
    if not os.path.exists(LARGE_TEST_DB_PATH) or os.environ.get("RESEED_DB") == "1":
        print(f"Seeding large test database at {LARGE_TEST_DB_PATH}...")
        seed_database(LARGE_TEST_DB_PATH)
    else:
        print(f"Using existing database at {LARGE_TEST_DB_PATH}")
    
    yield LARGE_TEST_DB_PATH
    
    # No cleanup - we keep the DB for reuse
    # To clean up, manually delete the file or run with CLEAN_DB=1 env var
    if os.environ.get("CLEAN_DB") == "1":
        if os.path.exists(LARGE_TEST_DB_PATH):
            os.remove(LARGE_TEST_DB_PATH)

@pytest.fixture(scope="function")
def db_conn(setup_large_test_db):
    """Provide a database connection for each test"""
    conn = sqlite3.connect(setup_large_test_db)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close() 
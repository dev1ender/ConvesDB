#!/usr/bin/env python3
import pytest
import sys
import os

if __name__ == "__main__":
    # Add current directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Run all tests in the large_test directory
    pytest_args = ["-v", os.path.dirname(os.path.abspath(__file__))]
    
    # Add any command line arguments
    pytest_args.extend(sys.argv[1:])
    
    # Run the tests
    sys.exit(pytest.main(pytest_args)) 
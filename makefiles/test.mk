# Test related tasks

# Run all tests using pytest (default)
test: env-setup
	@echo "Running tests with pytest..."
	. .venv/bin/activate && . .env && python -m pytest tests/

# Run all tests using unittest discovery (if needed)
test-unittest: env-setup
	@echo "Running tests with unittest..."
	. .venv/bin/activate && . .env && python -m unittest discover tests

# Run all tests using the custom runner (run_tests.py)
test-custom: env-setup
	@echo "Running tests with custom runner (run_tests.py)..."
	. .venv/bin/activate && . .env && python tests/run_tests.py

# Run direct test runner (run_direct.py)
test-direct: env-setup
	@echo "Running direct test runner (run_direct.py)..."
	. .venv/bin/activate && . .env && python tests/run_direct.py

# Run a specific test file with pytest (example: test_demo.py)
test-demo: env-setup
	@echo "Running test_demo.py with pytest..."
	. .venv/bin/activate && . .env && python -m pytest tests/test_demo.py -v

test-demo-direct: env-setup
	@echo "Running test_demo_direct.py directly..."
	. .venv/bin/activate && . .env && python tests/test_demo_direct.py

# Run all tests in sequence (comprehensive testing)
test-all: env-setup
	@echo "Running ALL tests sequentially..."
	@echo "========================================"
	@echo "Step 1: Running pytest-based tests"
	@make test || true
	@echo "========================================"
	@echo "Step 2: Running custom test runner (run_tests.py)"
	@make test-custom || true
	@echo "========================================"
	@echo "Step 3: Running direct test runner (run_direct.py)"
	@make test-direct || true
	@echo "========================================"
	@echo "Step 4: Running test_demo.py with pytest"
	@make test-demo || true
	@echo "========================================"
	@echo "Step 5: Running test_demo_direct.py directly"
	@make test-demo-direct || true
	@echo "========================================"
	@echo "All tests completed! Check output for any failures." 
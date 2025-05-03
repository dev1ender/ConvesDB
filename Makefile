.PHONY: setup install setup-ollama run-cli run-api run-ui run-demo test test-embeddings test-validation-modes clean config-openai config-ollama env-setup schema-extract schema-enrich schema-embed schema-docs schema-pure

# Default target
all: setup

# Define environment setup
env-setup:
	@if [ ! -f .env ]; then \
		echo "⚠️ .env file not found. Creating from template..."; \
		cp env.example .env; \
	fi

# Create virtual environment and install dependencies
setup: install setup-ollama

# Install Python dependencies
install:
	@echo "Creating virtual environment and installing dependencies..."
	python -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt
	@echo "✅ Dependencies installed."

# Setup Ollama with Llama 3.2 3B model
setup-ollama: env-setup
	@echo "Setting up Ollama with Llama 3.2 3B model..."
	. .venv/bin/activate && . .env && ./setup_ollama.sh

# Run the CLI version
run-cli: env-setup
	@echo "Running CLI version..."
	. .venv/bin/activate && . .env && python -m app.main

# Run the API version
run-api: env-setup
	@echo "Running API version..."
	. .venv/bin/activate && . .env && python -m app.api

# Run the Streamlit UI version
run-ui: env-setup
	@echo "Running Streamlit UI..."
	. .venv/bin/activate && . .env && streamlit run app/streamlit_app.py

# Run the demo script
run-demo: env-setup
	@echo "Running demo script..."
	. .venv/bin/activate && . .env && python demo.py

# Run the demo with config display
run-demo-config: env-setup
	@echo "Running demo script with configuration display..."
	. .venv/bin/activate && . .env && python demo.py --show-config

# Run tests
test: env-setup
	@echo "Running tests..."
	. .venv/bin/activate && . .env && python -m unittest discover tests

# Run tests for embeddings
test-embeddings: env-setup
	@echo "Running tests for schema embeddings..."
	. .venv/bin/activate && . .env && python tests/test_schema_embeddings.py

# Run comprehensive NL-to-SQL tests
test-nlsql: env-setup
	@echo "Running NL-to-SQL tests..."
	. .venv/bin/activate && . .env && python tests/test_nlsql_queries.py

# Run demo questions with expected answers
run-demo-questions: env-setup
	@echo "Running demo questions with expected answers..."
	. .venv/bin/activate && . .env && python tests/demo_questions.py

# Check if Ollama is running
check-ollama: env-setup
	@if ! curl -s http://localhost:11434/api/tags &> /dev/null; then \
		echo "Ollama is not running. Starting Ollama..."; \
		ollama serve & \
		sleep 3; \
	else \
		echo "Ollama is already running."; \
	fi

# Create .env file from template if it doesn't exist
env: env-setup
	@echo "✅ Environment setup complete."

# Set configuration to use OpenAI
config-openai: env-setup
	@echo "Configuring to use OpenAI..."
	@if [ -z "$$OPENAI_API_KEY" ]; then \
		read -p "Enter your OpenAI API key: " api_key; \
		sed -i'' -e "s/provider: \"ollama\"/provider: \"openai\"/" config.yml; \
		echo "export OPENAI_API_KEY=$$api_key" >> .env; \
	else \
		sed -i'' -e "s/provider: \"ollama\"/provider: \"openai\"/" config.yml; \
	fi
	@echo "✅ Configuration updated to use OpenAI."

# Set configuration to use Ollama
config-ollama: env-setup
	@echo "Configuring to use Ollama..."
	sed -i'' -e "s/provider: \"openai\"/provider: \"ollama\"/" config.yml
	@echo "✅ Configuration updated to use Ollama."

# Clean up environment
clean:
	@echo "Cleaning up..."
	rm -rf .venv
	rm -rf __pycache__
	rm -rf app/__pycache__
	rm -rf extensions/__pycache__
	rm -rf tests/__pycache__
	rm -f example.sqlite
	@echo "✅ Cleaned."

# Run validation modes test
test-validation-modes: env-setup
	@echo "Running validation modes test..."
	. .venv/bin/activate && . .env && python tests/test_validation_modes.py

# Extract schema from database
schema-extract: env-setup
	@echo "Extracting database schema..."
	@mkdir -p schema
	. .venv/bin/activate && . .env && python app/schema_extractor.py --db example.sqlite --output-dir schema --output-file raw_schema.json
	@echo "✅ Schema extracted to schema/raw_schema.json"

# Enrich schema with additional information
schema-enrich: env-setup
	@echo "Enriching schema with descriptions and metadata..."
	@if [ ! -f schema/raw_schema.json ]; then \
		echo "⚠️ Raw schema not found. Run 'make schema-extract' first."; \
		exit 1; \
	fi
	. .venv/bin/activate && . .env && python app/schema_enricher.py --schema schema/raw_schema.json --db example.sqlite --output schema/enriched_schema.json
	@echo "✅ Schema enriched and saved to schema/enriched_schema.json"

# Generate embeddings for schema elements
schema-embed: env-setup
	@echo "Generating embeddings for schema elements..."
	@if [ ! -f schema/enriched_schema.json ]; then \
		echo "⚠️ Enriched schema not found. Run 'make schema-enrich' first."; \
		exit 1; \
	fi
	. .venv/bin/activate && . .env && python app/schema_embedder.py --schema schema/enriched_schema.json --model local --output schema/schema_embeddings.pkl
	@echo "✅ Schema embeddings generated and saved to schema/schema_embeddings.pkl"

# Run full schema documentation workflow
schema-docs: env-setup
	@echo "Generating complete schema documentation..."
	@mkdir -p schema
	. .venv/bin/activate && . .env && python app/create_schema.py --db example.sqlite --output-dir schema
	@echo "✅ Complete schema documentation generated in schema directory"

# Generate pure database-only schema with enum/option values
schema-pure: env-setup
	@echo "Generating pure database schema with enum/option values..."
	@mkdir -p schema
	. .venv/bin/activate && . .env && python schema_generator.py --db example.sqlite --output-dir schema --output-file pure_schema.json
	@echo "✅ Pure schema extracted to schema/pure_schema.json"

# Help target
help:
	@echo "Available commands:"
	@echo "  make setup            : Set up environment and dependencies"
	@echo "  make install          : Install Python dependencies"
	@echo "  make setup-ollama     : Set up Ollama with Llama 3.2 3B model"
	@echo "  make run-cli          : Run CLI version"
	@echo "  make run-api          : Run API version"
	@echo "  make run-ui           : Run Streamlit UI"
	@echo "  make run-demo         : Run interactive demo script"
	@echo "  make run-demo-config  : Run demo with configuration display"
	@echo "  make test             : Run tests"
	@echo "  make test-embeddings  : Run tests for embeddings"
	@echo "  make test-nlsql       : Run comprehensive NL-to-SQL tests"
	@echo "  make test-validation-modes : Run SQL validation modes test"
	@echo "  make run-demo-questions: Run demo questions with expected answers"
	@echo "  make check-ollama     : Check if Ollama is running and start if not"
	@echo "  make env              : Create .env file from template"
	@echo "  make config-openai    : Configure to use OpenAI"
	@echo "  make config-ollama    : Configure to use Ollama"
	@echo "  make clean            : Clean up environment"
	@echo "  make schema-extract   : Extract schema from database"
	@echo "  make schema-enrich    : Enrich schema with descriptions"
	@echo "  make schema-embed     : Generate embeddings for schema"
	@echo "  make schema-docs      : Run full schema documentation workflow"
	@echo "  make schema-pure      : Generate pure database schema with enum values"
	@echo "  make help             : Show this help message" 
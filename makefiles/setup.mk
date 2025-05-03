# Setup related tasks

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
	python3 -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt
	@echo "✅ Dependencies installed."

# Install test dependencies
install-test: install
	@echo "Installing pytest and test dependencies..."
	. .venv/bin/activate && pip install pytest pytest-cov pytest-asyncio fastapi httpx
	@echo "✅ Test dependencies installed."

# Setup Ollama with Llama 3.2 3B model
setup-ollama: env-setup
	@echo "Setting up Ollama with Llama 3.2 3B model..."
	. .venv/bin/activate && . .env && ./setup_ollama.sh

# Setup Local Llama 3.2 3B model for HuggingFace
setup-llama-local: env-setup
	@echo "Setting up local Llama 3.2 3B model for HuggingFace..."
	chmod +x setup_llama_local.sh
	. .venv/bin/activate && . .env && ./setup_llama_local.sh

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
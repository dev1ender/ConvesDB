#!/bin/bash

echo "Setting up Ollama with Llama 3.2 3B model..."

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "Ollama is not installed. Please install Ollama first:"
    echo "macOS: curl -fsSL https://ollama.com/install.sh | sh"
    echo "Linux: curl -fsSL https://ollama.com/install.sh | sh"
    exit 1
fi

# Check if Ollama service is running
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "Ollama service is not running. Starting Ollama service..."
    ollama serve &
    # Wait for service to start
    sleep 5
fi

# Pull the Llama 3.2 3B model
echo "Downloading Llama 3.2 3B model (this may take a while)..."
ollama pull llama3:3b

# Verify the model is available
if ollama list | grep -q "llama3:3b"; then
    echo "✅ Llama 3.2 3B model is now available!"
    
    # Copy env.example to .env if it doesn't exist
    if [ ! -f .env ]; then
        echo "Creating .env file from env.example..."
        cp env.example .env
        echo "✅ Configuration ready! The application will use Ollama with Llama 3.2 3B model."
    else
        echo "⚠️ .env file already exists. Make sure it contains:"
        echo "USE_OPENAI=false"
        echo "OLLAMA_MODEL=llama3:3b"
    fi
    
    echo ""
    echo "You can now run the application with:"
    echo "python -m app.main  # CLI version"
    echo "python -m app.api   # API version"
    echo "streamlit run app/streamlit_app.py  # UI version"
else
    echo "❌ Failed to download the model. Please try again or check the Ollama documentation."
fi 
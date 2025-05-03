#!/bin/bash

# Script to set up local Llama 3.2 3B model for HuggingFace

echo "Setting up local Llama 3.2 3B model..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install required packages
echo "Installing required packages..."
pip install -U torch transformers accelerate safetensors sentence-transformers

# Create model cache directory if it doesn't exist
MODEL_CACHE_DIR="$HOME/.cache/huggingface/hub"
mkdir -p "$MODEL_CACHE_DIR"

# Check GPU availability
if python -c "import torch; print(torch.cuda.is_available())" | grep -q "True"; then
    echo "GPU detected, will download models optimized for GPU."
    GPU_AVAILABLE=true
else
    echo "No GPU detected, will download models optimized for CPU."
    GPU_AVAILABLE=false
fi

# Download Llama 3.2 3B model
echo "Downloading Llama 3.2 3B model (this may take a while)..."
python -c "
from huggingface_hub import snapshot_download
import torch

model_id = 'meta-llama/Llama-3.2-3B'
try:
    # Download the model files
    snapshot_download(
        repo_id=model_id,
        local_dir_use_symlinks=False
    )
    print(f'✅ Successfully downloaded {model_id}')
except Exception as e:
    print(f'❌ Error downloading model: {str(e)}')
"

# Download sentence transformer model for embeddings
echo "Downloading sentence transformer model for embeddings..."
python -c "
from huggingface_hub import snapshot_download
import torch

model_id = 'sentence-transformers/all-MiniLM-L6-v2'
try:
    # Download the model files
    snapshot_download(
        repo_id=model_id,
        local_dir_use_symlinks=False
    )
    print(f'✅ Successfully downloaded {model_id}')
except Exception as e:
    print(f'❌ Error downloading model: {str(e)}')
"

# Test model loading
echo "Testing Llama 3.2 3B model loading..."
python -c "
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch

    print('Loading tokenizer...')
    tokenizer = AutoTokenizer.from_pretrained('meta-llama/Llama-3.2-3B')
    
    print('Loading model...')
    model_kwargs = {}
    if torch.cuda.is_available():
        model_kwargs['device_map'] = 'auto'
    else:
        model_kwargs['load_in_4bit'] = True
        model_kwargs['device_map'] = 'auto'
    
    model = AutoModelForCausalLM.from_pretrained('meta-llama/Llama-3.2-3B', **model_kwargs)
    
    print('✅ Model loaded successfully!')
except Exception as e:
    print(f'❌ Error loading model: {str(e)}')
"

# Copy env.example to .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from env.example..."
    cp env.example .env
    echo "HUGGINGFACE_LOCAL=true" >> .env
    echo "✅ Configuration ready! The application will use local HuggingFace with Llama 3.2 3B model."
else
    echo "⚠️ .env file already exists. Make sure it contains:"
    echo "HUGGINGFACE_LOCAL=true"
fi

echo ""
echo "You can now run the application with:"
echo "python -m app.main  # CLI version"
echo "python -m app.api   # API version"
echo "streamlit run app/streamlit_app.py  # UI version"

# Make the script executable
chmod +x setup_llama_local.sh 
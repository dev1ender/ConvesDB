#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}   NLP-to-SQL System Setup             ${NC}"
echo -e "${GREEN}=========================================${NC}"

# Check if make is installed
if ! command -v make &> /dev/null; then
    echo -e "${RED}Error: 'make' is not installed.${NC}"
    echo "Please install 'make' to continue."
    exit 1
fi

# Setup steps
echo -e "\n${YELLOW}Step 1: Setting up environment and installing dependencies${NC}"
make install

echo -e "\n${YELLOW}Step 2: Creating .env file${NC}"
make env

# Ask user whether to use OpenAI or Ollama
echo -e "\n${YELLOW}Step 3: Choose LLM provider${NC}"
echo "Which LLM provider would you like to use?"
echo "1. OpenAI (requires API key)"
echo "2. Ollama with Llama 3.2 3B (local, no API key required)"
read -p "Enter your choice (1/2) [default: 2]: " choice

if [ "$choice" = "1" ]; then
    # Configure OpenAI
    read -p "Enter your OpenAI API key: " openai_key
    
    # Update .env file
    sed -i'' -e "s/USE_OPENAI=false/USE_OPENAI=true/" .env
    sed -i'' -e "s/OPENAI_API_KEY=your_openai_api_key_here/OPENAI_API_KEY=$openai_key/" .env
    
    echo -e "${GREEN}✅ OpenAI configured successfully!${NC}"
else
    # Configure Ollama
    echo -e "${YELLOW}Setting up Ollama with Llama 3.2 3B model...${NC}"
    make setup-ollama
fi

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}   Setup Complete!                     ${NC}"
echo -e "${GREEN}=========================================${NC}"
echo -e "\nYou can now run the application using:"
echo -e "${YELLOW}make run-cli${NC} - Run the command-line interface"
echo -e "${YELLOW}make run-api${NC} - Run the API server"
echo -e "${YELLOW}make run-ui${NC} - Run the Streamlit UI"
echo
echo -e "For more commands, run: ${YELLOW}make help${NC}" 
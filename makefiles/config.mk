# Configuration related tasks

# Configure system to use OpenAI
config-openai:
	@echo "Configuring system to use OpenAI..."
	@sed -i.bak 's/provider: ".*"/provider: "openai"/' config.yml
	@echo "✅ System configured to use OpenAI."

# Configure system to use Ollama
config-ollama:
	@echo "Configuring system to use Ollama..."
	@sed -i.bak 's/provider: ".*"/provider: "ollama"/' config.yml
	@echo "✅ System configured to use Ollama."

# Configure system to use HuggingFace
config-huggingface:
	@echo "Configuring system to use HuggingFace..."
	@sed -i.bak 's/provider: ".*"/provider: "huggingface"/' config.yml
	@echo "✅ System configured to use HuggingFace."

# Configure system to use local Llama model
config-local-llama:
	@echo "Configuring system to use local Llama model..."
	@sed -i.bak 's/provider: ".*"/provider: "local_huggingface"/' config.yml
	@echo "✅ System configured to use local Llama model." 
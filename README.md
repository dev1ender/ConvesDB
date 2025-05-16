# conversDB

A production-grade platform that enables users to communicate, chat, and interact with any kind of database or datastore using natural language processing (NLP).

## Overview

conversDB transforms how users interact with databases by enabling natural language conversations with data. It interprets questions, generates appropriate SQL or Cypher queries, executes them securely, and returns formatted results - all through simple conversational language.

## Features

- **Natural Language to SQL**: Convert plain English questions into SQL queries
- **Schema Detection**: Automatically detect relevant tables and columns in the database
- **Semantic Schema Matching**: Uses embeddings to find relevant tables based on semantic similarity
- **Relationship Tracking**: Understands and utilizes database relationships for complex queries
- **SQL Validation**: Validates generated SQL to ensure it adheres to the database schema
- **Query Execution**: Executes the generated SQL queries and formats the results
- **Multi-LLM Support**: Support for OpenAI, Ollama, and HuggingFace
- **Configuration System**: Centralized configuration with YAML
- **Comprehensive Logging**: Detailed logging throughout the application
- **Robust Testing**: Unit tests, integration tests, and demo tests

## System Architecture

The project follows a modular architecture with clean separation of concerns:

- **Interfaces Layer**: Abstract interfaces defining the contract for all components
- **Database Layer**: Handles database connections and queries (SQLite, PostgreSQL)
- **LLM Services Layer**: Integrates with multiple LLM providers
- **Agent Layer**: Core business logic components for schema and query generation
- **Configuration Layer**: Manages application config
- **Core Application**: Main application and factory
- **Extensions**: Pluggable extensions for additional functionality

## Project Roadmap

### Current Phase
- ✅ Core SQL generation functionality
- ✅ SQLite and PostgreSQL support
- ✅ Basic documentation
- ✅ Test framework

### Short-term Goals (Next 3 months)
- 🔄 Improve semantic matching accuracy
- 🔄 Add MySQL support
- 🔄 Create comprehensive documentation
- 🔄 Improve test coverage

### Mid-term Goals (3-6 months)
- 📋 Add MongoDB support
- 📋 Implement web interface improvements
- 📋 Create plugin system
- 📋 Improve error handling and feedback

### Long-term Vision
- 📋 Support for more complex analytical queries
- 📋 Integration with BI tools
- 📋 Enhanced multi-step reasoning
- 📋 Community-driven schema enrichment
- 📋 Support for domain-specific language customization

## Installation

### Prerequisites

- Python 3.9+
- [Ollama](https://ollama.ai/) (for local LLM inference) or OpenAI API key

### Setup Instructions

```bash
# Clone the repository
git clone https://github.com/yourusername/conversDB.git
cd conversDB

# Install dependencies
pip install -r requirements.txt

# Create .env file from template
cp env.example .env
```

## Configuration

### Basic Configuration

Configure the system through `config.yml`:

```yaml
# Database Settings
database:
  type: "sqlite"  # sqlite, postgres
  path: "example.sqlite"

# LLM Provider Settings
llm:
  provider: "ollama"  # ollama, openai, huggingface
```

### Advanced Configuration

For detailed configuration options, see the [Configuration Guide](docs/configuration.md).

## Usage

### Command Line Interface

```bash
# Run the CLI version
python -m app.main
```

### API Server

```bash
# Run the API server
python -m app.api
```

### Web Interface

```bash
# Run the Streamlit UI
python -m app.ui
```

## Code Example

```python
from app.main import NLToSQLApp

# Initialize the app
app = NLToSQLApp()

# Process a natural language question
response = app.process_question("How many orders did John Doe make?")

# Print the results
print(response["sql_query"])
print(response["results"])

# Clean up
app.close()
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT License](LICENSE)

## Acknowledgments

- LangChain for the LLM framework
- FastAPI and Streamlit for the web interfaces
- OpenAI and Meta for the LLM models 
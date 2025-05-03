# RAG-POC: Modular NLP-to-SQL System

A modular system that converts natural language questions into SQL queries, executes them, and returns the results. Built with SOLID principles and modular design.

## Features

1. **Natural Language to SQL**: Convert plain English questions into SQL queries
2. **Schema Detection**: Automatically detect relevant tables and columns in the database
3. **Semantic Schema Matching**: Uses embeddings to find relevant tables based on semantic similarity
4. **Relationship Tracking**: Understands and utilizes database relationships for complex queries
5. **SQL Validation**: Validates generated SQL to ensure it adheres to the database schema
6. **Query Execution**: Executes the generated SQL queries and formats the results
7. **Multi-LLM Support**: Support for both OpenAI and local LLMs (Ollama)
8. **Configuration System**: Centralized configuration with YAML
9. **Comprehensive Logging**: Detailed logging throughout the application
10. **Robust Testing**: Unit tests, integration tests, and demo tests

## Architecture

This project follows a SOLID, modular architecture with clear separation of concerns:

### Core Components

1. **Interfaces Layer**: Abstract interfaces defining the contract for all components
   - `app/interfaces/`: Contains all interface definitions following Interface Segregation Principle
   - `app/interfaces/database.py`: Database connector interfaces
   - `app/interfaces/llm.py`: LLM and embedding client interfaces
   - `app/interfaces/agents.py`: Agent interfaces for schema, prompt, and query components
   - `app/interfaces/config.py`: Configuration management interfaces
   - `app/interfaces/app.py`: Main application interface

2. **Database Layer**: Handles database connections and queries
   - `app/database/`: Database connector implementations
   - `app/database/sqlite_connector.py`: SQLite implementation
   - Extensible to support other databases via the common interface

3. **LLM Services Layer**: Integrates with LLM providers
   - `app/llm/`: LLM client implementations
   - `app/llm/factory.py`: Factory for creating LLM and embedding clients
   - `app/llm/embedding/`: Embedding client implementations
   - OpenAI and Ollama implementations in extensions

4. **Agent Layer**: Core business logic components
   - `app/agents/`: Agent implementations
   - `app/agents/schema_agent.py`: Extracts and manages database schema
   - `app/agents/prompt_agent.py`: Builds effective prompts for LLMs
   - `app/agents/query_generator.py`: Generates SQL queries from natural language
   - `app/agents/query_executor.py`: Safely executes SQL queries

5. **Configuration Layer**: Manages application config
   - `app/config/`: Configuration management implementations
   - `app/config/config_manager.py`: YAML-based configuration

6. **Core Application**: Main application and factory
   - `app/factory.py`: Factory for creating the application and components
   - `app/application.py`: Main application implementation
   - `app/main.py`: Entry point for CLI application

7. **Extensions**: Pluggable extensions
   - `extensions/llm_providers.py`: LLM client implementations for various providers
   - `extensions/database_connectors.py`: Additional database connectors

### Design Patterns Used

- **Factory Pattern**: For creating components with proper dependencies
- **Strategy Pattern**: For interchangeable LLM and database implementations
- **Dependency Injection**: For loose coupling between components
- **Interface Segregation**: Clear interfaces for each component type
- **Single Responsibility**: Each class has a single, well-defined purpose

## SQL Validation Modes

The system offers flexible SQL validation options that can be configured in `config.yml`:

```yaml
# Query Generator Settings
query_generator:
  validation_enabled: true      # Enable/disable validation completely
  validation_mode: "full"       # Options: "full", "syntax_only", "none"
  max_retries: 3                # Number of retry attempts for invalid queries
```

### Validation Modes

1. **Full Validation (`full`)**: Checks both SQL syntax and schema correctness
   - Validates table existence
   - Validates column existence in referenced tables
   - Validates table alias resolution
   - Catches errors before database execution

2. **Syntax-Only Validation (`syntax_only`)**: Only checks basic SQL syntax
   - Faster validation with less overhead
   - Catches syntax errors like missing keywords or unbalanced quotes
   - Doesn't validate against schema
   - Useful for rapid prototyping

3. **No Validation (`none`)**: Skips all validation
   - Maximum performance
   - Relies on database engine to catch errors
   - Use only in trusted environments

The validation mode can be useful in different scenarios - use full validation during development, syntax-only for better performance, or none for maximum speed in production with trusted queries.

## Getting Started

### Prerequisites

- Python 3.9+
- [Ollama](https://ollama.ai/) (for local LLM inference) or OpenAI API key

### Installation

1. Clone the repository
   ```bash
   git clone <repository-url>
   cd rag-poc
   ```

2. Create environment and install dependencies
   ```bash
   make setup
   ```

3. Set up environment variables
   ```bash
   # Copy example environment file
   cp env.example .env
   
   # Edit .env with your configuration
   # For OpenAI
   # OPENAI_API_KEY=your-api-key
   
   # For Ollama (default)
   # OLLAMA_HOST=http://localhost:11434
   ```

4. Set up Ollama (if using local LLM)
   ```bash
   make setup-ollama
   ```

### Running the Demo

Run the interactive CLI demo:
```bash
make run-demo
```

Or try a specific question:
```bash
python demo.py "What products did John Doe order?"
```

### Using the API

Start the FastAPI server:
```bash
make run-api
```

The API will be available at http://localhost:8000/docs

### Using the UI

Start the Streamlit UI:
```bash
make run-ui
```

The UI will be available at http://localhost:8501

## Configuration

The system uses a YAML configuration file (`config.yml`) to manage all settings:

### Database Configuration

```yaml
database:
  type: "sqlite"  # sqlite, postgres
  path: "example.sqlite"
  seed_on_startup: true
  
  # PostgreSQL connection (if using postgres)
  connection_string: "postgresql://username:password@localhost:5432/database"
```

### LLM Provider Configuration

```yaml
llm:
  provider: "ollama"  # ollama, openai
  
  # OpenAI settings
  openai:
    model: "gpt-3.5-turbo"
    api_key: "${OPENAI_API_KEY}"  # Uses environment variable
    
  # Ollama settings
  ollama:
    model: "llama3:3b"
    host: "http://localhost:11434"
```

You can also use these commands to quickly switch between providers:

```bash
# Switch to OpenAI
make config-openai

# Switch to Ollama
make config-ollama
```

## Extending the System

The modular design makes it easy to extend the system:

### Adding a New Database Connector

1. Create a new connector class that implements `DatabaseConnector`
2. Register it in the factory or extensions module
3. Update configuration to use the new connector

### Adding a New LLM Provider

1. Create a new client class that implements `LLMClient`
2. Add it to the extensions or create a new module
3. Update the factory to recognize the new provider
4. Update configuration to use the new provider

### Adding New Capabilities

1. Define new interfaces in the interfaces layer
2. Implement the interfaces in appropriate modules
3. Update the factory to create instances of the new components
4. Integrate with the main application flow

## Running Tests

Run the test suite:
```bash
make test
```

## Detailed Setup

### Prerequisites

- Python 3.8+
- Pip package manager
- Make (for using the provided Makefile)
- (Optional) OpenAI API key for using GPT models
- (Optional) Ollama for local LLM deployment
- (Optional) PostgreSQL for advanced database features

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd rag-poc
   ```

2. Use the provided Makefile to set up the environment:
   ```
   # Full setup (environment + dependencies + Ollama)
   make setup
   
   # Or individual steps:
   make install      # Install Python dependencies
   make setup-ollama # Set up Ollama with Llama 3.2 3B
   make env          # Create .env file from template
   ```

3. Configure your system through `config.yml` file:
   ```yaml
   # Database Settings
   database:
     type: "sqlite"  # sqlite, postgres
     path: "example.sqlite"
   
   # LLM Provider Settings
   llm:
     provider: "ollama"  # ollama, openai
   ```

### Configuration

The system uses a YAML configuration file (`config.yml`) to manage all settings:

#### Database Configuration

```yaml
database:
  type: "sqlite"  # sqlite, postgres
  path: "example.sqlite"
  seed_on_startup: true
  
  # PostgreSQL connection (if using postgres)
  connection_string: "postgresql://username:password@localhost:5432/database"
```

#### LLM Provider Configuration

```yaml
llm:
  provider: "ollama"  # ollama, openai
  
  # OpenAI settings
  openai:
    model: "gpt-3.5-turbo"
    api_key: "${OPENAI_API_KEY}"  # Uses environment variable
    
  # Ollama settings
  ollama:
    model: "llama3:3b"
    host: "http://localhost:11434"
```

You can also use these commands to quickly switch between providers:

```bash
# Switch to OpenAI
make config-openai

# Switch to Ollama
make config-ollama
```

### Using Ollama with Llama 3.2 3B

To use Llama 3.2 3B with Ollama:

1. Install Ollama:
   ```
   # macOS / Linux
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. Set up Ollama with the Llama model:
   ```
   make setup-ollama
   ```

   Or manually:
   ```
   # Start Ollama service
   ollama serve
   
   # In another terminal, pull the model
   ollama pull llama3:3b
   
   # Set up environment
   cp env.example .env
   ```

## Running the Application

Use the Makefile to run the application in different modes:

```bash
# Run the CLI version
make run-cli

# Run the API server
make run-api

# Run the Streamlit UI
make run-ui

# Run the interactive demo
make run-demo

# Run the demo with configuration display
make run-demo-config

# Run tests
make test

# Show all available commands
make help
```

## Interactive Demo

The project includes an interactive demo script that shows how to use the system. Run it with:

```bash
make run-demo
```

Or directly:

```bash
python demo.py
```

You can also pass a question directly as a command-line argument:

```bash
python demo.py "How many orders did John Doe make?"
```

To display the current configuration:

```bash
python demo.py --show-config
```

The demo will:
1. Initialize the system
2. Show the database schema
3. Let you choose from example questions or enter your own
4. Process the question and display the SQL query and results

## Example Usage

```python
from app.main import NLToSQLApp

# Initialize the app with custom configuration
app = NLToSQLApp(config_path="my_config.yml")

# Seed the database with sample data
app.seed_database()

# Process a natural language question
response = app.process_question("How many orders did John Doe make?")

# Print the generated SQL query
print(response["sql_query"])

# Print the results
print(response["results"])

# Clean up
app.close()
```

## Extending the System

### Adding New Database Connectors

1. Create a new connector in `extensions/database_connectors.py`
2. Implement the `DatabaseConnector` interface
3. Add required methods: `connect()`, `seed_database()`, `get_table_names()`, `get_table_schema()`, `run()`
4. Update your config.yml file to use the new database type

Example PostgreSQL connector is included in the project.

### Adding New LLM Providers

1. Create a new provider in `extensions/llm_providers.py`
2. Implement the `LLMClient` interface
3. Add required methods: `generate()`
4. Update your config.yml file to use the new provider

## RAG Capabilities

The system utilizes Retrieval-Augmented Generation (RAG) techniques for more accurate SQL query generation:

### Schema-Based RAG

The SchemaAgent component uses embeddings to semantically match natural language questions to relevant database tables and columns:

```yaml
# Schema Agent Settings in config.yml
schema_agent:
  cache_enabled: true
  embedding_model: "local"  # local, openai
  embedding_settings:
    use_semantic_matching: true   # Whether to use semantic matching
    similarity_threshold: 0.6     # Minimum similarity score
    max_tables: 5                 # Maximum number of tables
    include_column_matches: true  # Include columns in matching
```

The embedding-based matching offers several advantages over simple keyword matching:

1. **Semantic Understanding**: Recognizes related concepts even when exact keywords aren't present
2. **Relevance Ranking**: Prioritizes tables and columns by similarity score
3. **Contextual Awareness**: Understands the intent of the question beyond keyword presence
4. **Fallback Mechanism**: Automatically falls back to keyword matching if semantic matching fails

You can choose between different embedding models:
- `local`: Uses a lightweight Sentence Transformers model (all-MiniLM-L6-v2)
- `openai`: Uses OpenAI's embedding model (requires API key)

## Testing

The project includes comprehensive testing to ensure the accuracy and reliability of the NL-to-SQL conversions:

### Test Types

1. **Embeddings Tests**: Verify the semantic matching capabilities of the schema agent
   ```bash
   make test-embeddings
   ```

2. **NL-to-SQL Unit Tests**: Run automated tests for different query types
   ```bash
   make test-nlsql
   ```

3. **Demo Questions**: Run a collection of example questions with expected answers
   ```bash
   make run-demo-questions
   ```

### Test Coverage

The tests cover various aspects of the system:

- Simple queries (COUNT, filtering)
- Table joins and relationships
- Aggregation queries (SUM, AVG, etc.)
- GROUP BY operations
- ORDER BY and limiting results
- Complex multi-table queries
- Date filtering
- Customer-specific queries

These tests help verify that the RAG-based semantic matching correctly identifies relevant tables and that the generated SQL adheres to the database schema.

## License

[MIT License](LICENSE)

## Acknowledgments

- LangChain for the LLM framework
- FastAPI and Streamlit for the web interfaces
- OpenAI and Meta for the LLM models

# Database Schema Documentation Tools for LLM Reasoning

This project provides a set of tools to extract, enrich, and embed database schema information for improved LLM reasoning capabilities in database applications.

## Overview

Working with databases through natural language requires LLMs to understand the underlying schema - tables, columns, relationships, and constraints. These tools generate comprehensive schema documentation with rich metadata designed specifically for LLM consumption.

The toolkit includes three main components:

1. **Schema Extractor**: Extracts raw schema information from a database
2. **Schema Enricher**: Adds human-readable descriptions and LLM-friendly metadata 
3. **Schema Embedder**: Generates embeddings for semantic search capabilities

## Installation

### Requirements

- Python 3.8+
- SQLite database (support for other databases can be added)
- Required Python packages are in `requirements.txt`

```bash
# Clone the repository
git clone <repository-url>

# Install dependencies
pip install -r requirements.txt
```

## Usage

### 1. Extract Schema

The Schema Extractor pulls raw schema information from a database and generates a structured JSON file:

```bash
python app/schema_extractor.py --db example.sqlite --output-dir schema --output-file schema.json
```

This generates a comprehensive schema JSON file with:
- Tables, columns, and data types
- Primary keys and foreign keys
- Constraints and indexes
- Views and their definitions
- Placeholder fields for descriptions and other metadata

### 2. Enrich Schema

The Schema Enricher adds additional context and information to the extracted schema:

```bash
python app/schema_enricher.py --schema schema/schema.json --db example.sqlite
```

This adds:
- Automatically generated descriptions for tables and columns
- Sample data values (if database is available)
- Inferred semantic types for columns
- Important column identification
- Common query patterns based on schema structure

You can further enhance the enriched schema by manually editing it to add:
- More accurate descriptions
- Business purpose information
- Common use cases
- Relationship cardinality
- And more

### 3. Generate Embeddings

The Schema Embedder creates vector embeddings for schema elements to support semantic search:

```bash
python app/schema_embedder.py --schema schema/schema_enriched.json --model local
```

Options:
- `--model`: Choose between "local" or "openai" embeddings
- `--openai-key`: Your OpenAI API key (if using OpenAI embeddings)
- `--query`: Test a search query against the embeddings

## Schema JSON Structure

The generated schema JSON has a structure optimized for both human readability and LLM reasoning:

```json
{
  "metadata": {
    "generated_at": "2023-06-15T12:34:56.789012",
    "version": "1.0",
    "database_type": "sqlite",
    "tables_count": 10,
    "views_count": 5,
    "relationships_count": 15,
    "index_count": 25
  },
  "tables": {
    "customers": {
      "columns": [
        {
          "name": "customer_id",
          "type": "INTEGER",
          "nullable": false,
          "default_value": null,
          "description": "Primary key identifier for the customers table.",
          "example_values": ["1", "2", "3"],
          "semantic_type": "identifier",
          "primary_key": true
        },
        // Other columns...
      ],
      "primary_key": "customer_id",
      "foreign_keys": [],
      "check_constraints": [],
      "indexes": [
        {
          "name": "idx_customers_email",
          "columns": ["email"],
          "unique": true,
          "purpose": "Ensures email uniqueness and speeds up customer lookup by email"
        }
      ],
      "approximate_row_count": 1000,
      "description": "Contains information about registered customers.",
      "business_purpose": "Used to store and manage customer data for sales and support.",
      "llm_hints": {
        "important_columns": ["customer_id", "email", "name"],
        "common_filters": ["status", "registration_date"],
        "common_sorts": ["registration_date", "last_login_date"]
      }
    }
    // Other tables...
  },
  "views": {
    // Views with similar structure...
  },
  "relationships": [
    {
      "from_table": "orders",
      "from_column": "customer_id",
      "to_table": "customers",
      "to_column": "customer_id",
      "relationship_type": "many_to_one",
      "description": "Links orders to their respective customers.",
      "cardinality": "N:1"
    }
    // Other relationships...
  ],
  "llm_reasoning_hints": {
    "join_paths": [
      {
        "path": [
          {"table": "orders", "column": "customer_id"},
          {"table": "customers", "column": "customer_id"}
        ],
        "description": "Join from orders to customers",
        "usage": "Use to get customer details for each order"
      }
      // Other join paths...
    ],
    "common_query_patterns": [
      {
        "name": "Get all customers",
        "pattern": "SELECT * FROM customers",
        "description": "Retrieve all records from customers table"
      }
      // Other patterns...
    ],
    "embedding_options": {
      "similarity_threshold": 0.6,
      "max_tables": 5,
      "include_column_matches": true,
      "include_views": true
    }
  }
}
```

## Using with LLMs

The generated schema documentation and embeddings can be used with LLMs in several ways:

1. **Direct Embedding**: Include the full schema JSON directly in your prompts when working with capable models (e.g., GPT-4)

2. **RAG Approach**: Use the embeddings for semantic search to dynamically retrieve relevant schema elements based on user queries

3. **Context Building**: Programmatically construct targeted context about relevant tables and relationships based on the query

4. **Schema Agent**: Implement a dedicated schema agent that provides schema information to other LLM components

## Customization

These tools can be customized in various ways:

- Add support for other database types (PostgreSQL, MySQL, etc.) by creating new connectors
- Implement domain-specific description generators for your schema
- Extend the enrichment with additional metadata relevant for your use case
- Use different embedding models for varying levels of semantic understanding

## License

[Your license information]

## Contact

[Your contact information] 
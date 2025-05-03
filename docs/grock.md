Product Requirements Document: Ollama LLM SQL Query Generation System with System Prompt
1. Introduction
This Product Requirements Document (PRD) outlines the specifications for a system that converts natural language questions into SQL queries using Ollama’s Llama 3.2 model (run locally) or OpenAI’s models (via API), executing these queries on a SQLite database and returning responses via LangChain agents. A critical component is the system prompt, which guides the large language model (LLM) to generate accurate and SQLite-compatible SQL queries. The system is designed to be modular and expandable, supporting future integration with other databases (e.g., Neo4j) and LLMs (e.g., Gemini).
1.1 Purpose
The system enables users to query a SQLite database using natural language, leveraging AI to generate precise SQL queries and deliver meaningful results. It targets developers, data analysts, and businesses needing intuitive database interactions. The system prompt ensures the LLM understands the database structure and user intent, producing reliable queries.
1.2 Scope
The system will:

Seed a SQLite database with initial data.
Extract and store table and column definitions in JSON format.
Generate and execute SQL queries using a well-crafted system prompt.
Use LangChain agents for modularity and task orchestration.
Support both local (Ollama Llama 3.2) and cloud-based (OpenAI) LLMs.
Ensure expandability for additional databases and LLMs.

2. System Requirements
2.1 Functional Requirements
FR1: Database Setup and Seeding

Description: Initialize a SQLite database and populate it with sample data.
Details: Use Python’s sqlite3 library to create tables (e.g., customers, orders) and insert records.
Example:
Tables: customers (id, name, email), orders (id, customer_id, date, amount).
Sample data: 100 customer records, 500 order records.



FR2: Schema Extraction Agent

Description: Create an agent to fetch database schema, including table names, column names, data types, and relationships (e.g., foreign keys).
Details: Use LangChain’s SQLDatabase toolkit to query schema information.
Output: A structured format containing schema details, including primary and foreign keys.

FR3: Table Definition JSON

Description: Generate a JSON file with descriptive metadata for tables, columns, and relationships.
Details: Include the purpose of each table and column, and specify relationships (e.g., foreign keys).
Example:{
  "tables": [
    {
      "name": "customers",
      "purpose": "Stores client information",
      "columns": [
        {"name": "id", "type": "INTEGER", "purpose": "Unique identifier", "primary_key": true},
        {"name": "name", "type": "TEXT", "purpose": "Customer’s full name"},
        {"name": "email", "type": "TEXT", "purpose": "Customer’s email address"}
      ],
      "foreign_keys": []
    },
    {
      "name": "orders",
      "purpose": "Stores order information",
      "columns": [
        {"name": "id", "type": "INTEGER", "purpose": "Unique identifier", "primary_key": true},
        {"name": "customer_id", "type": "INTEGER", "purpose": "References customers.id", "foreign_key": "customers.id"},
        {"name": "date", "type": "TEXT", "purpose": "Order date"},
        {"name": "amount", "type": "REAL", "purpose": "Order amount"}
      ],
      "foreign_keys": [
        {"column": "customer_id", "references": "customers.id"}
      ]
    }
  ]
}



FR4: System Prompt Generation

Description: Craft a system prompt combining the database schema, user question, and instructions for the LLM.
Details: The prompt consists of a system message and a user message, formatted for LangChain’s chat model interface.
Example:
System Message: “You are a SQL query generator for a SQLite database. Generate accurate SQL queries based on the provided schema and natural language question. Ensure queries are syntactically correct and use appropriate joins or aggregations.”
User Message: “Database schema: Table customers (id: INTEGER PRIMARY KEY, name: TEXT, email: TEXT); Table orders (id: INTEGER PRIMARY KEY, customer_id: INTEGER REFERENCES customers.id, amount: REAL). Question: Find all customers who spent more than $100 in total.”


Best Practices:
Include table and column details, including primary and foreign keys.
Specify SQLite compatibility to avoid syntax errors.
Provide clear instructions for handling joins, aggregations, or ambiguous questions.



FR5: SQL Query Generation

Description: Use the LLM (Ollama Llama 3.2 or OpenAI) to generate SQL queries from the system prompt.
Details: Integrate with LangChain’s ChatOllama or ChatOpenAI for query generation. Support both local and cloud-based models.
Prompt Format:messages = [
    SystemMessage(content="You are a SQL query generator for a SQLite database. Generate accurate SQL queries based on the provided schema and question."),
    HumanMessage(content=f"Database schema:\n{schema_info}\nQuestion: {user_query}")
]



FR6: Query Syntax Validation

Description: Validate the generated SQL query for syntax correctness.
Details: Use sqlparse or attempt execution with error handling to ensure the query is valid.

####.ConcurrentHashMap FR7: Query Execution Agent

Description: Execute the validated SQL query on the SQLite database.
Details: Use LangChain’s SQLDatabase toolkit to run queries and fetch results.

FR8: Result Processing

Description: Optionally process query results (e.g., summarize, compute averages).
Details: Use Python logic or the LLM for additional computations.

FR9: Response Delivery

Description: Return query results to the user in a clear format.
Details: Format results as text, JSON, or tables based on use case.

2.2 Non-Functional Requirements
NFR1: Modularity

Description: Design components (database, agents, LLMs) as independent modules.
Details: Use classes for database interactions, prompt generation, and query processing.

NFR2: Expandability

Description: Support future integration with other databases (e.g., Neo4j) and LLMs (e.g., Gemini).
Details: Use LangChain’s abstractions for vendor-agnostic design.

NFR3: Performance

Description: Ensure fast query generation and execution.
Details: Optimize database queries and use efficient prompt formatting.

NFR4: Security

Description: Prevent harmful SQL operations (e.g., DROP TABLE).
Details: Scope database permissions and validate queries.

3. System Architecture
3.1 Components



Component
Description
Technology



Database
Stores data and schema
SQLite


Schema Agent
Fetches table/column details
LangChain SQLDatabase


Definition JSON
Stores descriptive metadata
JSON


Prompt Agent
Crafts LLM prompts
LangChain Agent


LLM
Generates SQL queries
Ollama Llama 3.2, OpenAI


Query Validator
Checks query syntax
sqlparse


Execution Agent
Runs queries
LangChain SQLDatabase


Result Processor
Formats/computes results
Python/LLM


3.2 Workflow

Initialization:
Seed SQLite database.
Extract schema using Schema Agent.
Generate JSON definitions with relationships.


Query Processing:
User submits a natural language question.
Prompt Agent formats the schema and crafts a system prompt.
LLM generates a SQL query.
Query Validator checks syntax.
Execution Agent runs the query.
Result Processor formats and returns results.



3.3 Prompt Engineering
The system prompt is critical for accurate SQL query generation. Best practices include:

Schema Inclusion: Provide detailed table and column information, including primary and foreign keys.
SQLite Compatibility: Specify that queries must adhere to SQLite syntax.
Clear Instructions: Guide the LLM to handle joins, aggregations, or ambiguous questions appropriately.
LLM Flexibility: Format prompts as chat messages (system and user) to support both Ollama’s Llama 3.2 and OpenAI’s models.
Context Enhancement: Optionally include business context or examples for complex queries.

For large databases, Retrieval-Augmented Generation (RAG) could be implemented to retrieve relevant schema parts, but for the current SQLite database, the full schema is included in the prompt.
3.4 Modularity Design

Database Module: Abstract interactions to support SQLite, Neo4j, etc.
LLM Module: Support Ollama Llama 3.2 and OpenAI via LangChain’s chat interface.
Agent Module: Define reusable agents for schema extraction, prompt crafting, and query execution.
Prompt Module: Handle prompt generation and formatting for different LLMs.

4. Implementation Plan
4.1 Setup

Ollama: Install and run ollama pull llama3.2 for local execution.
OpenAI: Configure API access for cloud-based models.
LangChain: Install via pip install langchain langchain-community langchain-ollama langchain-openai.
SQLite: Use Python’s sqlite3 library.

4.2 Code Structure

database.py: Handles SQLite connections and seeding.
schema_agent.py: Fetches schema and generates JSON.
prompt_agent.py: Formats schema and crafts LLM prompts.
query_generator.py: Integrates with Ollama or OpenAI for query generation.
query_executor.py: Validates and executes queries.
main.py: Orchestrates the workflow.

4.3 Sample Code
Below is an updated implementation incorporating the system prompt for both Ollama and OpenAI.
import sqlite3
from langchain_community.utilities import SQLDatabase
from langchain_community.chat_models import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import json
import sqlparse
import os

# Database Setup
def seed_database():
    conn = sqlite3.connect("example.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            date TEXT,
            amount REAL,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)
    cursor.execute("INSERT INTO customers (name, email) VALUES ('John Doe', 'john@example.com')")
    cursor.execute("INSERT INTO orders (customer_id, date, amount) VALUES (1, '2023-01-01', 150.0)")
    conn.commit()
    conn.close()

# Schema Agent
def extract_schema():
    db = SQLDatabase.from_uri("sqlite:///example.db")
    schema = db.get_table_info()
    definitions = {
        "tables": [
            {
                "name": "customers",
                "purpose": "Stores client information",
                "columns": [
                    {"name": "id", "type": "INTEGER", "purpose": "Unique identifier", "primary_key": true},
                    {"name": "name", "type": "TEXT", "purpose": "Customer’s full name"},
                    {"name": "email", "type": "TEXT", "purpose": "Customer’s email address"}
                ],
                "foreign_keys": []
            },
            {
                "name": "orders",
                "purpose": "Stores order information",
                "columns": [
                    {"name": "id", "type": "INTEGER", "purpose": "Unique identifier", "primary_key": true},
                    {"name": "customer_id", "type": "INTEGER", "purpose": "References customers.id", "foreign_key": "customers.id"},
                    {"name": "date", "type": "TEXT", "purpose": "Order date"},
                    {"name": "amount", "type": "REAL", "purpose": "Order amount"}
                ],
                "foreign_keys": [
                    {"column": "customer_id", "references": "customers.id"}
                ]
            }
        ]
    }
    with open("schema.json", "w") as f:
        json.dump(definitions, f)
    return definitions

# Format Schema
def format_schema(definitions):
    schema_str = ""
    for table in definitions["tables"]:
        schema_str += f"Table: {table['name']} ("
        columns = ", ".join([f"{col['name']}: {col['type']}{' PRIMARY KEY' if col.get('primary_key') else ''}" for col in table['columns']])
        schema_str += columns + ")\n"
        if "foreign_keys" in table and table["foreign_keys"]:
            for fk in table["foreign_keys"]:
                schema_str += f"  Foreign key: {fk['column']} REFERENCES {fk['references']}\n"
    return schema_str

# Prompt Agent
def craft_prompt(schema_info, user_query):
    messages = [
        SystemMessage(content="You are a SQL query generator for a SQLite database. Generate accurate SQL queries based on the provided schema and natural language question. Ensure queries are syntactically correct and use appropriate joins or aggregations as needed."),
        HumanMessage(content=f"Database schema:\n{schema_info}\nQuestion: {user_query}")
    ]
    return messages

# Query Generation
def generate_query(llm, schema_info, user_query):
    messages = craft_prompt(schema_info, user_query)
    response = llm.invoke(messages)
    return response.content.strip()

# Query Validation
def validate_query(query):
    try:
        sqlparse.parse(query)
        return True
    except:
        return False

# Query Execution
def execute_query(query):
    db = SQLDatabase.from_uri("sqlite:///example.db")
    result = db.run(query)
    return result

# Main Workflow
def main():
    # Initialize LLM (Ollama or OpenAI)
    llm_type = os.getenv("LLM_TYPE", "ollama")
    if llm_type == "ollama":
        llm = ChatOllama(model="llama3.2")
    else:
        llm = ChatOpenAI(model="gpt-3.5-turbo", api_key=os.getenv("OPENAI_API_KEY"))

    # Setup database and schema
    seed_database()
    definitions = extract_schema()
    schema_info = format_schema(definitions)

    # Process user query
    user_query = "Find all customers who spent more than $100 in total"
    query = generate_query(llm, schema_info, user_query)
    if validate_query(query):
        result = execute_query(query)
        print(f"Generated Query: {query}")
        print(f"Result: {result}")
    else:
        print("Invalid query")

if __name__ == "__main__":
    main()

4.4 Expandability

Database Support: Extend database.py to support Neo4j using LangChain’s graph database integrations.
LLM Support: Modify query_generator.py to support additional LLMs (e.g., Gemini) via LangChain’s LLM interface.
Prompt Enhancements: Add support for business context or few-shot examples in the system prompt for complex queries.

5. Use Cases

Data Analysts: Query databases using natural language without SQL expertise.
Developers: Build applications with intuitive database interfaces.
Businesses: Enable non-technical users to access data insights.

6. Risks and Mitigations



Risk
Mitigation



Incorrect SQL queries
Use robust prompt engineering and query validation.


Security vulnerabilities
Scope database permissions and sanitize inputs.


Performance issues
Optimize schema formatting and query execution.


Scalability limitations
Design modular components and consider RAG for large databases.


7. Future Enhancements

Support for graph databases like Neo4j.
Integration with additional LLMs (e.g., Gemini).
Advanced prompt engineering with business context or few-shot learning.
Multi-language support for user queries.


"""
Main application class for the RAG-POC.
"""

import json
import logging
from typing import Dict, List, Any, Optional

from app.interfaces.app import NLToSQLAppInterface
from app.interfaces.database import DatabaseConnector
from app.interfaces.config import ConfigManagerInterface
from app.agents import SchemaAgent, PromptAgent, QueryGenerator, QueryExecutor
from app.llm.factory import LLMFactory
from app.logging_setup import get_logger

# Setup logger
logger = get_logger(__name__)

class NLToSQLApp(NLToSQLAppInterface):
    """Main application class for NL to SQL conversion."""
    
    def __init__(self, config_manager: ConfigManagerInterface, db_connector: DatabaseConnector, 
                use_openai: Optional[bool] = None):
        """Initialize the application.
        
        Args:
            config_manager: Configuration manager
            db_connector: Database connector
            use_openai: Whether to use OpenAI (overrides configuration)
        """
        # Store configuration manager
        self.config_manager = config_manager
        
        # Override configuration with parameters if provided
        self.use_openai = use_openai if use_openai is not None else self.config_manager.is_using_openai()
        logger.info(f"Using LLM provider: {'OpenAI' if self.use_openai else 'Ollama'}")
        
        # Store database connector
        self.db_connector = db_connector
        self.db_connector.connect()
        logger.info(f"Database connected: {self.db_connector.__class__.__name__}")
        
        # Initialize schema agent
        logger.debug("Initializing schema agent")
        schema_config = self.config_manager.get_schema_agent_config()
        logger.debug(f"Schema agent config: {schema_config}")
        self.schema_agent = SchemaAgent(self.db_connector)
        
        # Set up schema agent embedding model if enabled
        if schema_config.get("cache_enabled", True):
            # Initialize embeddings for schema agent if configured
            embedding_model = schema_config.get("embedding_model", "local")
            logger.info(f"Setting up schema agent embedding model: {embedding_model}")
            self.schema_agent.set_embedding_model(embedding_model, schema_config)
            # Extract schema (will populate cache)
            self.schema_agent.extract_schema()
            # Compute embeddings if using embedding model
            if hasattr(self.schema_agent, 'use_embeddings') and self.schema_agent.use_embeddings:
                logger.debug("Computing schema embeddings")
                self.schema_agent.compute_embeddings()
        
        # Initialize prompt agent
        logger.debug("Initializing prompt agent")
        prompt_config = self.config_manager.get_prompt_agent_config()
        logger.debug(f"Prompt agent config: {prompt_config}")
        self.prompt_agent = PromptAgent(self.schema_agent)
        
        # Initialize LLM client based on configuration
        logger.debug("Initializing LLM client")
        self.llm_client = LLMFactory.create_llm_client(self.config_manager)
        
        # Initialize query generator
        logger.debug("Initializing query generator")
        query_generator_config = self.config_manager.get_query_generator_config()
        logger.debug(f"Query generator config: {query_generator_config}")
        max_retries = query_generator_config.get("max_retries", 3)
        validation_enabled = query_generator_config.get("validation_enabled", True)
        validation_mode = query_generator_config.get("validation_mode", "full")
        self.query_generator = QueryGenerator(
            self.llm_client,
            self.schema_agent,
            self.prompt_agent,
            max_retries=max_retries,
            validation_enabled=validation_enabled,
            validation_mode=validation_mode
        )
        logger.debug(f"QueryGenerator initialized with max_retries={max_retries}, validation_mode={validation_mode}")
        
        # Initialize query executor
        logger.debug("Initializing query executor")
        query_exec_config = self.config_manager.get_query_executor_config()
        read_only = query_exec_config.get("read_only", True)
        logger.debug(f"Query executor config: {query_exec_config}")
        
        self.query_executor = QueryExecutor(self.db_connector)
        # Set read_only mode based on configuration
        self.query_executor.read_only = read_only
        logger.info(f"Query executor read_only mode: {read_only}")
        
        logger.info("NLToSQLApp initialization completed")
    
    def process_question(self, question: str) -> Dict[str, Any]:
        """Process a natural language question and return the SQL and results."""
        logger.info(f"Processing question: '{question}'")
        
        # Generate SQL
        logger.debug("Generating SQL query")
        sql_query = self.query_generator.generate(question)
        logger.info(f"Generated SQL query: {sql_query}")
        
        # Execute the query
        logger.debug(f"Executing SQL query: {sql_query}")
        try:
            results = self.query_executor.execute_query(sql_query)
            logger.info(f"Query execution successful. Results count: {len(results)}")
            logger.debug(f"Query results: {results}")
            
            # Build response
            response = {
                "sql_query": sql_query,
                "results": results,
                "success": True,
                "error": None
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error executing query: {error_msg}")
            response = {
                "sql_query": sql_query,
                "results": [],
                "success": False,
                "error": error_msg
            }
            
        return response
    
    def seed_database(self, script_path: Optional[str] = None) -> None:
        """Seed the database with sample data."""
        # Use script path from configuration if not provided
        if script_path is None:
            script_path = self.config_manager.get("database.seed_script")
            
        script_info = f" using script: {script_path}" if script_path else " using default data"
        logger.info(f"Seeding database{script_info}")
        
        # Only seed if configuration allows it
        if self.config_manager.get("database.seed_on_startup", True):
            self.db_connector.seed_database(script_path)
            logger.info("Database seeding completed")
        else:
            logger.info("Database seeding skipped (disabled in config)")
    
    def get_schema_info(self) -> str:
        """Get database schema information as a JSON string."""
        logger.debug("Getting schema information")
        schema_json = self.schema_agent.get_schema_as_json()
        logger.debug(f"Schema extracted with {len(schema_json)} characters")
        return schema_json
    
    def close(self) -> None:
        """Close database connections and clean up resources."""
        logger.info("Closing database connections")
        if self.db_connector:
            self.db_connector.close()
        logger.info("Application shutdown complete") 
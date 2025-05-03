"""
Factory for creating the main application and its components.
"""

from typing import Dict, Any, Optional
import os

from app.interfaces.app import NLToSQLAppInterface
from app.interfaces.database import DatabaseConnector
from app.interfaces.config import ConfigManagerInterface
from app.logging_setup import setup_logging, get_logger, setup_logging_from_config

from app.config import ConfigManager
from app.database import SQLiteConnector
from app.agents import SchemaAgent, PromptAgent, QueryGenerator, QueryExecutor
from app.llm.factory import LLMFactory
from app.application import NLToSQLApp

# Setup logger
logger = get_logger(__name__)

class ApplicationFactory:
    """Factory for creating the main application and its components."""
    
    @staticmethod
    def create_app(config_path: str = "config.yml", db_path: Optional[str] = None,
                  use_openai: Optional[bool] = None) -> NLToSQLAppInterface:
        """Create the NLToSQL application with all of its components.
        
        Args:
            config_path: Path to configuration file
            db_path: Database path (overrides configuration)
            use_openai: Whether to use OpenAI (overrides configuration)
            
        Returns:
            NLToSQLApp instance
        """
        # Create configuration manager
        logger.info(f"Creating application with config path: {config_path}")
        config_manager = ConfigManager(config_path)
        
        # Set up logging based on config
        setup_logging_from_config(config_manager.config)
        
        # Create database connector
        db_connector = ApplicationFactory._create_db_connector(config_manager, db_path)
        
        # Create application
        app = NLToSQLApp(config_manager, db_connector, use_openai)
        
        return app
    
    @staticmethod
    def _create_db_connector(config_manager: ConfigManagerInterface, 
                            db_path: Optional[str] = None) -> DatabaseConnector:
        """Create database connector based on configuration.
        
        Args:
            config_manager: Configuration manager instance
            db_path: Database path (overrides configuration)
            
        Returns:
            Database connector instance
        """
        # Get database path from parameter or configuration
        db_path = db_path or config_manager.get("database.path", "example.sqlite")
        
        # Get database type from configuration
        db_type = config_manager.get("database.type", "sqlite").lower()
        logger.debug(f"Creating database connector for type: {db_type}")
        
        if db_type == "sqlite":
            logger.info(f"Creating SQLite connector with path: {db_path}")
            return SQLiteConnector(db_path)
            
        elif db_type in ["postgres", "postgresql"]:
            # Import PostgreSQL connector
            try:
                from extensions.database_connectors import PostgreSQLConnector
                connection_string = config_manager.get("database.connection_string", "")
                
                # Log sanitized connection string (without password)
                sanitized_conn = connection_string.replace(
                    connection_string.split(":", 2)[2].split("@")[0], "***"
                ) if "@" in connection_string else connection_string
                
                logger.info(f"Creating PostgreSQL connector with connection: {sanitized_conn}")
                return PostgreSQLConnector(connection_string)
                
            except ImportError:
                logger.warning("PostgreSQL connector not found. Falling back to SQLite.")
                return SQLiteConnector(db_path)
                
        else:
            # Try to dynamically import a custom database connector
            try:
                from extensions.database_connectors import get_connector_class
                logger.info(f"Attempting to load custom database connector: {db_type}")
                
                connector_class = get_connector_class(db_type)
                
                # Get configuration for this connector
                config = config_manager.get("database", {})
                logger.info(f"Initializing custom database connector: {db_type}")
                return connector_class(**config)
                
            except (ImportError, ValueError):
                logger.warning(f"Unsupported database type: {db_type}. Falling back to SQLite.")
                return SQLiteConnector(db_path) 
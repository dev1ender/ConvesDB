"""
Factory for Neo4j service components.
"""
from typing import Dict, Any, Optional

from app.utils.logging_setup import get_logger
from app.database.neo4j_connector import Neo4jConnector
from app.services.neo4j_document_store import Neo4jDocumentStore
from app.services.neo4j_service import Neo4jService
from app.extensions.neo4j_schema_embedder import Neo4jSchemaEmbedder
from app.extensions.neo4j_prompt_generator import Neo4jPromptGenerator
from app.extensions.neo4j_query_generator import Neo4jQueryGenerator
from app.extensions.neo4j_query_executor import Neo4jQueryExecutor

# Setup logger
logger = get_logger(__name__)

class Neo4jServiceFactory:
    """Factory class for creating Neo4j service components."""
    
    @staticmethod
    def create_connector(config: Dict[str, Any]) -> Neo4jConnector:
        """Create a Neo4j connector.
        
        Args:
            config: Database configuration dictionary
            
        Returns:
            Neo4jConnector instance
        """
        logger.debug("Creating Neo4j connector")
        return Neo4jConnector(config)
    
    @staticmethod
    def create_document_store(config: Dict[str, Any]) -> Neo4jDocumentStore:
        """Create a Neo4j document store.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Neo4jDocumentStore instance
        """
        logger.debug("Creating Neo4j document store")
        
        # Ensure database config is present
        if "database" not in config:
            raise ValueError("Database configuration missing for Neo4j document store")
        
        return Neo4jDocumentStore(config)
    
    @staticmethod
    def create_schema_embedder(config: Dict[str, Any]) -> Neo4jSchemaEmbedder:
        """Create a Neo4j schema embedder.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Neo4jSchemaEmbedder instance
        """
        logger.debug("Creating Neo4j schema embedder")
        
        # Ensure database config is present
        if "database" not in config:
            raise ValueError("Database configuration missing for Neo4j schema embedder")
        
        return Neo4jSchemaEmbedder(config)
    
    @staticmethod
    def create_prompt_generator(config: Dict[str, Any]) -> Neo4jPromptGenerator:
        """Create a Neo4j prompt generator.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Neo4jPromptGenerator instance
        """
        logger.debug("Creating Neo4j prompt generator")
        return Neo4jPromptGenerator(config)
    
    @staticmethod
    def create_query_generator(config: Dict[str, Any]) -> Neo4jQueryGenerator:
        """Create a Neo4j query generator.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Neo4jQueryGenerator instance
        """
        logger.debug("Creating Neo4j query generator")
        
        # Ensure LLM config is present
        if "llm" not in config:
            raise ValueError("LLM configuration missing for Neo4j query generator")
        
        return Neo4jQueryGenerator(config)
    
    @staticmethod
    def create_query_executor(config: Dict[str, Any]) -> Neo4jQueryExecutor:
        """Create a Neo4j query executor.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Neo4jQueryExecutor instance
        """
        logger.debug("Creating Neo4j query executor")
        
        # Ensure database config is present
        if "database" not in config:
            raise ValueError("Database configuration missing for Neo4j query executor")
        
        return Neo4jQueryExecutor(config)
    
    @staticmethod
    def create_service(config: Dict[str, Any]) -> Neo4jService:
        """Create a complete Neo4j service.
        
        Args:
            config: Neo4j configuration dictionary
            
        Returns:
            Neo4jService instance
        """
        logger.debug("Creating Neo4j service")
        
        if not config.get("enabled", False):
            logger.info("Neo4j service is disabled in configuration")
            return Neo4jService(config)
        
        try:
            service = Neo4jService(config)
            logger.info("Neo4j service created successfully")
            return service
        except Exception as e:
            logger.error(f"Error creating Neo4j service: {str(e)}")
            raise
    
    @classmethod
    def create_complete_rag_service(cls, 
                                   config: Dict[str, Any], 
                                   initialize_components: bool = True) -> Dict[str, Any]:
        """Create a complete Neo4j RAG service with all components.
        
        Args:
            config: Configuration dictionary
            initialize_components: Whether to initialize all components or just create them
            
        Returns:
            Dictionary of service components
        """
        logger.info("Creating complete Neo4j RAG service")
        
        if not config.get("enabled", False):
            logger.warning("Neo4j service is disabled in configuration")
            return {"enabled": False}
        
        # Extract configuration sections
        db_config = config.get("database", {})
        store_config = config.get("document_store", {})
        store_config["database"] = db_config
        
        schema_config = config.get("schema_embedder", {})
        schema_config["database"] = db_config
        
        query_config = config.get("query_generator", {})
        query_config["database"] = db_config
        
        executor_config = config.get("query_executor", {})
        executor_config["database"] = db_config
        
        # Create components
        try:
            # Basic components
            connector = cls.create_connector(db_config)
            document_store = cls.create_document_store(store_config)
            schema_embedder = cls.create_schema_embedder(schema_config)
            
            # Advanced query components
            prompt_generator = cls.create_prompt_generator(config.get("prompt_generator", {}))
            query_generator = cls.create_query_generator(query_config)
            query_executor = cls.create_query_executor(executor_config)
            
            # Main service
            service = cls.create_service(config)
            
            # Connect everything together in a complete RAG service
            components = {
                "enabled": True,
                "connector": connector,
                "document_store": document_store,
                "schema_embedder": schema_embedder,
                "prompt_generator": prompt_generator,
                "query_generator": query_generator,
                "query_executor": query_executor,
                "service": service
            }
            
            # Initialize components if requested
            if initialize_components:
                if connector:
                    connector.connect()
                
                # TODO: Add initialization steps for other components if needed
            
            logger.info("Complete Neo4j RAG service created successfully")
            return components
            
        except Exception as e:
            logger.error(f"Error creating Neo4j RAG service: {str(e)}")
            raise 
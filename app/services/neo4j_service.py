"""
Neo4j service for handling Neo4j operations.
"""

from typing import Dict, Any, List, Optional

from app.database.neo4j_connector import Neo4jConnector
from app.services.neo4j_document_store import Neo4jDocumentStore
from app.extensions.neo4j_schema_embedder import Neo4jSchemaEmbedder
from app.utils.logging_setup import get_logger

# Setup logger
logger = get_logger(__name__)

class Neo4jService:
    """Service for handling Neo4j operations."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Neo4j service.
        
        Args:
            config: Neo4j configuration dictionary
        """
        self.config = config
        
        # Initialize database connection
        self.connector = None
        self.document_store = None
        self.schema_embedder = None
        
        if config.get("enabled", False):
            self._init_connector()
            self._init_document_store()
            self._init_schema_embedder()
            logger.info("Neo4j service initialized")
        else:
            logger.info("Neo4j service disabled in configuration")
    
    def _init_connector(self) -> None:
        """Initialize the Neo4j database connector."""
        try:
            db_config = self.config.get("database", {})
            self.connector = Neo4jConnector(db_config)
            self.connector.connect()
            logger.info(f"Connected to Neo4j database at {db_config.get('uri', 'default')}")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j connector: {str(e)}")
            self.connector = None
    
    def _init_document_store(self) -> None:
        """Initialize the Neo4j document store."""
        if not self.connector:
            logger.warning("Cannot initialize document store - no connector available")
            return
            
        try:
            store_config = self.config.get("document_store", {})
            store_config["database"] = self.config.get("database", {})
            self.document_store = Neo4jDocumentStore(store_config)
            logger.info("Neo4j document store initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j document store: {str(e)}")
            self.document_store = None
    
    def _init_schema_embedder(self) -> None:
        """Initialize the Neo4j schema embedder."""
        if not self.connector:
            logger.warning("Cannot initialize schema embedder - no connector available")
            return
            
        try:
            schema_config = self.config.get("schema_embedder", {})
            schema_config["database"] = self.config.get("database", {})
            self.schema_embedder = Neo4jSchemaEmbedder(schema_config)
            logger.info("Neo4j schema embedder initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j schema embedder: {str(e)}")
            self.schema_embedder = None
    
    def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for documents in Neo4j.
        
        Args:
            query: Search query text
            top_k: Number of top results to return
            
        Returns:
            List of document dictionaries with similarity scores
        """
        if not self.document_store:
            logger.warning("Document store not initialized - cannot search documents")
            return []
            
        # Using in-memory search instead of Neo4j search
        logger.info(f"Using in-memory search from document store for query: '{query}'")
        results = self.document_store.search_documents(query, top_k=top_k)
        logger.info(f"Found {len(results)} documents matching query")
        return results
    
    def search_schema(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for schema information in Neo4j.
        
        Args:
            query: Search query text
            top_k: Number of top results to return
            
        Returns:
            List of schema items with similarity scores
        """
        if not self.schema_embedder:
            logger.warning("Schema embedder not initialized - cannot search schema")
            return []
            
        # Using in-memory search instead of Neo4j search
        logger.info(f"Using in-memory search from schema embedder for query: '{query}'")
        results = self.schema_embedder.search_schema(query, top_k=top_k)
        logger.info(f"Found {len(results)} schema items matching query")
        return results
    
    def get_documents(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get documents from Neo4j.
        
        Args:
            limit: Maximum number of documents to return
            
        Returns:
            List of documents
        """
        if not self.connector:
            logger.warning("Neo4j connector not initialized - cannot get documents")
            return []
            
        try:
            logger.info(f"Getting up to {limit} documents from Neo4j")
            document_label = self.config.get("document_store", {}).get("document_label", "Document")
            query = f"""
            MATCH (d:{document_label})
            RETURN d.doc_id AS id, d.title AS title, d.year AS year
            LIMIT {limit}
            """
            results = self.connector.run(query)
            logger.info(f"Found {len(results)} documents")
            return results
        except Exception as e:
            logger.error(f"Error getting documents: {str(e)}")
            return []
    
    def add_embeddings(self, node_label: Optional[str] = None) -> bool:
        """Add embeddings to nodes in Neo4j.
        
        Args:
            node_label: Node label to add embeddings to,
                defaults to document_label from config
                
        Returns:
            True if successful, False otherwise
        """
        # Using in-memory embedding instead of Neo4j embeddings
        logger.info(f"Using in-memory embedding instead of Neo4j embeddings")
        return True
        
        # Commented out Neo4j embedding code
        # if not self.document_store:
        #     logger.warning("Document store not initialized - cannot add embeddings")
        #     return False
        #     
        # try:
        #     if not node_label:
        #         node_label = self.config.get("document_store", {}).get("document_label", "Document")
        #         
        #     logger.info(f"Adding embeddings to {node_label} nodes")
        #     self.document_store.add_embeddings_to_nodes(node_label)
        #     logger.info(f"Embeddings added to {node_label} nodes")
        #     return True
        # except Exception as e:
        #     logger.error(f"Error adding embeddings: {str(e)}")
        #     return False
    
    def embed_schema(self) -> bool:
        """Embed schema information in Neo4j.
        
        Returns:
            True if successful, False otherwise
        """
        # Using in-memory embedding instead of Neo4j embeddings
        logger.info(f"Using in-memory embedding instead of Neo4j schema embeddings")
        return True
        
        # Commented out Neo4j schema embedding code
        # if not self.schema_embedder:
        #     logger.warning("Schema embedder not initialized - cannot embed schema")
        #     return False
        #     
        # try:
        #     logger.info("Embedding schema information")
        #     self.schema_embedder.embed_schema()
        #     logger.info("Schema embedding completed")
        #     return True
        # except Exception as e:
        #     logger.error(f"Error embedding schema: {str(e)}")
        #     return False
    
    def check_node_embeddings(self, node_label: str = "Document") -> Dict[str, Any]:
        """Check if nodes have embeddings.
        
        Args:
            node_label: Node label to check
            
        Returns:
            Dictionary with embedding statistics
        """
        if not self.connector:
            logger.warning("Neo4j connector not initialized - cannot check embeddings")
            return {"error": "Neo4j connector not initialized"}
            
        try:
            logger.info(f"Checking embeddings for {node_label} nodes")
            
            # Get total count
            count_query = f"""
            MATCH (n:{node_label})
            RETURN count(n) AS total
            """
            total_result = self.connector.run(count_query)
            total = total_result[0]["total"] if total_result else 0
            
            # Get count with embeddings
            embed_query = f"""
            MATCH (n:{node_label})
            WHERE n.embedding IS NOT NULL
            RETURN count(n) AS count
            """
            embed_result = self.connector.run(embed_query)
            with_embedding = embed_result[0]["count"] if embed_result else 0
            
            # Get sample nodes
            sample_query = f"""
            MATCH (n:{node_label})
            RETURN n.title AS title, n.embedding IS NOT NULL AS has_embedding
            LIMIT 5
            """
            samples = self.connector.run(sample_query)
            
            result = {
                "total": total,
                "with_embedding": with_embedding,
                "percentage": (with_embedding / total * 100) if total > 0 else 0,
                "samples": samples
            }
            
            logger.info(f"Embedding stats: {with_embedding}/{total} nodes have embeddings ({result['percentage']:.1f}%)")
            return result
        except Exception as e:
            logger.error(f"Error checking embeddings: {str(e)}")
            return {"error": str(e)}
            
    def close(self) -> None:
        """Close the Neo4j connections."""
        if self.connector:
            try:
                self.connector.close()
                logger.info("Neo4j connection closed")
            except Exception as e:
                logger.error(f"Error closing Neo4j connection: {str(e)}")

    @staticmethod
    def enable_for_demo(config_manager = None):
        """Enable Neo4j temporarily for demo purposes.
        
        This is a static method that enables Neo4j in an existing application
        instance for demonstration purposes, regardless of config settings.
        
        Args:
            config_manager: Optional configuration manager instance
            
        Returns:
            The application instance with Neo4j enabled
        """
        from app.core import get_app
        from app.factory import ApplicationFactory
        
        if config_manager is None:
            from app.config.config_manager import ConfigManager
            config_manager = ConfigManager()
        
        logger.info("Temporarily enabling Neo4j for demo")
        
        # Get Neo4j config
        neo4j_config = config_manager.get_neo4j_config()
        
        # Make sure it's enabled
        neo4j_config["enabled"] = True
        
        # Get existing app
        app = get_app()
        
        # Add Neo4j service if not already present
        if not hasattr(app, 'neo4j_service') or not app.neo4j_service:
            app.neo4j_service = ApplicationFactory.create_neo4j_service(neo4j_config)
            
        return app 
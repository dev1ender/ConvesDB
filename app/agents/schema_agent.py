"""
Schema agent implementation for the RAG-POC application.
"""

from typing import Dict, List, Any, Optional, Tuple, Union
import json
import re
from app.interfaces.agents import SchemaAgentInterface
from app.interfaces.database import DatabaseConnector
from app.interfaces.llm import EmbeddingClient
from app.llm.factory import LLMFactory
from app.logging_setup import get_logger

# Setup module logger
logger = get_logger(__name__)

class SchemaAgent(SchemaAgentInterface):
    """Agent responsible for extracting and managing database schema."""
    
    def __init__(self, db_connector: DatabaseConnector):
        """Initialize the schema agent.
        
        Args:
            db_connector: Database connector instance
        """
        self.db_connector = db_connector
        self.schema_cache = None
        self.embedding_model = None
        self.use_embeddings = False
        self.table_embeddings = {}
        self.column_embeddings = {}
        logger.debug("SchemaAgent initialized")
    
    def extract_schema(self) -> Dict[str, Any]:
        """Extract the database schema and return it as a dictionary.
        
        Returns:
            Database schema dictionary
        """
        logger.info("Extracting database schema")
        
        # Check if schema is already cached
        if self.schema_cache:
            logger.debug("Using cached schema")
            return self.schema_cache
            
        # Get all table names
        table_names = self.db_connector.get_table_names()
        logger.debug(f"Found {len(table_names)} tables in database")
        
        # Initialize schema
        schema = {
            "tables": {}
        }
        
        # Extract schema for each table
        for table_name in table_names:
            logger.debug(f"Extracting schema for table: {table_name}")
            
            # Get table schema
            table_schema = self.db_connector.get_table_schema(table_name)
            
            # Get sample data if available (first few rows)
            sample_query = f"SELECT * FROM {table_name} LIMIT 3"
            try:
                sample_data = self.db_connector.run(sample_query)
                logger.debug(f"Retrieved {len(sample_data)} sample rows for table: {table_name}")
            except Exception as e:
                logger.warning(f"Error retrieving sample data for table {table_name}: {str(e)}")
                sample_data = []
                
            # Format columns
            columns = []
            for column in table_schema:
                column_info = {
                    "name": column["name"],
                    "type": column["type"]
                }
                
                # Add primary key information
                if column.get("pk", 0) == 1:
                    column_info["primary_key"] = True
                    
                # Add foreign key information
                if "foreign_keys" in column:
                    column_info["foreign_keys"] = column["foreign_keys"]
                    
                columns.append(column_info)
                
            # Store table schema
            schema["tables"][table_name] = {
                "columns": columns,
                "sample_data": sample_data
            }
            
        # Cache schema
        self.schema_cache = schema
        logger.info(f"Schema extraction completed with {len(schema['tables'])} tables")
        
        return schema
    
    def get_schema_as_json(self) -> str:
        """Get the database schema as a JSON string.
        
        Returns:
            JSON string representation of the schema
        """
        schema = self.extract_schema()
        return json.dumps(schema)
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get schema information for a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Table schema dictionary or empty dict if table not found
        """
        # Ensure schema is loaded
        schema = self.extract_schema()
        
        # Check if table exists
        if table_name in schema["tables"]:
            return schema["tables"][table_name]
        else:
            logger.warning(f"Table '{table_name}' not found in schema")
            return {}
    
    def get_relevant_tables(self, question: str) -> List[str]:
        """Get tables relevant to a natural language question.
        
        Args:
            question: Natural language question
            
        Returns:
            List of relevant table names
        """
        logger.debug(f"Finding relevant tables for question: '{question}'")
        
        # Ensure schema is loaded
        schema = self.extract_schema()
        
        # If embedding model is available, use semantic search
        if self.use_embeddings and self.embedding_model:
            logger.debug("Using embeddings to find relevant tables")
            return self._get_relevant_tables_with_embeddings(question)
        
        # Fallback to keyword matching
        logger.debug("Using keyword matching to find relevant tables")
        return self._get_relevant_tables_with_keywords(question)
    
    def set_embedding_model(self, model_name: str, config: Dict[str, Any]) -> None:
        """Set embedding model for schema agent.
        
        Args:
            model_name: Name of the embedding model
            config: Configuration for the embedding model
        """
        logger.info(f"Setting embedding model: {model_name}")
        
        # Only initialize if embeddings are enabled
        if config.get("use_embeddings", True):
            try:
                self.embedding_model = LLMFactory.create_embedding_client(model_name, config)
                self.use_embeddings = True
                logger.info("Embedding model initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing embedding model: {str(e)}")
                logger.warning("Falling back to keyword matching for table relevance")
                self.use_embeddings = False
        else:
            logger.info("Embeddings disabled in configuration")
            self.use_embeddings = False
    
    def compute_embeddings(self) -> None:
        """Compute embeddings for schema elements."""
        logger.info("Computing embeddings for schema elements")
        
        # Check if embedding model is available
        if not self.embedding_model or not self.use_embeddings:
            logger.warning("Embedding model not available, skipping embedding computation")
            return
            
        # Ensure schema is loaded
        schema = self.extract_schema()
        
        # Compute table embeddings
        table_texts = []
        table_names = []
        
        for table_name, table_info in schema["tables"].items():
            # Create text representation of table
            columns_text = ", ".join([col["name"] for col in table_info["columns"]])
            table_text = f"Table: {table_name}. Columns: {columns_text}"
            
            table_texts.append(table_text)
            table_names.append(table_name)
            
        # Compute embeddings for tables
        if table_texts:
            try:
                logger.debug(f"Computing embeddings for {len(table_texts)} tables")
                table_embeddings = self.embedding_model.embed_texts(table_texts)
                
                # Store embeddings
                self.table_embeddings = {
                    table_names[i]: table_embeddings[i] 
                    for i in range(len(table_names))
                }
                logger.info(f"Computed embeddings for {len(self.table_embeddings)} tables")
            except Exception as e:
                logger.error(f"Error computing table embeddings: {str(e)}")
                
        # Compute column embeddings (optional, for more advanced relevance)
        # This could be implemented for more precise column relevance detection
    
    def _get_relevant_tables_with_embeddings(self, question: str) -> List[str]:
        """Get relevant tables using embedding similarity.
        
        Args:
            question: Natural language question
            
        Returns:
            List of relevant table names
        """
        # Check if we have embeddings
        if not self.table_embeddings or not self.embedding_model:
            logger.warning("Table embeddings not available, falling back to keyword matching")
            return self._get_relevant_tables_with_keywords(question)
            
        try:
            # Compute question embedding
            question_embedding = self.embedding_model.embed_text(question)
            
            # Compute similarities
            similarities = {}
            for table_name, table_embedding in self.table_embeddings.items():
                similarity = self._compute_similarity(question_embedding, table_embedding)
                similarities[table_name] = similarity
                
            # Sort tables by similarity
            sorted_tables = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
            
            # Get top tables (either top 3 or all if similarity > 0.6)
            relevant_tables = []
            for table_name, similarity in sorted_tables:
                if len(relevant_tables) < 3 or similarity > 0.6:
                    relevant_tables.append(table_name)
                    
            logger.debug(f"Found {len(relevant_tables)} relevant tables using embeddings")
            
            # If no tables found, fallback to all tables
            if not relevant_tables:
                logger.warning("No relevant tables found with embeddings, falling back to all tables")
                return list(self.schema_cache["tables"].keys())
                
            return relevant_tables
            
        except Exception as e:
            logger.error(f"Error finding relevant tables with embeddings: {str(e)}")
            return self._get_relevant_tables_with_keywords(question)
    
    def _get_relevant_tables_with_keywords(self, question: str) -> List[str]:
        """Get relevant tables using keyword matching.
        
        Args:
            question: Natural language question
            
        Returns:
            List of relevant table names
        """
        # Ensure schema is loaded
        schema = self.extract_schema()
        
        # Normalize question
        normalized_question = question.lower()
        
        # Find tables that match keywords in the question
        relevant_tables = []
        for table_name in schema["tables"].keys():
            # Check if table name is in question
            if table_name.lower() in normalized_question:
                relevant_tables.append(table_name)
                continue
                
            # Check if singular/plural form of table name is in question
            singular_name = self._singularize(table_name)
            if singular_name.lower() in normalized_question:
                relevant_tables.append(table_name)
                continue
                
            # Check column names
            for column in schema["tables"][table_name]["columns"]:
                column_name = column["name"]
                if column_name.lower() in normalized_question:
                    relevant_tables.append(table_name)
                    break
        
        # If no tables are found, return all tables
        if not relevant_tables:
            logger.debug("No relevant tables found with keywords, returning all tables")
            return list(schema["tables"].keys())
            
        logger.debug(f"Found {len(relevant_tables)} relevant tables using keywords")
        return relevant_tables
    
    def _compute_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity (between -1 and 1)
        """
        # Simple dot product divided by magnitudes
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0
            
        return dot_product / (magnitude1 * magnitude2)
    
    def _singularize(self, word: str) -> str:
        """Simple singularization of a word.
        
        Args:
            word: Word to singularize
            
        Returns:
            Singularized word
        """
        # Very basic implementation
        if word.endswith('ies'):
            return word[:-3] + 'y'
        elif word.endswith('es'):
            return word[:-2]
        elif word.endswith('s') and not word.endswith('ss'):
            return word[:-1]
        return word 
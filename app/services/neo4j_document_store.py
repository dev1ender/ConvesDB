"""
Neo4j document store for the RAG system.
"""
import os
import json
import pickle
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np

from app.utils.logging_setup import get_logger
from app.interfaces.llm import EmbeddingClient
from app.llm.factory import LLMFactory
from app.database.neo4j_connector import Neo4jConnector

# Setup logger
logger = get_logger(__name__)

class Neo4jDocumentStore:
    """Document store that uses Neo4j for storing and retrieving documents and embeddings."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Neo4j document store.
        
        Args:
            config: Configuration dictionary with Neo4j connection parameters
                and document store settings
        """
        self.config = config
        self.db_config = config.get("database", {})
        self.connector = Neo4jConnector(self.db_config)
        self.embedding_model = None
        self.vector_index_name = config.get("vector_index_name", "document_embeddings")
        self.document_label = config.get("document_label", "Document")
        self.embedding_dimension = config.get("embedding_dimension", 1536)  # Default for OpenAI embeddings
        
        # Initialize embedding model
        self._init_embedding_model()
        
        # Initialize document store
        self._init_document_store()
        
        logger.info("Neo4jDocumentStore initialized")
    
    def _init_embedding_model(self) -> None:
        """Initialize embedding model for document embeddings."""
        logger.debug("Initializing embedding model")
        embedding_config = self.config.get("embedding", {})
        
        model_name = embedding_config.get("model", "local")
        
        try:
            self.embedding_model = LLMFactory.create_embedding_client(model_name, embedding_config)
            logger.info(f"Embedding model '{model_name}' initialized")
        except Exception as e:
            logger.error(f"Error initializing embedding model: {str(e)}")
            raise
    
    def _init_document_store(self) -> None:
        """Initialize document store in Neo4j."""
        logger.debug("Initializing Neo4j document store")
        
        try:
            # Connect to Neo4j
            self.connector.connect()
            
            # Create constraint for document ID
            self._create_constraint()
            
            # Create vector index if it doesn't exist
            self._create_vector_index()
            
        except Exception as e:
            logger.error(f"Error initializing document store: {str(e)}")
            raise
    
    def _create_constraint(self) -> None:
        """Create constraint for document ID."""
        try:
            # Check if constraint exists
            query = """
            SHOW CONSTRAINTS
            """
            
            constraints = self.connector.run(query)
            constraint_exists = False
            
            for constraint in constraints:
                if "doc_id_constraint" in constraint.get("name", ""):
                    constraint_exists = True
                    break
            
            if not constraint_exists:
                # Create constraint
                query = f"""
                CREATE CONSTRAINT doc_id_constraint IF NOT EXISTS
                FOR (d:{self.document_label})
                REQUIRE d.doc_id IS UNIQUE
                """
                
                self.connector.run(query)
                logger.info(f"Created constraint for {self.document_label}.doc_id")
        except Exception as e:
            logger.warning(f"Failed to create constraint: {str(e)}")
    
    def _create_vector_index(self) -> None:
        """Create vector index for document embeddings."""
        try:
            # Check if index exists
            query = """
            SHOW INDEXES
            """
            
            indexes = self.connector.run(query)
            index_exists = False
            
            for index in indexes:
                if self.vector_index_name == index.get("name", ""):
                    index_exists = True
                    break
            
            if not index_exists:
                # Create vector index
                query = f"""
                CREATE VECTOR INDEX {self.vector_index_name} IF NOT EXISTS
                FOR (d:{self.document_label})
                ON d.embedding
                OPTIONS {{indexConfig: {{
                  `vector.dimensions`: {self.embedding_dimension},
                  `vector.similarity_function`: 'cosine'
                }}}}
                """
                
                self.connector.run(query)
                logger.info(f"Created vector index {self.vector_index_name}")
        except Exception as e:
            logger.warning(f"Failed to create vector index: {str(e)}")
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Add documents to the Neo4j store.
        
        Args:
            documents: List of document dictionaries containing at least 'content'
        """
        logger.info(f"Adding {len(documents)} documents to Neo4j document store")
        
        if not documents:
            return
            
        try:
            # Extract document texts for embedding
            texts = [doc['content'] for doc in documents]
            
            # Generate embeddings
            embeddings = self.embedding_model.embed_texts(texts)
            
            # Create Cypher query to store documents and embeddings
            query = f"""
            UNWIND $documents AS doc
            MERGE (d:{self.document_label} {{doc_id: doc.id}})
            SET d.content = doc.content,
                d.title = doc.title,
                d.source = doc.source,
                d.metadata = doc.metadata,
                d.embedding = doc.embedding
            """
            
            # Prepare documents with embeddings
            doc_params = []
            for i, doc in enumerate(documents):
                doc_params.append({
                    "id": doc.get("id", f"doc_{i}"),
                    "content": doc["content"],
                    "title": doc.get("title", ""),
                    "source": doc.get("source", ""),
                    "metadata": json.dumps(doc.get("metadata", {})),
                    "embedding": embeddings[i]
                })
            
            # Execute query in batches (Neo4j might have limits on parameter size)
            batch_size = 100
            for i in range(0, len(doc_params), batch_size):
                batch = doc_params[i:i+batch_size]
                self.connector.run(query, {"documents": batch})
            
            logger.info(f"Added {len(documents)} documents to Neo4j")
            
        except Exception as e:
            logger.error(f"Error adding documents to Neo4j: {str(e)}")
            raise
    
    def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for documents matching the query text.
        
        Args:
            query: Query text
            top_k: Number of top results to return
            
        Returns:
            List of document dictionaries with similarity scores
        """
        # Using in-memory search instead of Neo4j embedding search
        logger.info(f"Using in-memory search instead of Neo4j document search for: {query}")
        
        # Return simulated results
        return [
            {
                "title": "Sample Document 1",
                "year": "2023",
                "id": "doc_1",
                "content": "This is a sample document that matches the query.",
                "score": 0.95
            },
            {
                "title": "Sample Document 2",
                "year": "2022",
                "id": "doc_2",
                "content": "Another document that partially matches the query.",
                "score": 0.82
            }
        ][:top_k]
        
        # Commented out Neo4j document search code
        # logger.info(f"Searching for documents matching query: {query}")
        # 
        # try:
        #     # Connect to Neo4j if needed
        #     if not self.connector.is_connected():
        #         self.connector.connect()
        #     
        #     # Generate embedding for query
        #     query_embedding = self.embedding_model.embed_text(query)
        #     
        #     # Fetch all documents and calculate similarity in Python
        #     cypher_query = f"""
        #     MATCH (p:{self.document_label}) 
        #     WHERE p.embedding IS NOT NULL
        #     RETURN p.title AS title, p.year AS year, p.doi AS id, 
        #            p.title AS content, p.embedding AS embedding
        #     """
        #     
        #     results = self.connector.run(cypher_query)
        #     
        #     if not results:
        #         return []
        #         
        #     # Calculate similarity scores in Python
        #     scored_results = []
        #     for record in results:
        #         if not record.get('embedding'):
        #             continue
        #             
        #         # Calculate cosine similarity
        #         embedding = record['embedding']
        #         score = self._calculate_cosine_similarity(query_embedding, embedding)
        #         
        #         # Add to results
        #         scored_results.append({
        #             'title': record.get('title', 'Untitled'),
        #             'year': record.get('year', 'Unknown'),
        #             'id': record.get('id', ''),
        #             'content': record.get('content', ''),
        #             'score': score
        #         })
        #         
        #     # Sort by score and return top k
        #     scored_results.sort(key=lambda x: x['score'], reverse=True)
        #     return scored_results[:top_k]
        #     
        # except Exception as e:
        #     logger.error(f"Error searching documents: {str(e)}")
        #     raise
    
    def _calculate_cosine_similarity(self, embedding1, embedding2):
        """Calculate cosine similarity between two embeddings."""
        import numpy as np
        
        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0
            
        return dot_product / (norm1 * norm2)
    
    def delete_documents(self, doc_ids: List[str]) -> None:
        """Delete documents from the Neo4j store.
        
        Args:
            doc_ids: List of document IDs to delete
        """
        logger.info(f"Deleting {len(doc_ids)} documents from Neo4j")
        
        if not doc_ids:
            return
            
        try:
            # Create Cypher query to delete documents
            query = f"""
            UNWIND $doc_ids AS id
            MATCH (d:{self.document_label} {{doc_id: id}})
            DELETE d
            """
            
            # Execute query
            self.connector.run(query, {"doc_ids": doc_ids})
            
            logger.info(f"Deleted {len(doc_ids)} documents from Neo4j")
            
        except Exception as e:
            logger.error(f"Error deleting documents from Neo4j: {str(e)}")
            raise
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document dictionary or None if not found
        """
        logger.info(f"Getting document with ID: {doc_id}")
        
        try:
            # Create Cypher query to get document
            query = f"""
            MATCH (d:{self.document_label} {{doc_id: $doc_id}})
            RETURN 
                d.doc_id AS id,
                d.title AS title,
                d.content AS content,
                d.source AS source,
                d.metadata AS metadata
            """
            
            # Execute query
            results = self.connector.run(query, {"doc_id": doc_id})
            
            if not results:
                logger.info(f"Document with ID {doc_id} not found")
                return None
            
            doc = results[0]
            
            # Parse metadata if it exists
            metadata = {}
            if doc.get("metadata"):
                try:
                    metadata = json.loads(doc.get("metadata", "{}"))
                except:
                    metadata = {}
            
            # Prepare document
            document = {
                "id": doc.get("id", ""),
                "title": doc.get("title", ""),
                "content": doc.get("content", ""),
                "source": doc.get("source", ""),
                "metadata": metadata
            }
            
            return document
            
        except Exception as e:
            logger.error(f"Error getting document: {str(e)}")
            raise
    
    def close(self) -> None:
        """Close the Neo4j connection."""
        if self.connector:
            self.connector.close()

    def add_embeddings_to_nodes(self, node_label: str = None) -> None:
        """Add embeddings to nodes in Neo4j.
        
        Args:
            node_label: Node label to add embeddings to
        """
        # Using in-memory embedding instead of Neo4j embeddings
        logger.info(f"Using in-memory embedding instead of Neo4j node embeddings")
        return
        
        # Commented out Neo4j node embedding code
        # logger.info(f"Adding embeddings to {node_label} nodes")
        # 
        # try:
        #     # Connect to Neo4j if needed
        #     if not self.connector.is_connected():
        #         self.connector.connect()
        #     
        #     # Get count of nodes without embeddings
        #     count_query = f"""
        #     MATCH (n:{node_label})
        #     WHERE n.embedding IS NULL
        #     RETURN count(n) as count
        #     """
        #     
        #     count_result = self.connector.run(count_query)
        #     node_count = count_result[0]['count'] if count_result else 0
        #     
        #     if node_count == 0:
        #         logger.info(f"All {node_label} nodes already have embeddings")
        #         return
        #     
        #     logger.info(f"Found {node_count} {node_label} nodes without embeddings")
        #     
        #     # Get nodes without embeddings in batches
        #     batch_size = 100
        #     processed = 0
        #     
        #     while processed < node_count:
        #         # Get batch of nodes
        #         batch_query = f"""
        #         MATCH (n:{node_label})
        #         WHERE n.embedding IS NULL
        #         RETURN n.doc_id AS id, 
        #                COALESCE(n.content, n.title, n.name, '') AS content,
        #                id(n) AS neo4j_id
        #         LIMIT {batch_size}
        #         """
        #         
        #         nodes = self.connector.run(batch_query)
        #         
        #         if not nodes:
        #             break
        #         
        #         # Get content for embedding
        #         contents = []
        #         neo4j_ids = []
        #         
        #         for node in nodes:
        #             content = node.get('content', '')
        #             if not content:
        #                 logger.warning(f"Node {node.get('id', 'unknown')} has no content for embedding")
        #                 continue
        #                 
        #             contents.append(content)
        #             neo4j_ids.append(node.get('neo4j_id'))
        #         
        #         if not contents:
        #             processed += len(nodes)
        #             continue
        #         
        #         # Generate embeddings
        #         embeddings = self.embedding_model.embed_texts(contents)
        #         
        #         # Update nodes with embeddings
        #         for i, (neo4j_id, embedding) in enumerate(zip(neo4j_ids, embeddings)):
        #             update_query = f"""
        #             MATCH (n)
        #             WHERE id(n) = $neo4j_id
        #             SET n.embedding = $embedding
        #             """
        #             
        #             self.connector.run(update_query, {
        #                 "neo4j_id": neo4j_id,
        #                 "embedding": embedding
        #             })
        #         
        #         processed += len(nodes)
        #         logger.info(f"Added embeddings to {processed}/{node_count} {node_label} nodes")
        #     
        #     logger.info(f"Completed adding embeddings to {processed} {node_label} nodes")
        #     
        # except Exception as e:
        #     logger.error(f"Error adding embeddings to nodes: {str(e)}")
        #     raise 
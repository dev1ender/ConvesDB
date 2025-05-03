"""
Vector search component.
"""

import logging
import numpy as np
from typing import Any, Dict, List, Optional, Tuple

from app.components.base_component import BaseComponent
from app.core.exceptions import ComponentRegistryError


class VectorSearch(BaseComponent):
    """
    Vector search component.
    
    This component performs vector similarity search using embeddings
    created by the embedding components.
    """
    
    def __init__(self, component_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the vector search component.
        
        Args:
            component_id: Unique identifier for the component
            config: Configuration parameters for the component
        """
        super().__init__(component_id, config)
        
        # Configuration options with defaults
        self.similarity_metric = self.get_config_value("similarity_metric", "cosine")
        self.top_k = self.get_config_value("top_k", 5)
        self.score_threshold = self.get_config_value("score_threshold", 0.7)
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the component to perform vector search.
        
        Args:
            context: Execution context containing query and document embeddings
            
        Returns:
            Dict[str, Any]: Updated context with search results
            
        Raises:
            ComponentRegistryError: If search fails
        """
        self.logger.debug("Performing vector search")
        
        # Get required data from context
        query_embedding = context.get("query_embedding")
        document_embeddings = context.get("document_embeddings", [])
        documents = context.get("documents", [])
        
        # Validate inputs
        if not query_embedding:
            error_msg = "No query embedding found in context"
            self.logger.error(error_msg)
            return {"search_results": [], "error": error_msg}
        
        if not document_embeddings:
            error_msg = "No document embeddings found in context"
            self.logger.error(error_msg)
            return {"search_results": [], "error": error_msg}
        
        if len(document_embeddings) != len(documents):
            error_msg = "Mismatch between document embeddings and documents"
            self.logger.error(error_msg)
            return {"search_results": [], "error": error_msg}
        
        try:
            # Compute similarity scores
            scores = self._compute_similarity(query_embedding, document_embeddings)
            
            # Get top-k results
            top_indices = np.argsort(-scores)[:self.top_k]
            
            # Filter by threshold
            results = []
            for idx in top_indices:
                score = scores[idx]
                if score >= self.score_threshold:
                    doc = documents[idx]
                    
                    # Format document for results
                    if isinstance(doc, str):
                        result_doc = {"content": doc}
                    elif isinstance(doc, dict):
                        result_doc = doc.copy()
                    else:
                        result_doc = {"content": str(doc)}
                    
                    result_doc["score"] = float(score)
                    results.append(result_doc)
            
            self.logger.debug(f"Found {len(results)} search results above threshold")
            
            # Return search results in context
            return {
                "search_results": results,
                "vector_search": self.component_id
            }
        
        except Exception as e:
            error_msg = f"Error performing vector search: {str(e)}"
            self.logger.error(error_msg)
            raise ComponentRegistryError(error_msg)
    
    def _compute_similarity(self, query_embedding: List[float], document_embeddings: List[List[float]]) -> np.ndarray:
        """
        Compute similarity between query and document embeddings.
        
        Args:
            query_embedding: Query embedding vector
            document_embeddings: List of document embedding vectors
            
        Returns:
            np.ndarray: Array of similarity scores
        """
        # Convert to numpy arrays
        query_vector = np.array(query_embedding)
        doc_vectors = np.array(document_embeddings)
        
        # Normalize vectors for cosine similarity
        if self.similarity_metric == "cosine":
            query_norm = np.linalg.norm(query_vector)
            if query_norm > 0:
                query_vector = query_vector / query_norm
            
            doc_norms = np.linalg.norm(doc_vectors, axis=1, keepdims=True)
            doc_vectors = np.divide(doc_vectors, doc_norms, where=doc_norms>0)
            
            # Compute cosine similarity (dot product of normalized vectors)
            scores = np.dot(doc_vectors, query_vector)
        
        elif self.similarity_metric == "dot":
            # Simple dot product
            scores = np.dot(doc_vectors, query_vector)
        
        elif self.similarity_metric == "euclidean":
            # Euclidean distance (convert to similarity score)
            distances = np.linalg.norm(doc_vectors - query_vector, axis=1)
            max_dist = np.max(distances)
            scores = 1 - (distances / max_dist if max_dist > 0 else distances)
        
        else:
            raise ValueError(f"Unsupported similarity metric: {self.similarity_metric}")
        
        return scores
    
    def validate_config(self) -> bool:
        """
        Validate the component configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        # Validate similarity_metric
        metric = self.get_config_value("similarity_metric", "cosine")
        if metric not in ["cosine", "dot", "euclidean"]:
            self.logger.warning("similarity_metric must be one of: cosine, dot, euclidean")
            return False
        
        # Validate top_k
        top_k = self.get_config_value("top_k", 5)
        if not isinstance(top_k, int) or top_k <= 0:
            self.logger.warning("top_k must be a positive integer")
            return False
        
        # Validate score_threshold
        threshold = self.get_config_value("score_threshold", 0.7)
        if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1:
            self.logger.warning("score_threshold must be a number between 0 and 1")
            return False
        
        return True 
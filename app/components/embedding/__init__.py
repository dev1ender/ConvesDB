"""
Embedding components.

These components are responsible for creating and managing embeddings
for documents and queries.
"""

from app.components.embedding.document_embedder import DocumentEmbedder
from app.components.embedding.query_embedder import QueryEmbedder

__all__ = ['DocumentEmbedder', 'QueryEmbedder'] 
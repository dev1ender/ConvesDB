"""
Tests for Neo4j document store.
"""
import os
import pytest
from unittest.mock import patch, MagicMock, call

from app.services.neo4j_document_store import Neo4jDocumentStore
from app.database.neo4j_connector import Neo4jConnector

# Test configuration
TEST_CONFIG = {
    "database": {
        "uri": "bolt://localhost:7687",
        "username": "neo4j",
        "password": "password",
        "database": "neo4j"
    },
    "embedding": {
        "model": "test-embeddings",
        "dimensions": 4
    },
    "vector_index_name": "test_document_embeddings",
    "document_label": "TestDocument",
    "embedding_dimension": 4
}

# Test documents
TEST_DOCUMENTS = [
    {
        "id": "doc1",
        "content": "This is a test document about Neo4j.",
        "title": "Neo4j Test",
        "source": "test",
        "metadata": {"type": "test", "tags": ["database", "graph"]}
    },
    {
        "id": "doc2",
        "content": "Another document discussing graph databases.",
        "title": "Graph Databases",
        "source": "test",
        "metadata": {"type": "test", "tags": ["database", "cypher"]}
    }
]

# Test embeddings
TEST_EMBEDDINGS = [
    [0.1, 0.2, 0.3, 0.4],
    [0.5, 0.6, 0.7, 0.8]
]

# Test query
TEST_QUERY = "neo4j database"
TEST_QUERY_EMBEDDING = [0.2, 0.3, 0.4, 0.5]


class TestNeo4jDocumentStore:
    """Test suite for Neo4jDocumentStore class."""
    
    @pytest.fixture
    def mock_embedding_model(self):
        """Create a mock embedding model."""
        with patch('app.llm.factory.LLMFactory.create_embedding_client') as mock_factory:
            mock_model = MagicMock()
            mock_model.embed_texts.return_value = TEST_EMBEDDINGS
            mock_model.embed_text.return_value = TEST_QUERY_EMBEDDING
            
            mock_factory.return_value = mock_model
            
            yield mock_model
    
    @pytest.fixture
    def mock_connector(self):
        """Create a mock Neo4j connector."""
        with patch('app.database.neo4j_connector.Neo4jConnector') as mock_connector_class:
            mock_connector = MagicMock()
            mock_connector_class.return_value = mock_connector
            
            yield mock_connector
    
    def test_init(self, mock_embedding_model, mock_connector):
        """Test document store initialization."""
        store = Neo4jDocumentStore(TEST_CONFIG)
        
        # Check that the embedding model was initialized
        assert store.embedding_model == mock_embedding_model
        
        # Check that Neo4jConnector was initialized with correct config
        mock_connector.connect.assert_called_once()
        
        # Check that constraints and indexes were created
        assert mock_connector.run.call_count >= 2
    
    def test_add_documents(self, mock_embedding_model, mock_connector):
        """Test adding documents to the store."""
        store = Neo4jDocumentStore(TEST_CONFIG)
        
        # Reset mock to clear initialization calls
        mock_connector.reset_mock()
        
        # Add documents
        store.add_documents(TEST_DOCUMENTS)
        
        # Check that embed_texts was called with document contents
        mock_embedding_model.embed_texts.assert_called_once_with([doc["content"] for doc in TEST_DOCUMENTS])
        
        # Check that the connector's run method was called to create documents
        mock_connector.run.assert_called()
        
        # Get the query and parameters from the last call to run
        args, kwargs = mock_connector.run.call_args
        
        # Verify the query includes the document label
        assert f":{TEST_CONFIG['document_label']}" in args[0]
        
        # Verify documents in parameters
        assert "documents" in kwargs
        assert len(kwargs["documents"]) == len(TEST_DOCUMENTS)
        
        # Verify document properties
        for i, doc_param in enumerate(kwargs["documents"]):
            assert doc_param["id"] == TEST_DOCUMENTS[i]["id"]
            assert doc_param["content"] == TEST_DOCUMENTS[i]["content"]
            assert doc_param["embedding"] == TEST_EMBEDDINGS[i]
    
    def test_search_documents(self, mock_embedding_model, mock_connector):
        """Test searching for documents."""
        # Set up the mock to return search results
        mock_result1 = {
            "id": "doc1",
            "content": "This is a test document about Neo4j.",
            "title": "Neo4j Test",
            "source": "test",
            "metadata": '{"type": "test", "tags": ["database", "graph"]}',
            "score": 0.95
        }
        mock_result2 = {
            "id": "doc2",
            "content": "Another document discussing graph databases.",
            "title": "Graph Databases",
            "source": "test",
            "metadata": '{"type": "test", "tags": ["database", "cypher"]}',
            "score": 0.85
        }
        
        mock_connector.run.return_value = [mock_result1, mock_result2]
        
        store = Neo4jDocumentStore(TEST_CONFIG)
        
        # Reset mock to clear initialization calls
        mock_connector.reset_mock()
        mock_embedding_model.reset_mock()
        
        # Search for documents
        results = store.search_documents(TEST_QUERY, top_k=2)
        
        # Check that embed_text was called with the query
        mock_embedding_model.embed_text.assert_called_once_with(TEST_QUERY)
        
        # Check that the connector's run method was called with the right parameters
        mock_connector.run.assert_called_once()
        
        args, kwargs = mock_connector.run.call_args
        
        # Verify the query includes the vector index name
        assert f"'{TEST_CONFIG['vector_index_name']}'" in args[0]
        
        # Verify parameters
        assert kwargs["k"] == 2
        assert kwargs["embedding"] == TEST_QUERY_EMBEDDING
        
        # Verify results
        assert len(results) == 2
        assert results[0]["id"] == "doc1"
        assert results[0]["score"] == 0.95
        assert results[1]["id"] == "doc2"
        assert results[1]["score"] == 0.85
        
        # Verify metadata parsing
        assert isinstance(results[0]["metadata"], dict)
        assert results[0]["metadata"]["type"] == "test"
        assert "database" in results[0]["metadata"]["tags"]
    
    def test_delete_documents(self, mock_embedding_model, mock_connector):
        """Test deleting documents from the store."""
        store = Neo4jDocumentStore(TEST_CONFIG)
        
        # Reset mock to clear initialization calls
        mock_connector.reset_mock()
        
        # Delete documents
        doc_ids = ["doc1", "doc2"]
        store.delete_documents(doc_ids)
        
        # Check that the connector's run method was called with the right parameters
        mock_connector.run.assert_called_once()
        
        args, kwargs = mock_connector.run.call_args
        
        # Verify the query includes the document label
        assert f":{TEST_CONFIG['document_label']}" in args[0]
        
        # Verify parameters
        assert kwargs["ids"] == doc_ids
    
    def test_get_document(self, mock_embedding_model, mock_connector):
        """Test retrieving a document by ID."""
        # Set up the mock to return a document
        mock_result = {
            "id": "doc1",
            "content": "This is a test document about Neo4j.",
            "title": "Neo4j Test",
            "source": "test",
            "metadata": '{"type": "test", "tags": ["database", "graph"]}'
        }
        
        mock_connector.run.return_value = [mock_result]
        
        store = Neo4jDocumentStore(TEST_CONFIG)
        
        # Reset mock to clear initialization calls
        mock_connector.reset_mock()
        
        # Get document
        doc = store.get_document("doc1")
        
        # Check that the connector's run method was called with the right parameters
        mock_connector.run.assert_called_once()
        
        args, kwargs = mock_connector.run.call_args
        
        # Verify the query includes the document label
        assert f":{TEST_CONFIG['document_label']}" in args[0]
        
        # Verify parameters
        assert kwargs["id"] == "doc1"
        
        # Verify result
        assert doc["id"] == "doc1"
        assert doc["content"] == "This is a test document about Neo4j."
        
        # Verify metadata parsing
        assert isinstance(doc["metadata"], dict)
        assert doc["metadata"]["type"] == "test"
        assert "database" in doc["metadata"]["tags"]
    
    def test_get_document_not_found(self, mock_embedding_model, mock_connector):
        """Test retrieving a document that doesn't exist."""
        # Set up the mock to return no results
        mock_connector.run.return_value = []
        
        store = Neo4jDocumentStore(TEST_CONFIG)
        
        # Reset mock to clear initialization calls
        mock_connector.reset_mock()
        
        # Get document
        doc = store.get_document("nonexistent")
        
        # Verify result is None
        assert doc is None


# For integration testing with a real Neo4j instance (disabled by default)
@pytest.mark.skip(reason="Requires a running Neo4j instance")
class TestNeo4jDocumentStoreIntegration:
    """Integration tests for Neo4jDocumentStore with a real Neo4j instance."""
    
    @pytest.fixture
    def document_store(self):
        """Create a document store for testing."""
        # Use environment variables for connection information if available
        uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        username = os.environ.get("NEO4J_USERNAME", "neo4j")
        password = os.environ.get("NEO4J_PASSWORD", "password")
        database = os.environ.get("NEO4J_DATABASE", "neo4j")
        
        config = {
            "database": {
                "uri": uri,
                "username": username,
                "password": password,
                "database": database
            },
            "embedding": {
                "model": "test-embeddings",
                "dimensions": 4
            },
            "vector_index_name": "test_document_embeddings",
            "document_label": "TestDocument",
            "embedding_dimension": 4
        }
        
        # Mock the embedding model for consistent results
        with patch('app.llm.factory.LLMFactory.create_embedding_client') as mock_factory:
            mock_model = MagicMock()
            mock_model.embed_texts.return_value = TEST_EMBEDDINGS
            mock_model.embed_text.return_value = TEST_QUERY_EMBEDDING
            
            mock_factory.return_value = mock_model
            
            store = Neo4jDocumentStore(config)
            
            # Clear any existing test documents
            store.connector.run(f"MATCH (d:{config['document_label']}) DETACH DELETE d")
            
            yield store
            
            # Clean up test documents
            store.connector.run(f"MATCH (d:{config['document_label']}) DETACH DELETE d")
            store.close()
    
    def test_add_and_get_documents_integration(self, document_store):
        """Test adding and retrieving documents from a real Neo4j instance."""
        # Add documents
        document_store.add_documents(TEST_DOCUMENTS)
        
        # Get document
        doc = document_store.get_document("doc1")
        
        # Verify document properties
        assert doc["id"] == "doc1"
        assert doc["content"] == "This is a test document about Neo4j."
        assert doc["title"] == "Neo4j Test"
        assert doc["source"] == "test"
        assert isinstance(doc["metadata"], dict)
        assert doc["metadata"]["type"] == "test"
        assert "database" in doc["metadata"]["tags"]
    
    def test_search_documents_integration(self, document_store):
        """Test searching for documents in a real Neo4j instance."""
        # Add documents
        document_store.add_documents(TEST_DOCUMENTS)
        
        # Search for documents
        results = document_store.search_documents(TEST_QUERY, top_k=2)
        
        # Verify results
        assert len(results) == 2
        
        # Documents should be returned in order of score (descending)
        assert results[0]["score"] >= results[1]["score"]
    
    def test_delete_documents_integration(self, document_store):
        """Test deleting documents from a real Neo4j instance."""
        # Add documents
        document_store.add_documents(TEST_DOCUMENTS)
        
        # Delete one document
        document_store.delete_documents(["doc1"])
        
        # Verify document was deleted
        doc1 = document_store.get_document("doc1")
        doc2 = document_store.get_document("doc2")
        
        assert doc1 is None
        assert doc2 is not None 
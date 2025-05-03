"""
Copyright (c) 2024 dev1ender

This file is part of conversDB.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.

Agent interfaces for the conversDB application.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple


class SchemaAgentInterface(ABC):
    """Interface for schema agent that extracts and manages database schema."""
    
    @abstractmethod
    def extract_schema(self) -> Dict[str, Any]:
        """Extract the database schema and return it as a dictionary."""
        pass
    
    @abstractmethod
    def get_schema_as_json(self) -> str:
        """Get the database schema as a JSON string."""
        pass
    
    @abstractmethod
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get schema information for a specific table."""
        pass
    
    @abstractmethod
    def get_relevant_tables(self, question: str) -> List[str]:
        """Get tables relevant to a natural language question."""
        pass
    
    @abstractmethod
    def set_embedding_model(self, model_name: str, config: Dict[str, Any]) -> None:
        """Set embedding model for schema agent."""
        pass
    
    @abstractmethod
    def compute_embeddings(self) -> None:
        """Compute embeddings for schema elements."""
        pass
    
    @abstractmethod
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        pass


class PromptAgentInterface(ABC):
    """Interface for prompt agent that creates prompts for LLM."""
    
    @abstractmethod
    def build_prompt(self, user_question: str, relevant_tables: List[str], 
                     context_docs: Optional[List[Dict[str, Any]]] = None) -> str:
        """Build a prompt for the LLM to generate SQL from a question."""
        pass
    
    @abstractmethod
    def build_error_correction_prompt(self, sql_query: str, error: str, schema_context: str) -> str:
        """Build a prompt for error correction."""
        pass


class QueryGeneratorInterface(ABC):
    """Interface for query generator that generates SQL from natural language."""
    
    @abstractmethod
    def generate(self, user_question: str, context_docs: Optional[List[Dict[str, Any]]] = None) -> str:
        """Generate a SQL query from a natural language question."""
        pass
    
    @abstractmethod
    def validate_sql(self, query: str, retry_count: int = 0) -> Tuple[bool, Optional[str]]:
        """Validate a SQL query."""
        pass


class QueryExecutorInterface(ABC):
    """Interface for query executor that runs SQL queries."""
    
    @abstractmethod
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results."""
        pass


class DocumentStoreAgentInterface(ABC):
    """Interface for the document store agent."""
    
    @abstractmethod
    def load_documents_from_directory(self, directory_path: str) -> None:
        """Load and process documents from a directory."""
        pass
    
    @abstractmethod
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Add documents to the document store."""
        pass
    
    @abstractmethod
    def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for documents relevant to query."""
        pass 
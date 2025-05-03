"""
Agent interfaces for the RAG-POC application.
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


class PromptAgentInterface(ABC):
    """Interface for prompt agent that creates prompts for LLM."""
    
    @abstractmethod
    def build_prompt(self, user_question: str, relevant_tables: List[str]) -> str:
        """Build a prompt for the LLM to generate SQL from a question."""
        pass
    
    @abstractmethod
    def build_error_correction_prompt(self, sql_query: str, error: str, schema_context: str) -> str:
        """Build a prompt for error correction."""
        pass


class QueryGeneratorInterface(ABC):
    """Interface for query generator that generates SQL from natural language."""
    
    @abstractmethod
    def generate(self, user_question: str) -> str:
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
"""
Application interface for the RAG-POC application.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class NLToSQLAppInterface(ABC):
    """Interface for the main NL to SQL application."""
    
    @abstractmethod
    def process_question(self, question: str) -> Dict[str, Any]:
        """Process a natural language question and return the SQL and results."""
        pass
    
    @abstractmethod
    def seed_database(self, script_path: Optional[str] = None) -> None:
        """Seed the database with sample data."""
        pass
    
    @abstractmethod
    def get_schema_info(self) -> str:
        """Get database schema information as a JSON string."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close database connections and clean up resources."""
        pass 
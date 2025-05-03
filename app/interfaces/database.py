"""
Database interfaces for the RAG-POC application.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class DatabaseConnector(ABC):
    """Abstract base class for database connectors."""
    
    @abstractmethod
    def connect(self) -> None:
        """Connect to the database."""
        pass
    
    @abstractmethod
    def seed_database(self, script_path: Optional[str] = None) -> None:
        """Seed the database with sample data."""
        pass
    
    @abstractmethod
    def get_table_names(self) -> List[str]:
        """Get all table names from the database."""
        pass
    
    @abstractmethod
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get schema information for a specific table."""
        pass
    
    @abstractmethod
    def run(self, query: str) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close the database connection."""
        pass 
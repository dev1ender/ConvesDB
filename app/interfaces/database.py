"""
Copyright (c) 2024 dev1ender

This file is part of conversDB.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.

Database interfaces for the conversDB application.
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
    
    @abstractmethod
    def get_view_names(self) -> List[str]:
        """Get all view names from the database."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the database connection is active."""
        pass 
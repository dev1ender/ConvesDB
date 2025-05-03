"""
Copyright (c) 2024 dev1ender

This file is part of conversDB.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.

Application interface for the conversDB application.
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
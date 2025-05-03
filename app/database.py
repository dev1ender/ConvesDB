from abc import ABC, abstractmethod
import sqlite3
from typing import List, Dict, Any, Optional, Tuple

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


class SQLiteConnector(DatabaseConnector):
    """SQLite implementation of DatabaseConnector."""
    
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
    
    def connect(self) -> None:
        """Connect to SQLite database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
    
    def seed_database(self, script_path: Optional[str] = None) -> None:
        """Seed the database with sample data."""
        if not self.conn:
            self.connect()
            
        if script_path:
            with open(script_path, 'r') as f:
                self.cursor.executescript(f.read())
        else:
            # Default sample data if no script is provided
            self.cursor.executescript("""
            -- Create tables
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                sign_up_date DATE
            );
            
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                category TEXT
            );
            
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY,
                customer_id INTEGER,
                order_date DATE,
                total_amount REAL,
                FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
            );
            
            CREATE TABLE IF NOT EXISTS order_items (
                order_item_id INTEGER PRIMARY KEY,
                order_id INTEGER,
                product_id INTEGER,
                quantity INTEGER,
                price REAL,
                FOREIGN KEY (order_id) REFERENCES orders (order_id),
                FOREIGN KEY (product_id) REFERENCES products (product_id)
            );
            
            -- Insert sample data
            INSERT OR IGNORE INTO customers (name, email, sign_up_date) VALUES
                ('John Doe', 'john@example.com', '2023-01-15'),
                ('Jane Smith', 'jane@example.com', '2023-02-20'),
                ('Bob Johnson', 'bob@example.com', '2023-03-10');
                
            INSERT OR IGNORE INTO products (name, price, category) VALUES
                ('Laptop', 1200.00, 'Electronics'),
                ('Smartphone', 800.00, 'Electronics'),
                ('Headphones', 150.00, 'Accessories'),
                ('Notebook', 20.00, 'Office Supplies');
                
            INSERT OR IGNORE INTO orders (customer_id, order_date, total_amount) VALUES
                (1, '2023-03-15', 1350.00),
                (2, '2023-04-20', 800.00),
                (1, '2023-05-10', 170.00);
                
            INSERT OR IGNORE INTO order_items (order_id, product_id, quantity, price) VALUES
                (1, 1, 1, 1200.00),
                (1, 3, 1, 150.00),
                (2, 2, 1, 800.00),
                (3, 3, 1, 150.00),
                (3, 4, 1, 20.00);
            """)
        
        self.conn.commit()
    
    def get_table_names(self) -> List[str]:
        """Get all table and view names from the SQLite database."""
        if not self.conn:
            self.connect()
            
        # Query to get both tables and views
        self.cursor.execute("""
        SELECT name, type FROM sqlite_master 
        WHERE type IN ('table', 'view') 
        AND name NOT LIKE 'sqlite_%'
        ORDER BY type, name
        """)
        
        return [row['name'] for row in self.cursor.fetchall()]
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get schema information for a specific table or view."""
        if not self.conn:
            self.connect()
            
        # Check if this is a view or table
        self.cursor.execute("""
        SELECT type FROM sqlite_master 
        WHERE name = ? AND type IN ('table', 'view')
        """, (table_name,))
        
        result = self.cursor.fetchone()
        if not result:
            return []
            
        object_type = result[0]
            
        # Get column information
        self.cursor.execute(f"PRAGMA table_info({table_name})")
        schema = []
        for row in self.cursor.fetchall():
            column_info = dict(row)
            
            # Only get foreign key information for tables (not views)
            if object_type == 'table':
                # Get foreign key information
                self.cursor.execute(f"PRAGMA foreign_key_list({table_name})")
                fk_data = self.cursor.fetchall()
                
                # Find foreign keys for this column
                foreign_keys = []
                for fk in fk_data:
                    if fk['from'] == column_info['name']:
                        foreign_keys.append({
                            'table': fk['table'],
                            'column': fk['to']
                        })
                
                if foreign_keys:
                    column_info['foreign_keys'] = foreign_keys
                    
            schema.append(column_info)
            
        return schema
    
    def run(self, query: str) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results."""
        if not self.conn:
            self.connect()
            
        try:
            self.cursor.execute(query)
            
            # For SELECT queries
            if query.strip().lower().startswith('select'):
                results = []
                for row in self.cursor.fetchall():
                    results.append(dict(row))
                return results
            
            # For other queries (INSERT, UPDATE, DELETE)
            self.conn.commit()
            return []
            
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Database error: {str(e)}")
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None 
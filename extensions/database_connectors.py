"""
Additional database connectors for the NLP-to-SQL system.
"""
from typing import List, Dict, Any, Optional, Tuple
from app.database import DatabaseConnector

class PostgreSQLConnector(DatabaseConnector):
    """PostgreSQL implementation of DatabaseConnector."""
    
    def __init__(self, connection_string: str):
        """Initialize PostgreSQL connector.
        
        Args:
            connection_string: PostgreSQL connection string
                Format: postgresql://username:password@host:port/database
        """
        self.connection_string = connection_string
        self.conn = None
        self.cursor = None
    
    def connect(self) -> None:
        """Connect to PostgreSQL database."""
        try:
            import psycopg2
            import psycopg2.extras
            
            self.conn = psycopg2.connect(self.connection_string)
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
        except ImportError:
            raise ImportError("psycopg2 package not installed. Install with 'pip install psycopg2-binary'")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to PostgreSQL database: {str(e)}")
    
    def seed_database(self, script_path: Optional[str] = None) -> None:
        """Seed the database with sample data."""
        if not self.conn:
            self.connect()
            
        try:
            if script_path:
                with open(script_path, 'r') as f:
                    self.cursor.execute(f.read())
            else:
                # Default sample data if no script is provided
                self.cursor.execute("""
                -- Create tables
                CREATE TABLE IF NOT EXISTS customers (
                    customer_id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE,
                    sign_up_date DATE
                );
                
                CREATE TABLE IF NOT EXISTS products (
                    product_id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    price DECIMAL(10, 2) NOT NULL,
                    category TEXT
                );
                
                CREATE TABLE IF NOT EXISTS orders (
                    order_id SERIAL PRIMARY KEY,
                    customer_id INTEGER REFERENCES customers(customer_id),
                    order_date DATE,
                    total_amount DECIMAL(10, 2)
                );
                
                CREATE TABLE IF NOT EXISTS order_items (
                    order_item_id SERIAL PRIMARY KEY,
                    order_id INTEGER REFERENCES orders(order_id),
                    product_id INTEGER REFERENCES products(product_id),
                    quantity INTEGER,
                    price DECIMAL(10, 2)
                );
                
                -- Insert sample data (only if tables are empty)
                INSERT INTO customers (name, email, sign_up_date)
                SELECT 'John Doe', 'john@example.com', '2023-01-15'
                WHERE NOT EXISTS (SELECT 1 FROM customers LIMIT 1);
                
                INSERT INTO customers (name, email, sign_up_date)
                SELECT 'Jane Smith', 'jane@example.com', '2023-02-20'
                WHERE NOT EXISTS (SELECT 1 FROM customers LIMIT 1 OFFSET 1);
                
                INSERT INTO customers (name, email, sign_up_date)
                SELECT 'Bob Johnson', 'bob@example.com', '2023-03-10'
                WHERE NOT EXISTS (SELECT 1 FROM customers LIMIT 1 OFFSET 2);
                
                INSERT INTO products (name, price, category)
                SELECT 'Laptop', 1200.00, 'Electronics'
                WHERE NOT EXISTS (SELECT 1 FROM products LIMIT 1);
                
                INSERT INTO products (name, price, category)
                SELECT 'Smartphone', 800.00, 'Electronics'
                WHERE NOT EXISTS (SELECT 1 FROM products LIMIT 1 OFFSET 1);
                
                INSERT INTO products (name, price, category)
                SELECT 'Headphones', 150.00, 'Accessories'
                WHERE NOT EXISTS (SELECT 1 FROM products LIMIT 1 OFFSET 2);
                
                INSERT INTO products (name, price, category)
                SELECT 'Notebook', 20.00, 'Office Supplies'
                WHERE NOT EXISTS (SELECT 1 FROM products LIMIT 1 OFFSET 3);
                
                -- Only create orders if none exist
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM orders LIMIT 1) THEN
                        INSERT INTO orders (customer_id, order_date, total_amount) VALUES
                            (1, '2023-03-15', 1350.00),
                            (2, '2023-04-20', 800.00),
                            (1, '2023-05-10', 170.00);
                            
                        INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
                            (1, 1, 1, 1200.00),
                            (1, 3, 1, 150.00),
                            (2, 2, 1, 800.00),
                            (3, 3, 1, 150.00),
                            (3, 4, 1, 20.00);
                    END IF;
                END $$;
                """)
            
            self.conn.commit()
            
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Failed to seed database: {str(e)}")
    
    def get_table_names(self) -> List[str]:
        """Get all table names from the PostgreSQL database."""
        if not self.conn:
            self.connect()
        
        query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        """
        
        self.cursor.execute(query)
        return [row['table_name'] for row in self.cursor.fetchall()]
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get schema information for a specific table."""
        if not self.conn:
            self.connect()
        
        # Get column information
        column_query = """
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM
            information_schema.columns
        WHERE
            table_name = %s
        ORDER BY
            ordinal_position
        """
        
        self.cursor.execute(column_query, (table_name,))
        columns = self.cursor.fetchall()
        
        # Get primary key information
        pk_query = """
        SELECT
            kcu.column_name
        FROM
            information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
        WHERE
            tc.constraint_type = 'PRIMARY KEY'
            AND tc.table_name = %s
        """
        
        self.cursor.execute(pk_query, (table_name,))
        pk_columns = [row['column_name'] for row in self.cursor.fetchall()]
        
        # Get foreign key information
        fk_query = """
        SELECT
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM
            information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
        WHERE
            tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name = %s
        """
        
        self.cursor.execute(fk_query, (table_name,))
        fk_data = self.cursor.fetchall()
        
        # Build schema information
        schema = []
        for column in columns:
            column_info = {
                'name': column['column_name'],
                'type': column['data_type'],
                'notnull': column['is_nullable'] == 'NO'
            }
            
            # Check if column is a primary key
            if column['column_name'] in pk_columns:
                column_info['pk'] = 1
            
            # Check for foreign keys
            foreign_keys = []
            for fk in fk_data:
                if fk['column_name'] == column['column_name']:
                    foreign_keys.append({
                        'table': fk['foreign_table_name'],
                        'column': fk['foreign_column_name']
                    })
            
            if foreign_keys:
                column_info['foreign_keys'] = foreign_keys
            
            schema.append(column_info)
        
        return schema
    
    def run(self, query: str) -> Tuple[List[Dict[str, Any]], Optional[str]]:
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
                return results, None
            
            # For other queries (INSERT, UPDATE, DELETE)
            self.conn.commit()
            return [], None
            
        except Exception as e:
            self.conn.rollback()
            return [], str(e)
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None 
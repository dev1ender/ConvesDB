import pytest

def test_database_summary(db_conn):
    """Generate a summary of database tables"""
    cursor = db_conn.cursor()
    
    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    summary = {}
    for table in tables:
        table_name = table['name']
        if table_name.startswith('sqlite_'):
            continue
            
        cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
        count = cursor.fetchone()['count']
        summary[table_name] = count
    
    # Print summary
    print("\n=== Database Summary ===")
    for table, count in summary.items():
        print(f"{table}: {count} records")
    
    assert len(summary) > 0
    assert "offices" in summary
    assert "employees" in summary
    assert "customers" in summary
    assert "products" in summary
    assert "inventory" in summary
    assert "orders" in summary
    
    # Get list of views
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view';")
    views = cursor.fetchall()
    
    print("\n=== Views ===")
    for view in views:
        print(f"{view['name']}")
    
    # Check there are some views
    assert len(views) > 0
    
def test_table_relationships(db_conn):
    """Test database table relationships"""
    cursor = db_conn.cursor()
    
    # Test office-employee relationship
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM offices o
        JOIN employees e ON o.office_id = e.office_id
    """)
    count = cursor.fetchone()['count']
    assert count > 0  # Should have employees related to offices
    
    # Test customer-order relationship
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
    """)
    count = cursor.fetchone()['count']
    assert count > 0  # Should have orders related to customers
    
    # Test product-inventory relationship
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM products p
        JOIN inventory i ON p.product_id = i.product_id
    """)
    count = cursor.fetchone()['count']
    assert count > 0  # Should have inventory related to products
    
    # Test order-order item relationship
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
    """)
    count = cursor.fetchone()['count']
    assert count > 0  # Should have order items related to orders 
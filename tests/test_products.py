import pytest

def test_product_categories(db_conn):
    """Test product categorization"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT category, COUNT(*) as count
        FROM products
        GROUP BY category
    """)
    categories = {row['category']: row['count'] for row in cursor.fetchall()}
    assert len(categories) > 0
    assert "Electronics" in categories

def test_product_pricing(db_conn):
    """Test product pricing statistics"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT category, AVG(price) as avg_price
        FROM products
        GROUP BY category
    """)
    avg_prices = {row['category']: row['avg_price'] for row in cursor.fetchall()}
    assert len(avg_prices) > 0
    for category, avg_price in avg_prices.items():
        assert avg_price > 0

def test_product_status_distribution(db_conn):
    """Test product status distribution"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM products
        GROUP BY status
    """)
    statuses = {row['status']: row['count'] for row in cursor.fetchall()}
    assert "active" in statuses  # Should have active products
    assert statuses["active"] > 0  # Most products should be active

def test_featured_products(db_conn):
    """Test featured product selection"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT product_id, name, category, is_featured
        FROM products
        WHERE is_featured = 1
    """)
    featured = cursor.fetchall()
    assert len(featured) > 0  # Should have at least one featured product 
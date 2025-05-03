import pytest

def test_customer_account_types(db_conn):
    """Test customer account type distribution"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT account_type, COUNT(*) as count
        FROM customers
        GROUP BY account_type
    """)
    results = {row['account_type']: row['count'] for row in cursor.fetchall()}
    assert "standard" in results
    assert "premium" in results
    assert "enterprise" in results

def test_customer_orders(db_conn):
    """Test customer order relationship"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT c.customer_id, c.first_name, c.last_name, COUNT(o.order_id) as order_count
        FROM customers c
        LEFT JOIN orders o ON c.customer_id = o.customer_id
        GROUP BY c.customer_id
        ORDER BY order_count DESC
        LIMIT 10
    """)
    top_customers = cursor.fetchall()
    assert len(top_customers) == 10
    assert top_customers[0]['order_count'] > 0

def test_customer_statuses(db_conn):
    """Test customer status distribution"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM customers
        GROUP BY status
    """)
    statuses = {row['status']: row['count'] for row in cursor.fetchall()}
    assert "active" in statuses
    assert statuses["active"] > 0  # Most customers should be active

def test_customer_preferences(db_conn):
    """Test customer preferences data"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT customer_id, preferences
        FROM customers
        WHERE preferences IS NOT NULL
        LIMIT 10
    """)
    customers_with_prefs = cursor.fetchall()
    assert len(customers_with_prefs) > 0
    for customer in customers_with_prefs:
        assert customer['preferences'].startswith('{')  # Preferences stored as JSON 
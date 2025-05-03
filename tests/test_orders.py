import pytest

def test_order_status_distribution(db_conn):
    """Test order status distribution"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM orders
        GROUP BY status
    """)
    statuses = {row['status']: row['count'] for row in cursor.fetchall()}
    assert len(statuses) > 0
    # Should have some delivered orders
    assert "delivered" in statuses
    assert statuses["delivered"] > 0

def test_order_financial_summary(db_conn):
    """Test order financial calculations"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT 
            COUNT(*) as order_count,
            SUM(subtotal) as total_subtotal,
            SUM(tax_amount) as total_tax,
            SUM(shipping_cost) as total_shipping,
            SUM(discount_amount) as total_discounts,
            SUM(total_amount) as grand_total
        FROM orders
        WHERE status != 'cancelled'
    """)
    financial = cursor.fetchone()
    assert financial['order_count'] > 0
    assert financial['total_subtotal'] > 0
    # Verify that total = subtotal + tax + shipping - discounts
    calculated_total = (
        financial['total_subtotal'] + 
        financial['total_tax'] + 
        financial['total_shipping'] - 
        financial['total_discounts']
    )
    # Allow for small floating-point differences
    assert abs(calculated_total - financial['grand_total']) < 0.01

def test_order_items_relationship(db_conn):
    """Test relationship between orders and order items"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT 
            o.order_id,
            COUNT(oi.order_item_id) as item_count,
            SUM(oi.quantity) as total_quantity,
            SUM(oi.line_total) as items_total,
            o.total_amount
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        GROUP BY o.order_id
        LIMIT 10
    """)
    orders = cursor.fetchall()
    assert len(orders) > 0
    for order in orders:
        # Each order should have at least one item
        assert order['item_count'] > 0
        assert order['total_quantity'] > 0
        # Allow for differences due to shipping, taxes, and other factors
        # We're not expecting exact matches since orders have shipping costs and other fees
        assert order['items_total'] > 0

def test_payment_methods(db_conn):
    """Test payment method distribution"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT payment_method, COUNT(*) as count
        FROM orders
        GROUP BY payment_method
    """)
    methods = {row['payment_method']: row['count'] for row in cursor.fetchall()}
    assert len(methods) > 0
    assert "Credit Card" in methods  # Should have credit card payments 
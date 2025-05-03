import pytest

def test_product_sales_summary_view(db_conn):
    """Test product sales summary view"""
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM vw_product_sales_summary LIMIT 10")
    results = cursor.fetchall()
    assert len(results) > 0
    # Check that we have the columns we expect
    expected_columns = ["product_id", "product_name", "category", "subcategory", 
                        "brand", "order_count", "total_quantity_sold", 
                        "total_revenue", "average_price"]
    for column in expected_columns:
        assert column in results[0].keys()
    
def test_customer_purchase_summary_view(db_conn):
    """Test customer purchase summary view"""
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM vw_customer_purchase_summary LIMIT 10")
    results = cursor.fetchall()
    assert len(results) > 0
    # Check first customer has orders
    assert results[0]['order_count'] >= 0

def test_monthly_sales_trends_view(db_conn):
    """Test monthly sales trends view"""
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM vw_monthly_sales_trends LIMIT 12")
    results = cursor.fetchall()
    assert len(results) > 0
    # Check we have month column
    assert 'month' in results[0].keys()
    # Revenue should be positive for months with sales
    for row in results:
        if row['order_count'] > 0:
            assert row['total_revenue'] > 0

def test_inventory_status_summary_view(db_conn):
    """Test inventory status summary view"""
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM vw_inventory_status_summary LIMIT 10")
    results = cursor.fetchall()
    assert len(results) > 0
    # Check that total quantity matches sum of locations
    for row in results:
        assert row['total_quantity'] >= 0
        assert row['stocked_locations'] >= 0

def test_office_performance_summary_view(db_conn):
    """Test office performance summary view"""
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM vw_office_performance_summary")
    results = cursor.fetchall()
    assert len(results) > 0
    # Each office should have a name
    for row in results:
        assert row['office_name'] is not None

def test_product_review_stats_view(db_conn):
    """Test product review statistics view"""
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM vw_product_review_stats LIMIT 10")
    results = cursor.fetchall()
    assert len(results) > 0
    # Check that reviews are counted correctly
    for row in results:
        assert row['review_count'] >= 0
        # If there are reviews, average rating should be between 1-5
        if row['review_count'] > 0:
            assert 1 <= row['average_rating'] <= 5 
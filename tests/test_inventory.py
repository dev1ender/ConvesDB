import pytest

def test_inventory_levels(db_conn):
    """Test inventory levels across locations"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT 
            SUM(quantity) as total_quantity,
            AVG(quantity) as avg_quantity,
            COUNT(*) as inventory_records
        FROM inventory
    """)
    inventory_summary = cursor.fetchone()
    assert inventory_summary['total_quantity'] > 0
    assert inventory_summary['inventory_records'] > 0

def test_inventory_by_office(db_conn):
    """Test inventory distribution by office"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT 
            o.name as office_name,
            COUNT(i.inventory_id) as inventory_records,
            SUM(i.quantity) as total_quantity
        FROM inventory i
        JOIN offices o ON i.office_id = o.office_id
        GROUP BY o.name
        ORDER BY total_quantity DESC
    """)
    office_inventory = cursor.fetchall()
    assert len(office_inventory) > 0
    # Main warehouses should have most inventory
    assert office_inventory[0]['total_quantity'] > 0

def test_reorder_status(db_conn):
    """Test inventory reorder status"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN quantity <= reorder_level THEN 1 ELSE 0 END) as needs_reorder
        FROM inventory
    """)
    reorder_status = cursor.fetchone()
    assert reorder_status['total'] > 0
    # Some items should need reordering, but not all
    assert reorder_status['needs_reorder'] > 0
    assert reorder_status['needs_reorder'] < reorder_status['total']

def test_inventory_movements(db_conn):
    """Test inventory movements data"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT movement_type, COUNT(*) as count
        FROM inventory_movements
        GROUP BY movement_type
    """)
    movement_types = {row['movement_type']: row['count'] for row in cursor.fetchall()}
    assert len(movement_types) > 0
    assert "purchase" in movement_types
    assert "sale" in movement_types 
import pytest

def test_list_all_offices(db_conn):
    """Test retrieving all offices"""
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM offices")
    offices = cursor.fetchall()
    assert len(offices) >= 10
    assert offices[0]['name'] == "Global Headquarters"

def test_office_manager_relationship(db_conn):
    """Test office-manager relationships"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT o.office_id, o.name, e.first_name, e.last_name
        FROM offices o
        JOIN employees e ON o.manager_id = e.employee_id
        WHERE o.office_id = 1
    """)
    office = cursor.fetchone()
    assert office is not None
    assert office['name'] == "Global Headquarters"

def test_offices_by_country(db_conn):
    """Test offices grouped by country"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT country, COUNT(*) as count
        FROM offices
        GROUP BY country
        ORDER BY count DESC
    """)
    countries = cursor.fetchall()
    assert len(countries) > 0
    # USA should have the most offices based on seed data
    assert countries[0]['country'] == "USA"

def test_office_capacity(db_conn):
    """Test office capacity statistics"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT SUM(capacity) as total_capacity,
               AVG(capacity) as avg_capacity,
               MAX(capacity) as max_capacity,
               MIN(capacity) as min_capacity
        FROM offices
    """)
    capacity = cursor.fetchone()
    assert capacity['total_capacity'] > 1000  # Based on seed data
    assert capacity['max_capacity'] > capacity['min_capacity'] 
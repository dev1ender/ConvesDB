import pytest

def test_employee_count(db_conn):
    """Test employee count by department"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT department, COUNT(*) as count
        FROM employees
        GROUP BY department
    """)
    departments = {row['department']: row['count'] for row in cursor.fetchall()}
    assert len(departments) > 0
    assert "Technology" in departments
    assert "Executive" in departments

def test_employee_salary_range(db_conn):
    """Test employee salary ranges"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT MIN(salary) as min_salary, 
               MAX(salary) as max_salary, 
               AVG(salary) as avg_salary
        FROM employees
    """)
    salary_data = cursor.fetchone()
    assert salary_data['min_salary'] > 0
    assert salary_data['max_salary'] > salary_data['min_salary']

def test_employee_by_office(db_conn):
    """Test employee distribution by office"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT o.name as office_name, COUNT(e.employee_id) as emp_count
        FROM employees e
        JOIN offices o ON e.office_id = o.office_id
        GROUP BY o.name
        ORDER BY emp_count DESC
    """)
    office_employees = cursor.fetchall()
    assert len(office_employees) > 0
    # HQ should have the most employees
    assert "Headquarters" in office_employees[0]['office_name']

def test_employee_skills(db_conn):
    """Test employee skills data"""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT employee_id, skills
        FROM employees
        WHERE skills IS NOT NULL
        LIMIT 10
    """)
    employees_with_skills = cursor.fetchall()
    assert len(employees_with_skills) > 0
    for employee in employees_with_skills:
        assert employee['skills'].startswith('[')  # Skills are stored as JSON arrays 
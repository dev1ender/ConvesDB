"""
Complex database seeding script with realistic data.
Creates 10 tables with various data types, relationships, constraints, and indexes.
"""
import sqlite3
from datetime import datetime, timedelta, date
import os
import json
from pathlib import Path
import random

def create_database_schema(conn):
    """Create the database schema with 10 tables and their relationships."""
    cursor = conn.cursor()
    
    # Drop existing tables if they exist
    cursor.executescript("""
    DROP TABLE IF EXISTS transaction_logs;
    DROP TABLE IF EXISTS order_items;
    DROP TABLE IF EXISTS product_reviews;
    DROP TABLE IF EXISTS orders;
    DROP TABLE IF EXISTS inventory_movements;
    DROP TABLE IF EXISTS inventory;
    DROP TABLE IF EXISTS products;
    DROP TABLE IF EXISTS customers;
    DROP TABLE IF EXISTS employees;
    DROP TABLE IF EXISTS offices;
    """)
    
    # Create tables with various constraints, data types, and relationships
    cursor.executescript("""
    -- 1. Offices Table
    CREATE TABLE offices (
        office_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        address TEXT NOT NULL,
        city TEXT NOT NULL,
        state TEXT,
        country TEXT NOT NULL,
        postal_code TEXT,
        phone TEXT,
        email TEXT UNIQUE,
        website_url TEXT,
        opening_date DATE NOT NULL,
        status TEXT CHECK(status IN ('active', 'closed', 'under_renovation', 'planned')) NOT NULL,
        geo_location TEXT, -- Stored as JSON: {"lat": 00.000, "lng": 00.000}
        operating_hours TEXT, -- Stored as JSON
        last_renovation_date DATE,
        manager_id INTEGER, -- Will be updated after employees table is created
        tax_id TEXT UNIQUE,
        capacity INTEGER CHECK(capacity > 0),
        is_headquarters BOOLEAN DEFAULT 0
    );
    
    -- Add indexes
    CREATE INDEX idx_offices_country ON offices(country);
    CREATE INDEX idx_offices_status ON offices(status);
    
    -- 2. Employees Table
    CREATE TABLE employees (
        employee_id INTEGER PRIMARY KEY,
        office_id INTEGER NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        hire_date DATE NOT NULL,
        termination_date DATE,
        position TEXT NOT NULL,
        department TEXT NOT NULL,
        manager_id INTEGER,
        salary REAL CHECK(salary > 0),
        birth_date DATE,
        address TEXT,
        city TEXT,
        state TEXT,
        country TEXT,
        emergency_contact TEXT, -- Stored as JSON
        skills TEXT, -- Stored as JSON array
        performance_rating REAL CHECK(performance_rating BETWEEN 1 AND 5),
        FOREIGN KEY (office_id) REFERENCES offices(office_id),
        FOREIGN KEY (manager_id) REFERENCES employees(employee_id)
    );
    
    -- Add indexes
    CREATE INDEX idx_employees_office_id ON employees(office_id);
    CREATE INDEX idx_employees_department ON employees(department);
    CREATE INDEX idx_employees_manager_id ON employees(manager_id);
    
    -- 3. Customers Table
    CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login_timestamp TIMESTAMP,
        birth_date DATE,
        address TEXT,
        city TEXT,
        state TEXT,
        country TEXT,
        postal_code TEXT,
        status TEXT CHECK(status IN ('active', 'inactive', 'suspended', 'pending')) NOT NULL DEFAULT 'active',
        marketing_consent BOOLEAN DEFAULT 0,
        referral_source TEXT,
        loyalty_points INTEGER DEFAULT 0,
        preferences TEXT, -- Stored as JSON
        password_hash TEXT NOT NULL,
        account_type TEXT CHECK(account_type IN ('standard', 'premium', 'enterprise')) DEFAULT 'standard',
        ip_address TEXT
    );
    
    -- Add indexes
    CREATE INDEX idx_customers_email ON customers(email);
    CREATE INDEX idx_customers_registration_date ON customers(registration_date);
    CREATE INDEX idx_customers_status ON customers(status);
    CREATE INDEX idx_customers_account_type ON customers(account_type);
    
    -- 4. Products Table
    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        sku TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL,
        subcategory TEXT,
        brand TEXT NOT NULL,
        price REAL CHECK(price >= 0) NOT NULL,
        cost REAL CHECK(cost >= 0) NOT NULL,
        weight REAL,
        dimensions TEXT, -- Stored as JSON: {"length": 10, "width": 5, "height": 2}
        launch_date DATE,
        discontinuation_date DATE,
        is_taxable BOOLEAN DEFAULT 1,
        tax_rate REAL DEFAULT 0.0,
        tags TEXT, -- Stored as JSON array
        attributes TEXT, -- Stored as JSON
        is_featured BOOLEAN DEFAULT 0,
        is_digital BOOLEAN DEFAULT 0,
        minimum_order_quantity INTEGER DEFAULT 1,
        status TEXT CHECK(status IN ('active', 'discontinued', 'out_of_stock', 'coming_soon')) NOT NULL
    );
    
    -- Add indexes
    CREATE INDEX idx_products_category ON products(category);
    CREATE INDEX idx_products_brand ON products(brand);
    CREATE INDEX idx_products_status ON products(status);
    CREATE INDEX idx_products_price ON products(price);
    
    -- 5. Inventory Table
    CREATE TABLE inventory (
        inventory_id INTEGER PRIMARY KEY,
        product_id INTEGER NOT NULL,
        office_id INTEGER NOT NULL,
        quantity INTEGER CHECK(quantity >= 0) NOT NULL,
        reorder_level INTEGER NOT NULL,
        reorder_quantity INTEGER NOT NULL,
        last_restock_date TIMESTAMP,
        next_expected_restock TIMESTAMP,
        shelf_location TEXT,
        lot_number TEXT,
        expiration_date DATE,
        condition TEXT CHECK(condition IN ('new', 'used', 'refurbished', 'damaged')) DEFAULT 'new',
        notes TEXT,
        last_inventory_count_date TIMESTAMP,
        is_available BOOLEAN DEFAULT 1,
        FOREIGN KEY (product_id) REFERENCES products(product_id),
        FOREIGN KEY (office_id) REFERENCES offices(office_id),
        UNIQUE(product_id, office_id)
    );
    
    -- Add indexes
    CREATE INDEX idx_inventory_product_id ON inventory(product_id);
    CREATE INDEX idx_inventory_office_id ON inventory(office_id);
    CREATE INDEX idx_inventory_quantity ON inventory(quantity);
    CREATE INDEX idx_inventory_expiration_date ON inventory(expiration_date);
    """)
    
    # Continue with more tables in another function to keep code manageable
    return

def create_database_schema_part2(conn):
    """Create the second part of the database schema."""
    cursor = conn.cursor()
    
    cursor.executescript("""
    -- 6. Inventory Movements Table
    CREATE TABLE inventory_movements (
        movement_id INTEGER PRIMARY KEY,
        inventory_id INTEGER NOT NULL,
        movement_type TEXT CHECK(movement_type IN ('purchase', 'sale', 'return', 'adjustment', 'transfer', 'loss', 'write_off')) NOT NULL,
        quantity INTEGER NOT NULL,
        movement_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
        reference_id TEXT, -- Order ID, Purchase Order ID, etc.
        source_location_id INTEGER, -- For transfers
        destination_location_id INTEGER, -- For transfers
        employee_id INTEGER,
        reason TEXT,
        cost_per_unit REAL,
        total_cost REAL,
        notes TEXT,
        FOREIGN KEY (inventory_id) REFERENCES inventory(inventory_id),
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
        FOREIGN KEY (source_location_id) REFERENCES offices(office_id),
        FOREIGN KEY (destination_location_id) REFERENCES offices(office_id)
    );
    
    -- Add indexes
    CREATE INDEX idx_inventory_movements_inventory_id ON inventory_movements(inventory_id);
    CREATE INDEX idx_inventory_movements_movement_type ON inventory_movements(movement_type);
    CREATE INDEX idx_inventory_movements_movement_date ON inventory_movements(movement_date);
    CREATE INDEX idx_inventory_movements_employee_id ON inventory_movements(employee_id);
    
    -- 7. Orders Table
    CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
        status TEXT CHECK(status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled', 'returned', 'on_hold')) NOT NULL,
        shipping_address TEXT NOT NULL,
        shipping_city TEXT NOT NULL,
        shipping_state TEXT,
        shipping_country TEXT NOT NULL,
        shipping_postal_code TEXT,
        shipping_method TEXT NOT NULL,
        tracking_number TEXT,
        estimated_delivery_date DATE,
        actual_delivery_date DATE,
        subtotal REAL CHECK(subtotal >= 0) NOT NULL,
        tax_amount REAL CHECK(tax_amount >= 0) NOT NULL,
        shipping_cost REAL CHECK(shipping_cost >= 0) NOT NULL,
        discount_amount REAL CHECK(discount_amount >= 0) DEFAULT 0,
        total_amount REAL CHECK(total_amount >= 0) NOT NULL,
        payment_method TEXT NOT NULL,
        payment_status TEXT CHECK(payment_status IN ('pending', 'paid', 'failed', 'refunded', 'partially_refunded')) NOT NULL,
        coupon_code TEXT,
        notes TEXT,
        ip_address TEXT,
        user_agent TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );
    
    -- Add indexes
    CREATE INDEX idx_orders_customer_id ON orders(customer_id);
    CREATE INDEX idx_orders_order_date ON orders(order_date);
    CREATE INDEX idx_orders_status ON orders(status);
    CREATE INDEX idx_orders_payment_status ON orders(payment_status);
    
    -- 8. Order Items Table
    CREATE TABLE order_items (
        order_item_id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER CHECK(quantity > 0) NOT NULL,
        unit_price REAL CHECK(unit_price >= 0) NOT NULL,
        discount_percentage REAL CHECK(discount_percentage >= 0 AND discount_percentage <= 100) DEFAULT 0,
        tax_percentage REAL CHECK(tax_percentage >= 0) DEFAULT 0,
        line_total REAL CHECK(line_total >= 0) NOT NULL,
        status TEXT CHECK(status IN ('pending', 'shipped', 'delivered', 'cancelled', 'returned')) NOT NULL,
        shipped_date DATE,
        returned_date DATE,
        return_reason TEXT,
        warehouse_id INTEGER,
        is_gift BOOLEAN DEFAULT 0,
        gift_message TEXT,
        FOREIGN KEY (order_id) REFERENCES orders(order_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id),
        FOREIGN KEY (warehouse_id) REFERENCES offices(office_id)
    );
    
    -- Add indexes
    CREATE INDEX idx_order_items_order_id ON order_items(order_id);
    CREATE INDEX idx_order_items_product_id ON order_items(product_id);
    CREATE INDEX idx_order_items_status ON order_items(status);
    
    -- 9. Product Reviews Table
    CREATE TABLE product_reviews (
        review_id INTEGER PRIMARY KEY,
        product_id INTEGER NOT NULL,
        customer_id INTEGER NOT NULL,
        order_item_id INTEGER,
        rating INTEGER CHECK(rating BETWEEN 1 AND 5) NOT NULL,
        review_title TEXT,
        review_text TEXT,
        review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
        is_verified_purchase BOOLEAN DEFAULT 0,
        likes INTEGER DEFAULT 0,
        dislikes INTEGER DEFAULT 0,
        status TEXT CHECK(status IN ('pending', 'approved', 'rejected', 'spam')) NOT NULL DEFAULT 'pending',
        response TEXT, -- Store admin response
        response_date TIMESTAMP,
        response_employee_id INTEGER,
        helpful_count INTEGER DEFAULT 0,
        ip_address TEXT,
        FOREIGN KEY (product_id) REFERENCES products(product_id),
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
        FOREIGN KEY (order_item_id) REFERENCES order_items(order_item_id),
        FOREIGN KEY (response_employee_id) REFERENCES employees(employee_id),
        UNIQUE(customer_id, product_id)
    );
    
    -- Add indexes
    CREATE INDEX idx_product_reviews_product_id ON product_reviews(product_id);
    CREATE INDEX idx_product_reviews_customer_id ON product_reviews(customer_id);
    CREATE INDEX idx_product_reviews_order_item_id ON product_reviews(order_item_id);
    CREATE INDEX idx_product_reviews_rating ON product_reviews(rating);
    CREATE INDEX idx_product_reviews_review_date ON product_reviews(review_date);
    CREATE INDEX idx_product_reviews_status ON product_reviews(status);
    
    -- 10. Transaction Logs Table
    CREATE TABLE transaction_logs (
        log_id INTEGER PRIMARY KEY,
        transaction_type TEXT NOT NULL,
        entity_type TEXT NOT NULL, -- 'order', 'product', 'customer', etc.
        entity_id INTEGER NOT NULL, -- ID of the related entity
        user_id INTEGER, -- employee or customer ID
        user_type TEXT CHECK(user_type IN ('employee', 'customer', 'system')) NOT NULL,
        action TEXT NOT NULL, -- 'create', 'update', 'delete', 'view', etc.
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
        ip_address TEXT,
        user_agent TEXT,
        old_values TEXT, -- JSON representation of old values
        new_values TEXT, -- JSON representation of new values
        status TEXT CHECK(status IN ('success', 'failure', 'pending')) NOT NULL,
        error_message TEXT,
        details TEXT -- Additional JSON details
    );
    
    -- Add indexes
    CREATE INDEX idx_transaction_logs_transaction_type ON transaction_logs(transaction_type);
    CREATE INDEX idx_transaction_logs_entity_type ON transaction_logs(entity_type);
    CREATE INDEX idx_transaction_logs_entity_id ON transaction_logs(entity_id);
    CREATE INDEX idx_transaction_logs_user_id ON transaction_logs(user_id);
    CREATE INDEX idx_transaction_logs_timestamp ON transaction_logs(timestamp);
    CREATE INDEX idx_transaction_logs_status ON transaction_logs(status);
    """)
    
    # Update the offices table with manager_id references - using a simpler approach
    # that works with SQLite's limited ALTER TABLE support
    cursor.executescript("""
    -- Add foreign key reference from offices to employees
    CREATE TABLE offices_new (
        office_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        address TEXT NOT NULL,
        city TEXT NOT NULL,
        state TEXT,
        country TEXT NOT NULL,
        postal_code TEXT,
        phone TEXT,
        email TEXT UNIQUE,
        website_url TEXT,
        opening_date DATE NOT NULL,
        status TEXT CHECK(status IN ('active', 'closed', 'under_renovation', 'planned')) NOT NULL,
        geo_location TEXT, -- Stored as JSON: {"lat": 00.000, "lng": 00.000}
        operating_hours TEXT, -- Stored as JSON
        last_renovation_date DATE,
        manager_id INTEGER, -- Will be updated after employees table is created
        tax_id TEXT UNIQUE,
        capacity INTEGER CHECK(capacity > 0),
        is_headquarters BOOLEAN DEFAULT 0,
        FOREIGN KEY (manager_id) REFERENCES employees(employee_id)
    );
    
    -- Copy data from old to new table
    INSERT INTO offices_new 
    SELECT * FROM offices;
    
    -- Drop the old table
    DROP TABLE offices;
    
    -- Rename the new table to the original name
    ALTER TABLE offices_new RENAME TO offices;
    
    -- Recreate the indexes
    CREATE INDEX idx_offices_country ON offices(country);
    CREATE INDEX idx_offices_status ON offices(status);
    """)
    
    conn.commit()
    return

def seed_offices(conn):
    """Insert realistic data into the offices table."""
    cursor = conn.cursor()
    
    # Office data
    offices = [
        (1, "Global Headquarters", "123 Main St", "New York", "NY", "USA", "10001", "+1-212-555-1000", 
         "hq@example.com", "https://www.example.com", "2010-01-15", "active", 
         json.dumps({"lat": 40.7128, "lng": -74.0060}), 
         json.dumps({"monday": "9:00-17:00", "tuesday": "9:00-17:00", "wednesday": "9:00-17:00", 
                   "thursday": "9:00-17:00", "friday": "9:00-17:00", "saturday": "closed", "sunday": "closed"}),
         "2020-06-10", None, "US12345678", 500, 1),
        
        (2, "West Coast Office", "456 Tech Blvd", "San Francisco", "CA", "USA", "94105", "+1-415-555-2000", 
         "sf@example.com", "https://sf.example.com", "2012-03-20", "active", 
         json.dumps({"lat": 37.7749, "lng": -122.4194}), 
         json.dumps({"monday": "8:00-16:00", "tuesday": "8:00-16:00", "wednesday": "8:00-16:00", 
                   "thursday": "8:00-16:00", "friday": "8:00-16:00", "saturday": "closed", "sunday": "closed"}),
         "2022-01-15", None, "US23456789", 250, 0),
        
        (3, "European Headquarters", "10 Thames Rd", "London", None, "UK", "EC1V 9BX", "+44-20-5555-3000", 
         "london@example.com", "https://uk.example.com", "2015-05-10", "active", 
         json.dumps({"lat": 51.5074, "lng": -0.1278}), 
         json.dumps({"monday": "9:00-17:30", "tuesday": "9:00-17:30", "wednesday": "9:00-17:30", 
                   "thursday": "9:00-17:30", "friday": "9:00-17:00", "saturday": "closed", "sunday": "closed"}),
         "2021-10-05", None, "GB34567890", 200, 0),
        
        (4, "APAC Regional Office", "88 Connaught Rd", "Hong Kong", None, "China", None, "+852-3555-4000", 
         "hk@example.com", "https://hk.example.com", "2017-11-12", "active", 
         json.dumps({"lat": 22.3193, "lng": 114.1694}), 
         json.dumps({"monday": "9:00-18:00", "tuesday": "9:00-18:00", "wednesday": "9:00-18:00", 
                   "thursday": "9:00-18:00", "friday": "9:00-18:00", "saturday": "9:00-13:00", "sunday": "closed"}),
         None, None, "HK45678901", 150, 0),
        
        (5, "Australia Branch", "42 George St", "Sydney", "NSW", "Australia", "2000", "+61-2-5555-5000", 
         "sydney@example.com", "https://au.example.com", "2019-02-28", "active", 
         json.dumps({"lat": -33.8688, "lng": 151.2093}), 
         json.dumps({"monday": "8:30-17:00", "tuesday": "8:30-17:00", "wednesday": "8:30-17:00", 
                   "thursday": "8:30-17:00", "friday": "8:30-16:00", "saturday": "closed", "sunday": "closed"}),
         None, None, "AU56789012", 75, 0),
        
        (6, "South American Office", "123 Av Paulista", "São Paulo", "SP", "Brazil", "01311-000", "+55-11-5555-6000", 
         "saopaulo@example.com", "https://br.example.com", "2020-09-15", "active", 
         json.dumps({"lat": -23.5505, "lng": -46.6333}), 
         json.dumps({"monday": "8:00-17:00", "tuesday": "8:00-17:00", "wednesday": "8:00-17:00", 
                   "thursday": "8:00-17:00", "friday": "8:00-16:00", "saturday": "closed", "sunday": "closed"}),
         None, None, "BR67890123", 80, 0),
        
        (7, "Midwest Distribution Center", "789 Warehouse Pkwy", "Chicago", "IL", "USA", "60607", "+1-312-555-7000", 
         "chicago@example.com", "https://dc.example.com", "2016-07-20", "active", 
         json.dumps({"lat": 41.8781, "lng": -87.6298}), 
         json.dumps({"monday": "7:00-19:00", "tuesday": "7:00-19:00", "wednesday": "7:00-19:00", 
                   "thursday": "7:00-19:00", "friday": "7:00-19:00", "saturday": "8:00-16:00", "sunday": "closed"}),
         "2022-05-10", None, "US78901234", 300, 0),
        
        (8, "Tokyo Office", "1-1 Marunouchi", "Tokyo", None, "Japan", "100-0005", "+81-3-5555-8000", 
         "tokyo@example.com", "https://jp.example.com", "2018-04-01", "active", 
         json.dumps({"lat": 35.6762, "lng": 139.6503}), 
         json.dumps({"monday": "9:00-18:00", "tuesday": "9:00-18:00", "wednesday": "9:00-18:00", 
                   "thursday": "9:00-18:00", "friday": "9:00-18:00", "saturday": "closed", "sunday": "closed"}),
         "2023-01-10", None, "JP89012345", 100, 0),
        
        (9, "Dubai Office", "Sheikh Zayed Rd", "Dubai", None, "UAE", None, "+971-4-555-9000", 
         "dubai@example.com", "https://uae.example.com", "2021-01-10", "active", 
         json.dumps({"lat": 25.2048, "lng": 55.2708}), 
         json.dumps({"sunday": "8:00-17:00", "monday": "8:00-17:00", "tuesday": "8:00-17:00", 
                   "wednesday": "8:00-17:00", "thursday": "8:00-16:00", "friday": "closed", "saturday": "closed"}),
         None, None, "AE90123456", 60, 0),
        
        (10, "Berlin Office", "10 Unter den Linden", "Berlin", None, "Germany", "10117", "+49-30-5555-1000", 
         "berlin@example.com", "https://de.example.com", "2019-11-05", "under_renovation", 
         json.dumps({"lat": 52.5200, "lng": 13.4050}), 
         json.dumps({"monday": "9:00-17:30", "tuesday": "9:00-17:30", "wednesday": "9:00-17:30", 
                   "thursday": "9:00-17:30", "friday": "9:00-16:30", "saturday": "closed", "sunday": "closed"}),
         "2023-08-15", None, "DE01234567", 85, 0)
    ]
    
    cursor.executemany("""
    INSERT INTO offices (
        office_id, name, address, city, state, country, postal_code, phone, email, website_url,
        opening_date, status, geo_location, operating_hours, last_renovation_date, manager_id,
        tax_id, capacity, is_headquarters
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, offices)
    
    conn.commit()
    return

def seed_employees(conn):
    """Insert realistic data into the employees table."""
    cursor = conn.cursor()
    
    # List of realistic skills for various departments
    tech_skills = ["Python", "JavaScript", "React", "AWS", "Docker", "Kubernetes", "SQL", "NoSQL", "Machine Learning"]
    sales_skills = ["Negotiation", "CRM", "Account Management", "Lead Generation", "Market Analysis", "Presentation"]
    hr_skills = ["Recruitment", "Employee Relations", "Training", "Compensation", "HRIS", "Performance Management"]
    finance_skills = ["Accounting", "Financial Analysis", "Budgeting", "Forecasting", "Audit", "Tax Planning"]
    marketing_skills = ["Digital Marketing", "Content Creation", "SEO", "Social Media", "Analytics", "Campaign Management"]
    operations_skills = ["Process Optimization", "Supply Chain", "Inventory Management", "Quality Control", "Logistics"]
    
    # Employee data
    employees = [
        # Executive Leadership
        (1, 1, "Sarah", "Johnson", "sarah.johnson@example.com", "+1-212-555-1001", "2010-01-15", None, 
         "CEO", "Executive", None, 450000.00, "1975-06-12", "875 Park Avenue", "New York", "NY", "USA", 
         json.dumps({"name": "Michael Johnson", "relationship": "Spouse", "phone": "+1-212-555-1991"}), 
         json.dumps(["Leadership", "Strategic Planning", "Public Speaking", "Negotiation"]), 4.9),
        
        (2, 1, "David", "Chen", "david.chen@example.com", "+1-212-555-1002", "2010-03-20", None, 
         "CTO", "Technology", 1, 380000.00, "1980-09-25", "301 E 64th St", "New York", "NY", "USA", 
         json.dumps({"name": "Jennifer Chen", "relationship": "Spouse", "phone": "+1-212-555-1992"}), 
         json.dumps(["System Architecture", "AI", "Cloud Infrastructure", "Team Leadership"]), 4.8),
        
        (3, 1, "Maria", "Rodriguez", "maria.rodriguez@example.com", "+1-212-555-1003", "2011-05-15", None, 
         "CFO", "Finance", 1, 375000.00, "1978-11-30", "420 E 72nd St", "New York", "NY", "USA", 
         json.dumps({"name": "Carlos Rodriguez", "relationship": "Brother", "phone": "+1-212-555-1993"}), 
         json.dumps(["Financial Planning", "M&A", "Risk Management", "Investor Relations"]), 4.7),
        
        (4, 1, "James", "Wilson", "james.wilson@example.com", "+1-212-555-1004", "2012-08-10", None, 
         "COO", "Operations", 1, 370000.00, "1977-04-18", "250 E 53rd St", "New York", "NY", "USA", 
         json.dumps({"name": "Emily Wilson", "relationship": "Spouse", "phone": "+1-212-555-1994"}), 
         json.dumps(["Operations Management", "Strategic Planning", "Process Optimization"]), 4.7),
        
        (5, 1, "Emily", "Taylor", "emily.taylor@example.com", "+1-212-555-1005", "2013-02-25", None, 
         "CMO", "Marketing", 1, 350000.00, "1982-07-03", "160 E 65th St", "New York", "NY", "USA", 
         json.dumps({"name": "Robert Taylor", "relationship": "Spouse", "phone": "+1-212-555-1995"}), 
         json.dumps(["Brand Development", "Marketing Strategy", "Digital Transformation"]), 4.6),
        
        # Technology Department - New York
        (6, 1, "Michael", "Brown", "michael.brown@example.com", "+1-212-555-1006", "2014-09-15", None, 
         "VP of Engineering", "Technology", 2, 290000.00, "1985-03-22", "222 E 44th St", "New York", "NY", "USA", 
         json.dumps({"name": "Lisa Brown", "relationship": "Spouse", "phone": "+1-212-555-1996"}), 
         json.dumps(["Software Architecture", "Team Leadership", "Agile", "DevOps"] + random.sample(tech_skills, 5)), 4.5),
        
        (7, 1, "Lisa", "Wang", "lisa.wang@example.com", "+1-212-555-1007", "2015-11-10", None, 
         "Senior Software Engineer", "Technology", 6, 195000.00, "1988-09-18", "400 E 67th St", "New York", "NY", "USA", 
         json.dumps({"name": "Kevin Wang", "relationship": "Spouse", "phone": "+1-212-555-1997"}), 
         json.dumps(random.sample(tech_skills, 6)), 4.7),
        
        (8, 1, "Ryan", "Garcia", "ryan.garcia@example.com", "+1-212-555-1008", "2016-04-05", None, 
         "Software Engineer", "Technology", 6, 165000.00, "1992-05-24", "305 E 86th St", "New York", "NY", "USA", 
         json.dumps({"name": "Anna Garcia", "relationship": "Mother", "phone": "+1-212-555-1998"}), 
         json.dumps(random.sample(tech_skills, 6)), 4.4),
        
        # San Francisco Office
        (9, 2, "Jessica", "Miller", "jessica.miller@example.com", "+1-415-555-2001", "2012-03-20", None, 
         "Regional Director", "Executive", 1, 310000.00, "1979-12-15", "88 King St", "San Francisco", "CA", "USA", 
         json.dumps({"name": "Mark Miller", "relationship": "Spouse", "phone": "+1-415-555-2991"}), 
         json.dumps(["Regional Management", "Team Leadership", "Strategic Planning"]), 4.8),
        
        (10, 2, "Andrew", "Thompson", "andrew.thompson@example.com", "+1-415-555-2002", "2012-06-15", None, 
         "Head of Product", "Product", 9, 285000.00, "1983-08-22", "1 Front St", "San Francisco", "CA", "USA", 
         json.dumps({"name": "Rebecca Thompson", "relationship": "Spouse", "phone": "+1-415-555-2992"}), 
         json.dumps(["Product Strategy", "UX Design", "Agile Development", "Market Analysis"]), 4.6),
        
        # Continue with more employees for other offices...
        # London Office
        (11, 3, "Emma", "Clark", "emma.clark@example.com", "+44-20-5555-3001", "2015-05-10", None, 
         "Regional Director", "Executive", 1, 290000.00, "1981-02-15", "25 Bedford St", "London", None, "UK", 
         json.dumps({"name": "William Clark", "relationship": "Spouse", "phone": "+44-20-5555-3991"}), 
         json.dumps(["International Business", "Team Leadership", "Strategic Planning"]), 4.7),
        
        # More employees for each office will be added in the full implementation
        # This is a representative sample of the first several employees
    ]
    
    # Add more employees for each office
    current_id = len(employees) + 1
    for office_id in range(1, 11):
        # Determine the right department manager to report to based on office
        if office_id == 1:  # HQ
            tech_manager_id = 6
            sales_manager_id = 4  # COO
            hr_manager_id = 1  # CEO
            finance_manager_id = 3  # CFO
            marketing_manager_id = 5  # CMO
            operations_manager_id = 4  # COO
        elif office_id == 2:  # SF
            tech_manager_id = 9  # Regional Director
            sales_manager_id = 9
            hr_manager_id = 9
            finance_manager_id = 9
            marketing_manager_id = 9
            operations_manager_id = 9
        elif office_id == 3:  # London
            tech_manager_id = 11  # Regional Director
            sales_manager_id = 11
            hr_manager_id = 11
            finance_manager_id = 11
            marketing_manager_id = 11
            operations_manager_id = 11
        else:
            # For other offices, we'll set managers later
            tech_manager_id = None
            sales_manager_id = None
            hr_manager_id = None
            finance_manager_id = None
            marketing_manager_id = None
            operations_manager_id = None
        
        # Add more employees per department based on office size
        # This is just a brief sample - in a full implementation, we'd add many more
        if office_id <= 5:  # Add more employees to larger offices
            # Technology Department
            for i in range(3):
                hire_date = date(2015 + i, random.randint(1, 12), random.randint(1, 28)).isoformat()
                birth_year = random.randint(1980, 1995)
                birth_date = date(birth_year, random.randint(1, 12), random.randint(1, 28)).isoformat()
                salary = 120000 + random.randint(0, 50000)
                
                employees.append((
                    current_id, office_id, f"TechFirst{current_id}", f"TechLast{current_id}", 
                    f"tech.employee{current_id}@example.com", f"+1-555-{current_id:04d}", hire_date, None,
                    "Software Developer", "Technology", tech_manager_id, salary, birth_date,
                    f"{random.randint(100, 999)} Tech St", "City", "State", "Country",
                    json.dumps({"name": "Emergency Contact", "relationship": "Family", "phone": f"+1-555-{current_id+1000:04d}"}),
                    json.dumps(random.sample(tech_skills, min(len(tech_skills), 5))),
                    round(random.uniform(3.0, 5.0), 1)
                ))
                current_id += 1
                
            # Sales Department
            for i in range(2):
                hire_date = date(2015 + i, random.randint(1, 12), random.randint(1, 28)).isoformat()
                birth_year = random.randint(1980, 1995)
                birth_date = date(birth_year, random.randint(1, 12), random.randint(1, 28)).isoformat()
                salary = 85000 + random.randint(0, 40000)
                
                employees.append((
                    current_id, office_id, f"SalesFirst{current_id}", f"SalesLast{current_id}", 
                    f"sales.employee{current_id}@example.com", f"+1-555-{current_id:04d}", hire_date, None,
                    "Sales Representative", "Sales", sales_manager_id, salary, birth_date,
                    f"{random.randint(100, 999)} Sales Ave", "City", "State", "Country",
                    json.dumps({"name": "Emergency Contact", "relationship": "Family", "phone": f"+1-555-{current_id+1000:04d}"}),
                    json.dumps(random.sample(sales_skills, min(len(sales_skills), 4))),
                    round(random.uniform(3.0, 5.0), 1)
                ))
                current_id += 1
    
    cursor.executemany("""
    INSERT INTO employees (
        employee_id, office_id, first_name, last_name, email, phone, hire_date, termination_date,
        position, department, manager_id, salary, birth_date, address, city, state, country,
        emergency_contact, skills, performance_rating
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, employees)
    
    conn.commit()
    
    # Update offices with managers
    cursor.execute("UPDATE offices SET manager_id = 1 WHERE office_id = 1")  # CEO for HQ
    cursor.execute("UPDATE offices SET manager_id = 9 WHERE office_id = 2")  # Regional Director for SF
    cursor.execute("UPDATE offices SET manager_id = 11 WHERE office_id = 3") # Regional Director for London
    
    # For other offices, we'd assign appropriate managers similarly
    
    conn.commit()
    return 

def seed_customers(conn):
    """Insert realistic data into the customers table."""
    cursor = conn.cursor()
    
    # Customer data with realistic information
    customers = [
        (1, "John", "Smith", "john.smith@email.com", "+1-555-123-4567", "2020-05-12 14:30:22", "2023-08-15 09:45:11",
         "1985-03-22", "123 Main St", "New York", "NY", "USA", "10001", "active", 1, "Google Search", 250,
         json.dumps({"preferred_categories": ["Electronics", "Books"], "communication_preferences": {"email": True, "sms": False}}),
         "hashed_password_123", "standard", "192.168.1.105"),
        
        (2, "Maria", "Garcia", "maria.garcia@email.com", "+1-555-234-5678", "2021-02-28 10:15:33", "2023-08-10 11:20:45",
         "1990-07-15", "456 Park Ave", "Los Angeles", "CA", "USA", "90001", "active", 1, "Friend Referral", 500,
         json.dumps({"preferred_categories": ["Clothing", "Home"], "communication_preferences": {"email": True, "sms": True}}),
         "hashed_password_234", "premium", "192.168.1.106"),
        
        (3, "James", "Johnson", "james.johnson@email.com", "+1-555-345-6789", "2019-11-05 08:45:10", "2023-08-14 16:30:22",
         "1978-11-30", "789 Oak St", "Chicago", "IL", "USA", "60007", "active", 0, "Facebook Ad", 100,
         json.dumps({"preferred_categories": ["Electronics", "Sports"], "communication_preferences": {"email": True, "sms": False}}),
         "hashed_password_345", "standard", "192.168.1.107"),
        
        (4, "Emma", "Brown", "emma.brown@email.com", "+1-555-456-7890", "2022-01-15 16:20:45", "2023-08-12 14:15:33",
         "1995-05-25", "101 Pine Ln", "Houston", "TX", "USA", "77001", "active", 1, "Instagram Ad", 75,
         json.dumps({"preferred_categories": ["Beauty", "Clothing"], "communication_preferences": {"email": True, "sms": True}}),
         "hashed_password_456", "standard", "192.168.1.108"),
        
        (5, "Mohammed", "Ali", "mohammed.ali@email.com", "+44-7700-900123", "2020-07-22 12:10:33", "2023-08-09 10:45:22",
         "1982-09-18", "10 High Street", "London", None, "UK", "EC1A 1BB", "active", 1, "Email Campaign", 320,
         json.dumps({"preferred_categories": ["Books", "Electronics"], "communication_preferences": {"email": True, "sms": False}}),
         "hashed_password_567", "premium", "192.168.1.109"),
        
        (6, "Sophie", "Martin", "sophie.martin@email.com", "+33-6-12-34-56-78", "2021-05-10 09:35:12", "2023-08-11 08:50:15",
         "1988-04-12", "25 Rue de la Paix", "Paris", None, "France", "75001", "active", 1, "Google Search", 180,
         json.dumps({"preferred_categories": ["Fashion", "Beauty"], "communication_preferences": {"email": True, "sms": True}}),
         "hashed_password_678", "standard", "192.168.1.110"),
        
        (7, "Hiroshi", "Tanaka", "hiroshi.tanaka@email.com", "+81-3-1234-5678", "2022-03-15 11:25:40", "2023-08-08 22:15:30",
         "1975-12-03", "1-1-1 Chiyoda", "Tokyo", None, "Japan", "100-0001", "active", 0, "Friend Referral", 420,
         json.dumps({"preferred_categories": ["Electronics", "Home"], "communication_preferences": {"email": True, "sms": False}}),
         "hashed_password_789", "enterprise", "192.168.1.111"),
        
        (8, "Anna", "Schmidt", "anna.schmidt@email.com", "+49-30-12345678", "2020-09-20 15:40:55", "2023-08-10 15:30:25",
         "1992-02-28", "10 Berliner Str", "Berlin", None, "Germany", "10115", "active", 1, "Email Campaign", 290,
         json.dumps({"preferred_categories": ["Books", "Home"], "communication_preferences": {"email": True, "sms": True}}),
         "hashed_password_890", "standard", "192.168.1.112"),
        
        (9, "Carlos", "Rodriguez", "carlos.rodriguez@email.com", "+34-91-1234567", "2021-08-05 13:55:22", "2023-08-13 17:45:10",
         "1980-06-15", "Calle Mayor 10", "Madrid", None, "Spain", "28013", "inactive", 0, "Facebook Ad", 150,
         json.dumps({"preferred_categories": ["Sports", "Fashion"], "communication_preferences": {"email": True, "sms": False}}),
         "hashed_password_901", "standard", "192.168.1.113"),
        
        (10, "Olivia", "Wilson", "olivia.wilson@email.com", "+1-555-567-8901", "2019-04-30 10:05:15", "2023-07-30 09:25:40",
         "1987-09-09", "202 Maple Dr", "Miami", "FL", "USA", "33101", "suspended", 0, "Google Search", 50,
         json.dumps({"preferred_categories": ["Home", "Beauty"], "communication_preferences": {"email": False, "sms": False}}),
         "hashed_password_012", "standard", "192.168.1.114"),
        
        (11, "Liu", "Wei", "liu.wei@email.com", "+86-10-12345678", "2022-02-10 08:15:30", "2023-08-14 11:35:20",
         "1991-11-12", "10 Wangfujing St", "Beijing", None, "China", "100006", "active", 1, "WeChat Ad", 200,
         json.dumps({"preferred_categories": ["Electronics", "Home"], "communication_preferences": {"email": True, "sms": True}}),
         "hashed_password_123", "premium", "192.168.1.115"),
        
        (12, "Raj", "Patel", "raj.patel@email.com", "+91-22-12345678", "2020-12-18 14:25:50", "2023-08-12 16:55:15",
         "1989-07-23", "15 Marine Drive", "Mumbai", None, "India", "400001", "active", 1, "Email Campaign", 280,
         json.dumps({"preferred_categories": ["Clothing", "Electronics"], "communication_preferences": {"email": True, "sms": True}}),
         "hashed_password_234", "standard", "192.168.1.116"),
        
        (13, "Fatima", "Al-Sayed", "fatima.alsayed@email.com", "+971-4-1234567", "2021-06-22 09:45:33", "2023-08-11 10:20:45",
         "1993-03-15", "10 Sheikh Zayed Rd", "Dubai", None, "UAE", None, "active", 1, "Instagram Ad", 150,
         json.dumps({"preferred_categories": ["Fashion", "Beauty"], "communication_preferences": {"email": True, "sms": True}}),
         "hashed_password_345", "premium", "192.168.1.117"),
        
        (14, "Isabella", "Rossi", "isabella.rossi@email.com", "+39-02-12345678", "2020-10-10 12:35:20", "2023-08-09 14:40:15",
         "1986-12-05", "Via Roma 10", "Milan", None, "Italy", "20121", "active", 0, "Friend Referral", 190,
         json.dumps({"preferred_categories": ["Fashion", "Home"], "communication_preferences": {"email": True, "sms": False}}),
         "hashed_password_456", "standard", "192.168.1.118"),
        
        (15, "Michael", "Davis", "michael.davis@email.com", "+1-555-678-9012", "2019-08-15 15:50:10", "2023-08-13 13:15:30",
         "1984-05-30", "303 Cedar St", "Seattle", "WA", "USA", "98101", "active", 1, "Google Search", 310,
         json.dumps({"preferred_categories": ["Electronics", "Sports"], "communication_preferences": {"email": True, "sms": True}}),
         "hashed_password_567", "enterprise", "192.168.1.119")
    ]
    
    # Add more customers with generated data
    current_id = len(customers) + 1
    for i in range(current_id, 51):  # Add 35 more customers to make 50 total
        # Generate registration date between 2 years ago and 6 months ago
        days_ago = random.randint(180, 730)
        registration_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
        
        # Generate last login date between registration and now
        last_login_days_ago = random.randint(0, days_ago - 1)
        last_login = (datetime.now() - timedelta(days=last_login_days_ago)).strftime("%Y-%m-%d %H:%M:%S")
        
        # Generate birth date for someone 18-70 years old
        years_old = random.randint(18, 70)
        birth_year = datetime.now().year - years_old
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)  # Simplified to avoid month/day validation issues
        birth_date = f"{birth_year}-{birth_month:02d}-{birth_day:02d}"
        
        # Generate random data for other fields
        status_options = ["active", "inactive", "suspended", "pending"]
        status_weights = [0.85, 0.1, 0.03, 0.02]  # Mostly active accounts
        account_type_options = ["standard", "premium", "enterprise"]
        account_type_weights = [0.7, 0.25, 0.05]  # Mostly standard accounts
        
        preferred_categories = random.sample(["Electronics", "Books", "Clothing", "Home", "Beauty", "Sports", "Fashion", "Toys", "Food", "Health"], random.randint(1, 4))
        communication_prefs = {"email": random.random() > 0.1, "sms": random.random() > 0.5}  # Most want email, about half want SMS
        
        customers.append((
            i, f"FirstName{i}", f"LastName{i}", f"customer{i}@email.com", f"+1-555-{i:03d}-{random.randint(1000, 9999)}",
            registration_date, last_login, birth_date,
            f"{random.randint(100, 999)} Street Name", "City", None, "Country", f"{random.randint(10000, 99999)}",
            random.choices(status_options, status_weights)[0], random.randint(0, 1), 
            random.choice(["Google Search", "Friend Referral", "Social Media", "Email Campaign", "Other"]),
            random.randint(0, 1000),
            json.dumps({
                "preferred_categories": preferred_categories,
                "communication_preferences": communication_prefs
            }),
            f"hashed_password_{i}", random.choices(account_type_options, account_type_weights)[0],
            f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"
        ))
    
    cursor.executemany("""
    INSERT INTO customers (
        customer_id, first_name, last_name, email, phone, registration_date, last_login_timestamp,
        birth_date, address, city, state, country, postal_code, status, marketing_consent,
        referral_source, loyalty_points, preferences, password_hash, account_type, ip_address
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, customers)
    
    conn.commit()
    return

def seed_products(conn):
    """Insert realistic data into the products table."""
    cursor = conn.cursor()
    
    # Products data
    products = [
        (1, "Ultra HD Smart TV 55\"", "55-inch 4K Ultra HD Smart LED TV with HDR and voice control",
         "TV-55UHD-2023", "Electronics", "Televisions", "TechVision", 899.99, 650.00, 18.5,
         json.dumps({"length": 48.5, "width": 28.2, "height": 3.0}), "2023-01-15", None, 1, 0.07,
         json.dumps(["4K", "Smart TV", "HDR", "Voice Control"]),
         json.dumps({"display_type": "LED", "resolution": "3840x2160", "refresh_rate": "60Hz", "smart_features": ["Netflix", "Amazon Prime", "YouTube"]}),
         1, 0, 1, "active"),
        
        (2, "Wireless Noise-Cancelling Headphones", "Premium wireless over-ear headphones with adaptive noise cancellation",
         "AUDIO-NC750-BLK", "Electronics", "Audio", "SoundMaster", 349.99, 220.00, 0.65,
         json.dumps({"length": 7.5, "width": 6.5, "height": 3.2}), "2022-09-10", None, 1, 0.07,
         json.dumps(["Wireless", "Noise-Cancelling", "Bluetooth", "Premium"]),
         json.dumps({"battery_life": "30 hours", "connectivity": "Bluetooth 5.0", "color": "Black", "features": ["Active Noise Cancellation", "Touch Controls", "Voice Assistant"]}),
         0, 0, 1, "active"),
        
        (3, "Professional DSLR Camera", "24.1MP Digital SLR Camera with 18-55mm Lens",
         "CAM-PRO24-KIT", "Electronics", "Cameras", "OptiView", 1299.99, 950.00, 1.5,
         json.dumps({"length": 5.2, "width": 4.0, "height": 3.0}), "2022-05-20", None, 1, 0.07,
         json.dumps(["DSLR", "Professional", "High Resolution", "Photography"]),
         json.dumps({"sensor": "CMOS", "megapixels": 24.1, "iso_range": "100-25600", "video": "4K", "includes": ["Camera Body", "18-55mm Lens", "Battery", "Charger"]}),
         0, 0, 1, "active"),
        
        (4, "Ergonomic Office Chair", "High-back ergonomic office chair with lumbar support and adjustable features",
         "FURN-CHAIR-ERG01", "Home", "Furniture", "ComfortPlus", 299.99, 180.00, 35.0,
         json.dumps({"length": 26.0, "width": 26.0, "height": 48.0}), "2021-11-15", None, 1, 0.07,
         json.dumps(["Ergonomic", "Office", "Adjustable", "Lumbar Support"]),
         json.dumps({"material": "Mesh/Fabric", "color": "Black", "weight_capacity": "300 lbs", "features": ["Height Adjustment", "Tilt Function", "Swivel", "Armrest Adjustment"]}),
         0, 0, 1, "active"),
        
        (5, "Smart Home Security System", "Comprehensive wireless home security system with camera, sensors, and mobile app control",
         "SECURE-HOME-PRO", "Electronics", "Smart Home", "SafeGuard", 399.99, 240.00, 5.2,
         json.dumps({"length": 12.0, "width": 10.0, "height": 8.0}), "2023-02-28", None, 1, 0.07,
         json.dumps(["Security", "Smart Home", "Wireless", "Mobile App"]),
         json.dumps({"components": ["Base Station", "2 Cameras", "4 Door/Window Sensors", "Motion Detector"], "connectivity": "Wi-Fi/Cellular", "storage": "Cloud + Local", "subscription": "Optional"}),
         1, 0, 1, "active"),
        
        (6, "Premium Fitness Tracker", "Advanced fitness tracking watch with heart rate monitoring and GPS",
         "WEARABLE-FIT-PRO", "Electronics", "Wearables", "FitTech", 199.99, 105.00, 0.15,
         json.dumps({"length": 1.75, "width": 1.5, "height": 0.5}), "2022-08-15", None, 1, 0.07,
         json.dumps(["Fitness", "Heart Rate", "GPS", "Waterproof"]),
         json.dumps({"display": "Color AMOLED", "battery_life": "7 days", "water_resistant": "50m", "features": ["Sleep Tracking", "Step Counter", "Workout Detection", "Smartphone Notifications"]}),
         0, 0, 1, "active"),
        
        (7, "Professional Stand Mixer", "High-performance stand mixer for baking enthusiasts and professional chefs",
         "KITCHEN-MIX-PRO", "Home", "Kitchen Appliances", "ChefElite", 449.99, 320.00, 25.0,
         json.dumps({"length": 14.0, "width": 9.0, "height": 14.0}), "2022-04-10", None, 1, 0.07,
         json.dumps(["Kitchen", "Baking", "Professional", "Mixer"]),
         json.dumps({"capacity": "5.5 quarts", "speeds": 10, "color": "Metallic", "includes": ["Flat Beater", "Dough Hook", "Wire Whip", "Pouring Shield"]}),
         0, 0, 1, "active"),
        
        (8, "Italian Leather Messenger Bag", "Handcrafted genuine Italian leather messenger bag with multiple compartments",
         "BAG-MSNGR-LTHR", "Fashion", "Bags", "MilanoStyle", 249.99, 150.00, 2.8,
         json.dumps({"length": 15.0, "width": 4.0, "height": 12.0}), "2021-09-15", None, 1, 0.07,
         json.dumps(["Leather", "Messenger", "Professional", "Handcrafted"]),
         json.dumps({"material": "Genuine Italian Leather", "color": "Brown", "compartments": 5, "features": ["Laptop Sleeve", "Adjustable Strap", "Brass Hardware"]}),
         0, 0, 1, "active"),
        
        (9, "Organic Cotton Bedding Set", "Luxury 100% organic cotton sheet set with duvet cover, Queen size",
         "BEDDING-ORG-QUEEN", "Home", "Bedding", "EcoComfort", 149.99, 85.00, 5.0,
         json.dumps({"length": 20.0, "width": 16.0, "height": 4.0}), "2022-06-20", None, 1, 0.07,
         json.dumps(["Organic", "Cotton", "Bedding", "Luxury"]),
         json.dumps({"size": "Queen", "thread_count": 400, "color": "White", "includes": ["Fitted Sheet", "Flat Sheet", "2 Pillowcases", "Duvet Cover"]}),
         0, 0, 1, "active"),
        
        (10, "Stainless Steel Cookware Set", "10-piece professional-grade stainless steel cookware set",
         "KITCHEN-COOK-SS10", "Home", "Cookware", "ChefElite", 299.99, 180.00, 15.0,
         json.dumps({"length": 24.0, "width": 16.0, "height": 12.0}), "2021-08-10", None, 1, 0.07,
         json.dumps(["Cookware", "Stainless Steel", "Professional", "Kitchen"]),
         json.dumps({"pieces": 10, "material": "18/10 Stainless Steel", "dishwasher_safe": True, "includes": ["8\" Fry Pan", "10\" Fry Pan", "1.5qt Saucepan", "3qt Saucepan", "3.5qt Saute Pan", "8qt Stockpot", "4 Lids"]}),
         0, 0, 1, "active"),
        
        (11, "Yoga Mat Premium", "Eco-friendly non-slip yoga mat with carrying strap",
         "FITNESS-YOGA-PREM", "Sports", "Yoga", "ZenFlex", 49.99, 30.00, 2.2,
         json.dumps({"length": 72.0, "width": 24.0, "height": 0.25}), "2022-01-15", None, 1, 0.07,
         json.dumps(["Yoga", "Fitness", "Non-Slip", "Eco-Friendly"]),
         json.dumps({"material": "TPE + Natural Rubber", "thickness": "6mm", "color": "Blue", "features": ["Non-Slip Surface", "Carrying Strap", "Moisture Resistant"]}),
         0, 0, 1, "active"),
        
        (12, "Wireless Bluetooth Speaker", "Portable waterproof Bluetooth speaker with 20-hour battery life",
         "AUDIO-BT-SPEAK20", "Electronics", "Audio", "SoundMaster", 129.99, 75.00, 1.8,
         json.dumps({"length": 8.0, "width": 3.0, "height": 3.0}), "2022-11-10", None, 1, 0.07,
         json.dumps(["Bluetooth", "Speaker", "Waterproof", "Portable"]),
         json.dumps({"battery_life": "20 hours", "water_rating": "IPX7", "connectivity": "Bluetooth 5.1", "features": ["360° Sound", "Built-in Microphone", "USB-C Charging"]}),
         0, 0, 1, "active"),
        
        (13, "Coffee Maker with Grinder", "Programmable coffee maker with built-in burr grinder",
         "KITCHEN-COFFEE-PRO", "Home", "Kitchen Appliances", "BrewMaster", 199.99, 120.00, 10.0,
         json.dumps({"length": 14.0, "width": 9.0, "height": 16.0}), "2022-07-15", None, 1, 0.07,
         json.dumps(["Coffee", "Grinder", "Programmable", "Kitchen"]),
         json.dumps({"capacity": "12 cups", "grinder_settings": 8, "features": ["Programmable Timer", "Brew Strength Control", "Keep Warm Function"], "color": "Stainless Steel"}),
         0, 0, 1, "active"),
        
        (14, "Ultra-light Hiking Backpack", "Durable waterproof 45L hiking backpack with hydration compatibility",
         "OUTDOOR-PACK-45L", "Sports", "Outdoor", "TrailMaster", 119.99, 70.00, 2.5,
         json.dumps({"length": 22.0, "width": 14.0, "height": 9.0}), "2022-03-20", None, 1, 0.07,
         json.dumps(["Hiking", "Backpack", "Waterproof", "Lightweight"]),
         json.dumps({"capacity": "45L", "material": "Ripstop Nylon", "weight": "2.5 lbs", "features": ["Hydration Compatible", "Multiple Compartments", "Adjustable Straps", "Rain Cover"]}),
         0, 0, 1, "active"),
        
        (15, "Smart Robot Vacuum", "Wi-Fi connected robot vacuum with mapping and app control",
         "HOME-ROBOT-VAC", "Home", "Appliances", "CleanTech", 349.99, 210.00, 8.0,
         json.dumps({"length": 13.0, "width": 13.0, "height": 3.5}), "2023-01-05", None, 1, 0.07,
         json.dumps(["Robot", "Vacuum", "Smart Home", "Cleaning"]),
         json.dumps({"suction_power": "2500Pa", "battery_life": "120 minutes", "features": ["Mapping Technology", "App Control", "Voice Assistant Compatible", "Scheduled Cleaning"], "filter_type": "HEPA"}),
         1, 0, 1, "active")
    ]
    
    # Add more products with generated data
    current_id = len(products) + 1
    categories = ["Electronics", "Home", "Fashion", "Sports", "Beauty", "Books", "Toys", "Office", "Food", "Health"]
    subcategories = {
        "Electronics": ["Smartphones", "Laptops", "Tablets", "Accessories", "Gaming", "Audio", "Cameras"],
        "Home": ["Furniture", "Decor", "Bedding", "Kitchen", "Bath", "Storage", "Lighting"],
        "Fashion": ["Men's Clothing", "Women's Clothing", "Shoes", "Accessories", "Jewelry", "Watches"],
        "Sports": ["Fitness", "Outdoor", "Team Sports", "Water Sports", "Winter Sports", "Apparel"],
        "Beauty": ["Skincare", "Makeup", "Haircare", "Fragrance", "Tools", "Bath & Body"],
        "Books": ["Fiction", "Non-Fiction", "Children's", "Educational", "Reference", "E-books"],
        "Toys": ["Action Figures", "Board Games", "Educational", "Dolls", "Outdoor", "Building Sets"],
        "Office": ["Furniture", "Supplies", "Electronics", "Organization", "Paper", "Writing"],
        "Food": ["Pantry", "Snacks", "Beverages", "Organic", "Specialty", "Baking"],
        "Health": ["Vitamins", "Supplements", "Personal Care", "Medical Supplies", "Fitness", "Wellness"]
    }
    brands = {
        "Electronics": ["TechVision", "SoundMaster", "OptiView", "DigitalLife", "PowerTech"],
        "Home": ["ComfortPlus", "HomeStyle", "EcoComfort", "LivingEssentials", "DwellWell"],
        "Fashion": ["MilanoStyle", "UrbanChic", "ClassicWear", "FashionForward", "TrendSetters"],
        "Sports": ["TrailMaster", "ZenFlex", "AthleticPro", "SportElite", "ActiveLife"],
        "Beauty": ["GlowUp", "NaturalBeauty", "PureEssence", "BeautyLux", "SkinFirst"],
        "Books": ["PageTurner", "KnowledgePress", "ReadMore", "LiteraryCraft", "BookWorm"],
        "Toys": ["PlayTime", "KidZone", "ImagineThat", "FunFactory", "ToyWorld"],
        "Office": ["WorkSmart", "OfficePro", "BusinessBasics", "DeskMaster", "ProducTech"],
        "Food": ["GourmetSelect", "FreshChoice", "OrganicHarvest", "TastyBites", "FlavorFull"],
        "Health": ["WellnessOne", "VitaLife", "PureHealth", "NaturalCare", "HealthEssentials"]
    }
    statuses = ["active", "discontinued", "out_of_stock", "coming_soon"]
    status_weights = [0.7, 0.1, 0.15, 0.05]  # Mostly active products
    
    for i in range(current_id, 101):  # Add more products to have 100 total
        category = random.choice(categories)
        subcategory = random.choice(subcategories[category])
        brand = random.choice(brands[category])
        
        price = round(random.uniform(9.99, 1499.99), 2)
        cost = round(price * random.uniform(0.4, 0.7), 2)  # Cost is 40-70% of price
        
        weight = round(random.uniform(0.1, 50.0), 2) if random.random() > 0.2 else None  # Some products don't have weight
        
        dimensions = {
            "length": round(random.uniform(1, 60), 1),
            "width": round(random.uniform(1, 40), 1),
            "height": round(random.uniform(1, 30), 1)
        }
        
        # Generate launch date between 3 years ago and 1 month ago
        days_ago = random.randint(30, 1095)
        launch_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        
        # 10% chance of being discontinued
        discontinuation_date = (datetime.now() - timedelta(days=random.randint(1, 180))).strftime("%Y-%m-%d") if random.random() < 0.1 else None
        
        # Generate random tags
        possible_tags = ["Bestseller", "New Arrival", "Sale", "Limited Edition", "Exclusive", "Eco-Friendly", 
                       "Premium", "Budget", "High Performance", "Energy Efficient", "Award Winning"]
        tags = random.sample(possible_tags, k=random.randint(1, 4))
        
        # Generate attributes specific to the category
        attributes = {}
        if category == "Electronics":
            attributes = {
                "power": f"{random.randint(5, 500)}W",
                "warranty": f"{random.randint(1, 5)} years",
                "connectivity": random.choice(["Bluetooth", "Wi-Fi", "Wired", "Multiple"])
            }
        elif category == "Home":
            attributes = {
                "material": random.choice(["Wood", "Metal", "Plastic", "Glass", "Fabric", "Ceramic"]),
                "color": random.choice(["Black", "White", "Gray", "Brown", "Blue", "Green", "Red"]),
                "assembly_required": random.choice([True, False])
            }
        elif category == "Fashion":
            attributes = {
                "material": random.choice(["Cotton", "Polyester", "Wool", "Leather", "Denim", "Silk"]),
                "color": random.choice(["Black", "White", "Blue", "Red", "Green", "Yellow", "Purple"]),
                "size": random.choice(["XS", "S", "M", "L", "XL", "XXL"])
            }
        else:
            attributes = {
                "color": random.choice(["Black", "White", "Blue", "Red", "Green", "Yellow", "Purple", "Multi"]),
                "warranty": f"{random.randint(1, 5)} years" if random.random() > 0.5 else None
            }
        
        products.append((
            i, f"Product {i}", f"Description for Product {i} - a high-quality {subcategory} item",
            f"SKU-{category[:3].upper()}-{i:04d}", category, subcategory, brand, price, cost, weight,
            json.dumps(dimensions), launch_date, discontinuation_date, 
            1, round(random.uniform(0.05, 0.12), 2),  # is_taxable and tax_rate
            json.dumps(tags), json.dumps(attributes),
            random.random() < 0.2,  # 20% chance of being featured
            random.random() < 0.15,  # 15% chance of being digital
            random.randint(1, 5),  # minimum order quantity
            random.choices(statuses, status_weights)[0]  # status with weights
        ))
    
    cursor.executemany("""
    INSERT INTO products (
        product_id, name, description, sku, category, subcategory, brand, price, cost, weight,
        dimensions, launch_date, discontinuation_date, is_taxable, tax_rate, tags, attributes,
        is_featured, is_digital, minimum_order_quantity, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, products)
    
    conn.commit()
    return 

def seed_inventory(conn):
    """Insert realistic data into the inventory table."""
    cursor = conn.cursor()
    
    # Get all product IDs
    cursor.execute("SELECT product_id FROM products")
    product_ids = [row[0] for row in cursor.fetchall()]
    
    # Get all office IDs
    cursor.execute("SELECT office_id FROM offices")
    office_ids = [row[0] for row in cursor.fetchall()]
    
    # Inventory data
    inventory_entries = []
    inventory_id = 1
    
    warehouse_offices = [1, 2, 3, 7]  # Main warehouses (HQ, SF, London, Chicago)
    
    # Assign inventory to main warehouse offices
    for product_id in product_ids:
        for office_id in warehouse_offices:
            # Create realistic inventory levels (higher for popular products, lower for others)
            if product_id <= 20:  # Popular products
                quantity = random.randint(50, 500)
            elif product_id <= 50:  # Moderately popular
                quantity = random.randint(20, 150)
            else:  # Less popular
                quantity = random.randint(5, 100)
                
            # Some products might be out of stock
            if random.random() < 0.05:  # 5% chance of being out of stock
                quantity = 0
                
            # Set appropriate reorder levels and quantities
            reorder_level = max(int(quantity * 0.2), 5)
            reorder_quantity = max(int(quantity * 0.5), 10)
            
            # Generate last restock date (between 1 and 90 days ago)
            last_restock_days_ago = random.randint(1, 90)
            last_restock_date = (datetime.now() - timedelta(days=last_restock_days_ago)).strftime("%Y-%m-%d %H:%M:%S")
            
            # Generate next expected restock date for low inventory items
            next_restock_date = None
            if quantity <= reorder_level and quantity > 0:
                next_restock_days = random.randint(3, 14)
                next_restock_date = (datetime.now() + timedelta(days=next_restock_days)).strftime("%Y-%m-%d %H:%M:%S")
            
            # Generate shelf location
            section = random.choice(["A", "B", "C", "D", "E"])
            aisle = random.randint(1, 20)
            shelf = random.randint(1, 5)
            shelf_location = f"{section}{aisle:02d}-{shelf}"
            
            # Generate lot number
            lot_number = f"LOT-{random.randint(10000, 99999)}"
            
            # Generate expiration date for applicable products (e.g., food, health)
            cursor.execute("SELECT category FROM products WHERE product_id = ?", (product_id,))
            category = cursor.fetchone()[0]
            
            expiration_date = None
            if category in ["Food", "Health"]:
                expiry_days = random.randint(180, 730)  # 6 months to 2 years
                expiration_date = (datetime.now() + timedelta(days=expiry_days)).strftime("%Y-%m-%d")
            
            # Generate last inventory count date
            count_days_ago = random.randint(1, 30)
            last_count_date = (datetime.now() - timedelta(days=count_days_ago)).strftime("%Y-%m-%d %H:%M:%S")
            
            # Determine if available
            is_available = 1 if quantity > 0 else 0
            
            inventory_entries.append((
                inventory_id, product_id, office_id, quantity, reorder_level, reorder_quantity,
                last_restock_date, next_restock_date, shelf_location, lot_number, expiration_date,
                "new", None, last_count_date, is_available
            ))
            
            inventory_id += 1
    
    # Assign some inventory to retail offices (smaller quantities)
    retail_offices = [office_id for office_id in office_ids if office_id not in warehouse_offices]
    
    for product_id in product_ids:
        # Only 30% of products are stocked in retail locations
        if random.random() < 0.3:
            for office_id in retail_offices:
                # Much smaller quantities for retail locations
                quantity = random.randint(0, 25)
                
                # Set appropriate reorder levels and quantities
                reorder_level = max(int(quantity * 0.3), 2)
                reorder_quantity = max(int(quantity * 0.7), 5)
                
                # Generate last restock date (between 1 and 45 days ago)
                last_restock_days_ago = random.randint(1, 45)
                last_restock_date = (datetime.now() - timedelta(days=last_restock_days_ago)).strftime("%Y-%m-%d %H:%M:%S")
                
                # Generate next expected restock date for low inventory items
                next_restock_date = None
                if quantity <= reorder_level and quantity > 0:
                    next_restock_days = random.randint(5, 21)
                    next_restock_date = (datetime.now() + timedelta(days=next_restock_days)).strftime("%Y-%m-%d %H:%M:%S")
                
                # Generate shelf location
                section = random.choice(["S", "R", "T"])
                aisle = random.randint(1, 5)
                shelf = random.randint(1, 3)
                shelf_location = f"{section}{aisle:02d}-{shelf}"
                
                # Use the same lot number pattern
                lot_number = f"LOT-{random.randint(10000, 99999)}"
                
                # Get product category for expiration date logic
                cursor.execute("SELECT category FROM products WHERE product_id = ?", (product_id,))
                category = cursor.fetchone()[0]
                
                expiration_date = None
                if category in ["Food", "Health"]:
                    expiry_days = random.randint(180, 730)
                    expiration_date = (datetime.now() + timedelta(days=expiry_days)).strftime("%Y-%m-%d")
                
                # Generate last inventory count date
                count_days_ago = random.randint(1, 30)
                last_count_date = (datetime.now() - timedelta(days=count_days_ago)).strftime("%Y-%m-%d %H:%M:%S")
                
                # Determine if available
                is_available = 1 if quantity > 0 else 0
                
                inventory_entries.append((
                    inventory_id, product_id, office_id, quantity, reorder_level, reorder_quantity,
                    last_restock_date, next_restock_date, shelf_location, lot_number, expiration_date,
                    "new", None, last_count_date, is_available
                ))
                
                inventory_id += 1
    
    cursor.executemany("""
    INSERT INTO inventory (
        inventory_id, product_id, office_id, quantity, reorder_level, reorder_quantity,
        last_restock_date, next_expected_restock, shelf_location, lot_number, expiration_date,
        condition, notes, last_inventory_count_date, is_available
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, inventory_entries)
    
    conn.commit()
    return 

def seed_inventory_movements(conn):
    """Insert realistic data into the inventory_movements table."""
    cursor = conn.cursor()
    
    # Get all inventory entries
    cursor.execute("SELECT inventory_id, product_id, office_id, quantity FROM inventory")
    inventory_data = cursor.fetchall()
    
    # Get employee IDs for reference
    cursor.execute("SELECT employee_id FROM employees")
    employee_ids = [row[0] for row in cursor.fetchall()]
    
    movement_entries = []
    movement_id = 1
    
    for inv_id, product_id, office_id, current_qty in inventory_data:
        if current_qty == 0:
            continue
            
        # Get product cost for financial calculations
        cursor.execute("SELECT cost FROM products WHERE product_id = ?", (product_id,))
        cost = cursor.fetchone()[0]
        
        # Generate purchases (initial stocking)
        purchase_qty = current_qty + random.randint(0, 50)
        purchase_date = (datetime.now() - timedelta(days=random.randint(90, 365))).strftime("%Y-%m-%d %H:%M:%S")
        
        # Create a purchase entry
        movement_entries.append((
            movement_id, inv_id, "purchase", purchase_qty, purchase_date,
            f"PO-{random.randint(10000, 99999)}", None, None,
            random.choice(employee_ids), "Initial stocking", 
            cost, cost * purchase_qty, 
            "Initial inventory purchase"
        ))
        movement_id += 1
        
        # Generate sales movements
        num_sales = random.randint(3, 15)
        remaining_qty = purchase_qty
        
        for _ in range(num_sales):
            if remaining_qty <= current_qty:
                break
                
            sale_qty = random.randint(1, min(10, remaining_qty - current_qty))
            remaining_qty -= sale_qty
            
            # Sale date between purchase and now
            days_after_purchase = random.randint(1, 180)
            sale_date = (datetime.now() - timedelta(days=days_after_purchase)).strftime("%Y-%m-%d %H:%M:%S")
            
            movement_entries.append((
                movement_id, inv_id, "sale", -sale_qty, sale_date,
                f"ORD-{random.randint(100000, 999999)}", None, None,
                None, "Customer order", 
                cost, cost * sale_qty, 
                None
            ))
            movement_id += 1
        
        # Some inventory might have adjustments
        if random.random() < 0.3:
            adjustment_types = ["adjustment", "loss", "write_off"]
            adj_type = random.choice(adjustment_types)
            
            # Ensure at least 1 quantity for adjustment, but not more than current
            adj_qty = -random.randint(1, max(1, min(5, current_qty)))
            adj_date = (datetime.now() - timedelta(days=random.randint(1, 60))).strftime("%Y-%m-%d %H:%M:%S")
            
            reasons = {
                "adjustment": "Inventory count reconciliation",
                "loss": "Product damaged during handling",
                "write_off": "Expired product removed from inventory"
            }
            
            movement_entries.append((
                movement_id, inv_id, adj_type, adj_qty, adj_date,
                f"ADJ-{random.randint(10000, 99999)}", None, None,
                random.choice(employee_ids), reasons[adj_type], 
                cost, cost * abs(adj_qty), 
                f"{adj_type.capitalize()} recorded on {adj_date}"
            ))
            movement_id += 1
        
        # Some inventory might have transfers between locations
        if random.random() < 0.15 and current_qty >= 5:  # Only if we have enough quantity
            cursor.execute("SELECT office_id FROM offices WHERE office_id != ?", (office_id,))
            other_offices = [row[0] for row in cursor.fetchall()]
            
            if other_offices:
                dest_office = random.choice(other_offices)
                transfer_qty = -random.randint(5, min(20, current_qty))
                transfer_date = (datetime.now() - timedelta(days=random.randint(7, 90))).strftime("%Y-%m-%d %H:%M:%S")
                
                movement_entries.append((
                    movement_id, inv_id, "transfer", transfer_qty, transfer_date,
                    f"TRF-{random.randint(10000, 99999)}", office_id, dest_office,
                    random.choice(employee_ids), "Inventory rebalancing", 
                    cost, cost * abs(transfer_qty), 
                    f"Transfer to {dest_office} for stock rebalancing"
                ))
                movement_id += 1
    
    cursor.executemany("""
    INSERT INTO inventory_movements (
        movement_id, inventory_id, movement_type, quantity, movement_date,
        reference_id, source_location_id, destination_location_id,
        employee_id, reason, cost_per_unit, total_cost, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, movement_entries)
    
    conn.commit()
    return

def seed_orders(conn):
    """Insert realistic data into the orders table."""
    cursor = conn.cursor()
    
    # Get customer IDs
    cursor.execute("SELECT customer_id FROM customers")
    customer_ids = [row[0] for row in cursor.fetchall()]
    
    # Orders data
    orders = []
    order_id = 1
    
    # Create orders for the past year
    for _ in range(200):  # Create 200 orders
        # Select a customer
        customer_id = random.choice(customer_ids)
        
        # Get customer details for shipping info
        cursor.execute("""
        SELECT address, city, state, country, postal_code
        FROM customers WHERE customer_id = ?
        """, (customer_id,))
        customer_data = cursor.fetchone()
        
        # Generate order date (weighted towards more recent dates)
        days_weight = random.choices([1, 2, 3], weights=[0.5, 0.3, 0.2])[0]
        days_ago = random.randint(1, 365 // days_weight)
        order_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
        
        # Order status based on date
        status_options = ["pending", "processing", "shipped", "delivered", "cancelled", "returned", "on_hold"]
        
        # Adjust status probabilities based on order age
        if days_ago < 2:  # Very recent orders
            status_weights = [0.4, 0.4, 0.1, 0.0, 0.05, 0.0, 0.05]
        elif days_ago < 7:  # Orders within a week
            status_weights = [0.05, 0.15, 0.5, 0.2, 0.05, 0.0, 0.05]
        elif days_ago < 30:  # Orders within a month
            status_weights = [0.0, 0.05, 0.25, 0.6, 0.05, 0.05, 0.0]
        else:  # Older orders
            status_weights = [0.0, 0.0, 0.05, 0.8, 0.05, 0.1, 0.0]
            
        status = random.choices(status_options, weights=status_weights)[0]
        
        # Generate shipping method
        shipping_methods = ["Standard", "Express", "Next Day", "International"]
        shipping_method_weights = [0.6, 0.25, 0.1, 0.05]
        shipping_method = random.choices(shipping_methods, shipping_method_weights)[0]
        
        # Generate tracking number
        tracking_number = f"TRK{random.randint(1000000000, 9999999999)}" if status not in ["pending", "processing", "cancelled"] else None
        
        # Generate delivery dates based on status and order date
        estimated_delivery_date = None
        actual_delivery_date = None
        
        if status not in ["pending", "cancelled", "on_hold"]:
            # Estimated delivery is usually 3-10 days after order
            est_delivery_days = random.randint(3, 10)
            estimated_delivery_date = (datetime.now() - timedelta(days=days_ago) + timedelta(days=est_delivery_days)).strftime("%Y-%m-%d")
            
            # Actual delivery date based on status
            if status == "delivered":
                # Actual delivery is around the estimated date (slight variations)
                variance = random.randint(-2, 3)
                actual_days = est_delivery_days + variance
                actual_delivery_date = (datetime.now() - timedelta(days=days_ago) + timedelta(days=actual_days)).strftime("%Y-%m-%d")
        
        # Generate financial details
        subtotal = round(random.uniform(20, 2000), 2)
        tax_rate = round(random.uniform(0.05, 0.12), 2)
        tax_amount = round(subtotal * tax_rate, 2)
        
        # Shipping cost based on method and subtotal
        if shipping_method == "Standard":
            shipping_cost = round(max(5.99, min(subtotal * 0.05, 15.99)), 2)
        elif shipping_method == "Express":
            shipping_cost = round(max(12.99, min(subtotal * 0.08, 25.99)), 2)
        elif shipping_method == "Next Day":
            shipping_cost = round(max(19.99, min(subtotal * 0.12, 49.99)), 2)
        else:  # International
            shipping_cost = round(max(29.99, min(subtotal * 0.15, 99.99)), 2)
        
        # Discount (sometimes applied)
        discount_amount = 0
        coupon_code = None
        if random.random() < 0.3:  # 30% chance of discount
            discount_percentage = random.choice([0.05, 0.1, 0.15, 0.2, 0.25])
            discount_amount = round(subtotal * discount_percentage, 2)
            coupon_code = random.choice(["WELCOME10", "SAVE15", "SUMMER20", "HOLIDAY25", "SPECIAL30"])
        
        # Calculate total
        total_amount = round(subtotal + tax_amount + shipping_cost - discount_amount, 2)
        
        # Payment method
        payment_methods = ["Credit Card", "PayPal", "Apple Pay", "Google Pay", "Bank Transfer"]
        payment_method_weights = [0.6, 0.25, 0.05, 0.05, 0.05]
        payment_method = random.choices(payment_methods, payment_method_weights)[0]
        
        # Payment status
        if status == "cancelled":
            payment_status = random.choice(["pending", "failed"])
        elif status == "returned":
            payment_status = random.choice(["refunded", "partially_refunded"])
        elif random.random() < 0.95:  # 95% of non-cancelled orders are paid
            payment_status = "paid"
        else:
            payment_status = "pending"
        
        # Generate IP address and user agent
        ip_address = f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"
        
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPad; CPU OS 15_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36 Edg/96.0.1054.62"
        ]
        user_agent = random.choice(user_agents)
        
        orders.append((
            order_id, customer_id, order_date, status,
            customer_data[0], customer_data[1], customer_data[2], customer_data[3], customer_data[4],
            shipping_method, tracking_number, estimated_delivery_date, actual_delivery_date,
            subtotal, tax_amount, shipping_cost, discount_amount, total_amount,
            payment_method, payment_status, coupon_code, 
            random.choice([None, "Customer requested gift wrapping.", "Please deliver to front desk.", "Call before delivery."]),
            ip_address, user_agent
        ))
        
        order_id += 1
    
    cursor.executemany("""
    INSERT INTO orders (
        order_id, customer_id, order_date, status,
        shipping_address, shipping_city, shipping_state, shipping_country, shipping_postal_code,
        shipping_method, tracking_number, estimated_delivery_date, actual_delivery_date,
        subtotal, tax_amount, shipping_cost, discount_amount, total_amount,
        payment_method, payment_status, coupon_code, notes,
        ip_address, user_agent
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, orders)
    
    conn.commit()
    return

def seed_order_items(conn):
    """Insert realistic data into the order_items table."""
    cursor = conn.cursor()
    
    # Get order data
    cursor.execute("""
    SELECT order_id, order_date, status, subtotal
    FROM orders
    """)
    order_data = cursor.fetchall()
    
    # Get product data
    cursor.execute("""
    SELECT product_id, price, tax_rate
    FROM products
    """)
    all_products = cursor.fetchall()
    
    # Get office (warehouse) ids for shipping location
    cursor.execute("""
    SELECT office_id
    FROM offices
    """)
    office_ids = [row[0] for row in cursor.fetchall()]
    warehouse_ids = [1, 2, 3, 7]  # Main warehouses
    
    order_items = []
    order_item_id = 1
    
    for order_id, order_date, order_status, order_subtotal in order_data:
        # Skip cancelled orders
        if order_status == "cancelled":
            continue
            
        # Determine number of items in this order (1-5 items)
        num_items = random.choices([1, 2, 3, 4, 5], weights=[0.3, 0.3, 0.2, 0.15, 0.05])[0]
        
        # Select random products for this order
        order_products = random.sample(all_products, k=min(num_items, len(all_products)))
        
        # Set the ordered quantity for each product
        total_price = 0.0
        
        for product_id, price, tax_rate in order_products:
            # Quantity is usually 1, but can be more for some products
            quantity = random.choices([1, 2, 3, 4, 5], weights=[0.7, 0.15, 0.1, 0.03, 0.02])[0]
            
            # Determine if discount applies (some products might be on sale)
            discount_percentage = 0.0
            if random.random() < 0.2:  # 20% chance of product discount
                discount_percentage = random.choice([5.0, 10.0, 15.0, 20.0, 25.0])
            
            # Calculate unit price with discount
            unit_price = price * (1 - discount_percentage / 100)
            
            # Calculate tax percentage
            tax_percentage = tax_rate * 100
            
            # Calculate line total
            line_total = round(unit_price * quantity * (1 + tax_rate), 2)
            total_price += line_total
            
            # Set item status based on order status
            item_status = order_status
            if order_status == "returned" and random.random() < 0.3:
                # Some items might not be returned even if the order is
                item_status = "delivered"
            
            # Ensure status is valid for order_items
            if item_status not in ["pending", "shipped", "delivered", "cancelled", "returned"]:
                # Map processing/on_hold to pending
                if item_status in ["processing", "on_hold"]:
                    item_status = "pending"
                # Default to delivered for any other statuses
                else:
                    item_status = "delivered"
            
            # Generate dates based on item status
            shipped_date = None
            returned_date = None
            
            if item_status in ["shipped", "delivered", "returned"]:
                # Parse order date string to datetime
                order_datetime = datetime.strptime(order_date, "%Y-%m-%d %H:%M:%S")
                
                # Shipped date is usually 1-3 days after order
                ship_days = random.randint(1, 3)
                shipped_date = (order_datetime + timedelta(days=ship_days)).strftime("%Y-%m-%d")
                
                if item_status == "returned":
                    # Return date is usually 5-14 days after shipping
                    return_days = random.randint(5, 14)
                    shipped_datetime = datetime.strptime(shipped_date, "%Y-%m-%d")
                    returned_date = (shipped_datetime + timedelta(days=return_days)).strftime("%Y-%m-%d")
            
            # Generate return reason if applicable
            return_reason = None
            if item_status == "returned":
                return_reasons = [
                    "Item damaged during shipping",
                    "Wrong size/color",
                    "Not as described",
                    "Changed mind",
                    "Arrived too late",
                    "Found better price elsewhere",
                    "Defective product"
                ]
                return_reason = random.choice(return_reasons)
            
            # Assign warehouse
            warehouse_id = random.choice(warehouse_ids)
            
            # Gift options
            is_gift = random.random() < 0.1  # 10% chance of being a gift
            gift_message = None
            
            if is_gift:
                gift_messages = [
                    "Happy Birthday! Enjoy your gift.",
                    "Congratulations on your new home!",
                    "Happy Anniversary!",
                    "Thank you for everything.",
                    "Hope you enjoy this gift!",
                    "Wishing you all the best.",
                    "Just a small token of appreciation."
                ]
                gift_message = random.choice(gift_messages)
            
            order_items.append((
                order_item_id, order_id, product_id, quantity, unit_price,
                discount_percentage, tax_percentage, line_total, item_status,
                shipped_date, returned_date, return_reason, warehouse_id,
                1 if is_gift else 0, gift_message
            ))
            
            order_item_id += 1
        
    cursor.executemany("""
    INSERT INTO order_items (
        order_item_id, order_id, product_id, quantity, unit_price,
        discount_percentage, tax_percentage, line_total, status,
        shipped_date, returned_date, return_reason, warehouse_id,
        is_gift, gift_message
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, order_items)
    
    conn.commit()
    return

def seed_product_reviews(conn):
    """Insert realistic data into the product_reviews table."""
    cursor = conn.cursor()
    
    # Get order items that have been delivered
    cursor.execute("""
    SELECT oi.order_item_id, oi.product_id, o.customer_id
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    WHERE oi.status = 'delivered'
    """)
    delivered_items = cursor.fetchall()
    
    # Get employee IDs for response_employee_id
    cursor.execute("SELECT employee_id FROM employees")
    employee_ids = [row[0] for row in cursor.fetchall()]
    
    reviews = []
    review_id = 1
    
    # Track combinations of customer_id and product_id to avoid duplicates
    customer_product_pairs = set()
    
    # About 30% of delivered items get reviews
    for item_id, product_id, customer_id in delivered_items:
        # Skip if this customer has already reviewed this product
        if (customer_id, product_id) in customer_product_pairs:
            continue
            
        customer_product_pairs.add((customer_id, product_id))
        
        if random.random() < 0.3:  # 30% chance of review
            # Generate rating (weighted towards positive reviews)
            rating = random.choices([1, 2, 3, 4, 5], weights=[0.05, 0.05, 0.15, 0.35, 0.4])[0]
            
            # Generate review date (1-30 days after delivery)
            cursor.execute("""
            SELECT o.order_date
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE oi.order_item_id = ?
            """, (item_id,))
            order_date = cursor.fetchone()[0]
            
            order_datetime = datetime.strptime(order_date, "%Y-%m-%d %H:%M:%S")
            days_after_order = random.randint(5, 30)
            review_date = (order_datetime + timedelta(days=days_after_order)).strftime("%Y-%m-%d %H:%M:%S")
            
            # Generate review title based on rating
            if rating >= 4:
                titles = [
                    "Love this product!",
                    "Excellent purchase",
                    "Exactly what I needed",
                    "Highly recommended",
                    "Great value",
                    "Very satisfied",
                    "Exceeded expectations"
                ]
            elif rating == 3:
                titles = [
                    "Decent product",
                    "Good but not great",
                    "Satisfied overall",
                    "Met expectations",
                    "Average quality",
                    "OK for the price"
                ]
            else:
                titles = [
                    "Disappointed",
                    "Not as described",
                    "Expected better",
                    "Would not recommend",
                    "Save your money",
                    "Poor quality"
                ]
            
            review_title = random.choice(titles)
            
            # Generate review text
            if rating >= 4:
                texts = [
                    f"I'm extremely satisfied with this purchase. The quality is excellent and it arrived quickly.",
                    f"This product exceeded my expectations. I would definitely buy again.",
                    f"Great product for the price. Exactly as described and works perfectly.",
                    f"Absolutely love it! Easy to use and exactly what I was looking for.",
                    f"High quality and well worth the money. Shipping was fast too."
                ]
            elif rating == 3:
                texts = [
                    f"This product is okay. It serves its purpose but nothing special.",
                    f"Decent quality for the price, but there are a few minor issues.",
                    f"Works as expected, but the instructions could be clearer.",
                    f"Average product. Does what it needs to do but wouldn't rave about it.",
                    f"Satisfied with the purchase but there's room for improvement."
                ]
            else:
                texts = [
                    f"Very disappointed with this purchase. The quality is much lower than expected.",
                    f"Product arrived damaged and didn't work properly. Would not recommend.",
                    f"Not worth the money at all. Doesn't match the description.",
                    f"Had to return this. It broke after just a few uses.",
                    f"Save your money and look elsewhere. This was a complete letdown."
                ]
            
            review_text = random.choice(texts)
            
            # Determine if verified purchase
            is_verified = 1
            
            # Set status (most are approved)
            status_options = ["pending", "approved", "rejected", "spam"]
            status_weights = [0.05, 0.9, 0.03, 0.02]
            status = random.choices(status_options, weights=status_weights)[0]
            
            # Generate likes/dislikes based on rating
            if rating >= 4:
                likes = random.randint(0, 20)
                dislikes = random.randint(0, 2)
            elif rating == 3:
                likes = random.randint(0, 10)
                dislikes = random.randint(0, 5)
            else:
                likes = random.randint(0, 5)
                dislikes = random.randint(0, 15)
            
            # Generate admin response for some reviews
            response = None
            response_date = None
            response_employee_id = None
            
            # More likely to respond to negative reviews
            response_chance = 0.8 if rating <= 2 else 0.3 if rating == 3 else 0.1
            
            if random.random() < response_chance and status == "approved":
                if rating <= 2:
                    responses = [
                        "We're sorry to hear about your experience. Please contact our customer service team so we can make this right.",
                        "Thank you for your feedback. We apologize that our product didn't meet your expectations. We'd like to offer a replacement or refund.",
                        "We appreciate your honest review and will use this feedback to improve our products. Please contact us directly to resolve your concerns."
                    ]
                else:
                    responses = [
                        "Thank you for your review! We're glad you're enjoying our product.",
                        "We appreciate your feedback and are happy to hear about your positive experience.",
                        "Thanks for taking the time to share your thoughts. We value your business!"
                    ]
                
                response = random.choice(responses)
                
                # Response is typically 1-3 days after the review
                review_datetime = datetime.strptime(review_date, "%Y-%m-%d %H:%M:%S")
                response_days = random.randint(1, 3)
                response_date = (review_datetime + timedelta(days=response_days)).strftime("%Y-%m-%d %H:%M:%S")
                
                # Assign a random employee to respond
                response_employee_id = random.choice(employee_ids)
            
            # Helpful count
            helpful_count = random.randint(0, likes)
            
            # Generate IP address
            ip_address = f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"
            
            reviews.append((
                review_id, product_id, customer_id, item_id, rating,
                review_title, review_text, review_date, is_verified,
                likes, dislikes, status, response, response_date,
                response_employee_id, helpful_count, ip_address
            ))
            
            review_id += 1
    
    cursor.executemany("""
    INSERT INTO product_reviews (
        review_id, product_id, customer_id, order_item_id, rating,
        review_title, review_text, review_date, is_verified_purchase,
        likes, dislikes, status, response, response_date,
        response_employee_id, helpful_count, ip_address
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, reviews)
    
    conn.commit()
    return

def seed_transaction_logs(conn):
    """Insert realistic data into the transaction_logs table."""
    cursor = conn.cursor()
    
    # Get data for various entities
    cursor.execute("SELECT order_id FROM orders LIMIT 50")
    order_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT product_id FROM products LIMIT 50")
    product_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT customer_id FROM customers LIMIT 50")
    customer_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT employee_id FROM employees LIMIT 50")
    employee_ids = [row[0] for row in cursor.fetchall()]
    
    transaction_logs = []
    log_id = 1
    
    # Generate logs for various entity types
    entity_configs = [
        {
            "entity_type": "order",
            "ids": order_ids,
            "actions": ["create", "update", "view", "delete"],
            "action_weights": [0.3, 0.4, 0.25, 0.05],
            "user_types": ["employee", "customer"],
            "user_type_weights": [0.7, 0.3]
        },
        {
            "entity_type": "product",
            "ids": product_ids,
            "actions": ["create", "update", "view", "delete"],
            "action_weights": [0.1, 0.3, 0.55, 0.05],
            "user_types": ["employee", "customer", "system"],
            "user_type_weights": [0.4, 0.5, 0.1]
        },
        {
            "entity_type": "customer",
            "ids": customer_ids,
            "actions": ["create", "update", "view", "delete"],
            "action_weights": [0.1, 0.3, 0.55, 0.05],
            "user_types": ["employee", "customer", "system"],
            "user_type_weights": [0.6, 0.3, 0.1]
        }
    ]
    
    # Generate 1000 log entries
    for _ in range(1000):
        # Select entity type configuration
        entity_config = random.choice(entity_configs)
        
        # Select entity ID
        entity_id = random.choice(entity_config["ids"])
        
        # Select action
        action = random.choices(
            entity_config["actions"], 
            weights=entity_config["action_weights"]
        )[0]
        
        # Select user type
        user_type = random.choices(
            entity_config["user_types"], 
            weights=entity_config["user_type_weights"]
        )[0]
        
        # Select user ID based on user type
        if user_type == "employee":
            user_id = random.choice(employee_ids)
        elif user_type == "customer":
            user_id = random.choice(customer_ids)
        else:  # system
            user_id = None
        
        # Generate timestamp (within the last 90 days)
        days_ago = random.randint(0, 90)
        timestamp = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
        
        # Generate transaction type
        if action == "create":
            transaction_type = f"{entity_config['entity_type']}_creation"
        elif action == "update":
            transaction_type = f"{entity_config['entity_type']}_update"
        elif action == "delete":
            transaction_type = f"{entity_config['entity_type']}_deletion"
        else:  # view
            transaction_type = f"{entity_config['entity_type']}_view"
        
        # Generate IP address and user agent for non-system users
        ip_address = None
        user_agent = None
        
        if user_type != "system":
            ip_address = f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"
            
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
                "Mozilla/5.0 (iPhone; CPU iPhone OS 15_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Mobile/15E148 Safari/604.1",
                "Mozilla/5.0 (iPad; CPU OS 15_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Mobile/15E148 Safari/604.1",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36 Edg/96.0.1054.62"
            ]
            user_agent = random.choice(user_agents)
        
        # Generate old and new values for updates
        old_values = None
        new_values = None
        
        if action == "update":
            if entity_config["entity_type"] == "order":
                statuses = ["pending", "processing", "shipped", "delivered", "cancelled", "returned", "on_hold"]
                old_status = random.choice(statuses)
                new_status = random.choice([s for s in statuses if s != old_status])
                
                old_values = json.dumps({"status": old_status})
                new_values = json.dumps({"status": new_status})
                
            elif entity_config["entity_type"] == "product":
                old_price = round(random.uniform(10, 500), 2)
                new_price = round(old_price * random.uniform(0.8, 1.2), 2)
                
                old_values = json.dumps({"price": old_price})
                new_values = json.dumps({"price": new_price})
                
            elif entity_config["entity_type"] == "customer":
                statuses = ["active", "inactive", "suspended", "pending"]
                old_status = random.choice(statuses)
                new_status = random.choice([s for s in statuses if s != old_status])
                
                old_values = json.dumps({"status": old_status})
                new_values = json.dumps({"status": new_status})
        
        # Set status (mostly successful operations)
        status_options = ["success", "failure", "pending"]
        status_weights = [0.95, 0.04, 0.01]
        status = random.choices(status_options, weights=status_weights)[0]
        
        # Set error message for failures
        error_message = None
        if status == "failure":
            error_messages = [
                "Database connection error",
                "Permission denied",
                "Validation failed",
                "Timeout occurred",
                "Concurrency conflict"
            ]
            error_message = random.choice(error_messages)
        
        # Add additional details
        details = None
        if random.random() < 0.3:  # 30% chance of additional details
            if entity_config["entity_type"] == "order":
                details = json.dumps({
                    "shipping_method": random.choice(["Standard", "Express", "Next Day", "International"]),
                    "payment_method": random.choice(["Credit Card", "PayPal", "Apple Pay", "Google Pay", "Bank Transfer"])
                })
            elif entity_config["entity_type"] == "product":
                details = json.dumps({
                    "category": random.choice(["Electronics", "Home", "Fashion", "Sports", "Beauty"]),
                    "brand": random.choice(["TechVision", "SoundMaster", "OptiView", "ComfortPlus", "TrailMaster"])
                })
            elif entity_config["entity_type"] == "customer":
                details = json.dumps({
                    "account_type": random.choice(["standard", "premium", "enterprise"]),
                    "marketing_consent": random.choice([True, False])
                })
        
        transaction_logs.append((
            log_id, transaction_type, entity_config["entity_type"], entity_id,
            user_id, user_type, action, timestamp, ip_address, user_agent,
            old_values, new_values, status, error_message, details
        ))
        
        log_id += 1
    
    cursor.executemany("""
    INSERT INTO transaction_logs (
        log_id, transaction_type, entity_type, entity_id,
        user_id, user_type, action, timestamp, ip_address, user_agent,
        old_values, new_values, status, error_message, details
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, transaction_logs)
    
    conn.commit()
    return

def create_aggregated_views(conn):
    """Create pre-computed aggregated views with appropriate indexing."""
    cursor = conn.cursor()
    
    cursor.executescript("""
    -- 1. Product Sales Summary View
    DROP VIEW IF EXISTS vw_product_sales_summary;
    CREATE VIEW vw_product_sales_summary AS
    SELECT 
        p.product_id,
        p.name AS product_name,
        p.category,
        p.subcategory,
        p.brand,
        COUNT(DISTINCT oi.order_id) AS order_count,
        SUM(oi.quantity) AS total_quantity_sold,
        SUM(oi.line_total) AS total_revenue,
        AVG(oi.unit_price) AS average_price,
        MAX(o.order_date) AS last_order_date
    FROM products p
    LEFT JOIN order_items oi ON p.product_id = oi.product_id
    LEFT JOIN orders o ON oi.order_id = o.order_id
    WHERE oi.status != 'cancelled' OR oi.status IS NULL
    GROUP BY p.product_id, p.name, p.category, p.subcategory, p.brand;
    
    -- 2. Customer Purchase History Summary
    DROP VIEW IF EXISTS vw_customer_purchase_summary;
    CREATE VIEW vw_customer_purchase_summary AS
    SELECT
        c.customer_id,
        c.first_name || ' ' || c.last_name AS customer_name,
        c.email,
        c.account_type,
        COUNT(DISTINCT o.order_id) AS order_count,
        SUM(o.total_amount) AS total_spent,
        AVG(o.total_amount) AS average_order_value,
        MAX(o.order_date) AS last_order_date,
        MIN(o.order_date) AS first_order_date,
        SUM(CASE WHEN o.status = 'delivered' THEN 1 ELSE 0 END) AS completed_orders,
        SUM(CASE WHEN o.status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_orders
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_id, c.first_name, c.last_name, c.email, c.account_type;
    
    -- 3. Inventory Status Summary
    DROP VIEW IF EXISTS vw_inventory_status_summary;
    CREATE VIEW vw_inventory_status_summary AS
    SELECT
        i.product_id,
        p.name AS product_name,
        p.category,
        p.brand,
        SUM(i.quantity) AS total_quantity,
        COUNT(DISTINCT i.office_id) AS stocked_locations,
        SUM(CASE WHEN i.quantity <= i.reorder_level THEN 1 ELSE 0 END) AS locations_needing_restock,
        SUM(CASE WHEN i.quantity = 0 THEN 1 ELSE 0 END) AS out_of_stock_locations,
        MAX(i.last_restock_date) AS last_restock_date
    FROM inventory i
    JOIN products p ON i.product_id = p.product_id
    GROUP BY i.product_id, p.name, p.category, p.brand;
    
    -- 4. Monthly Sales Trends
    DROP VIEW IF EXISTS vw_monthly_sales_trends;
    CREATE VIEW vw_monthly_sales_trends AS
    SELECT
        strftime('%Y-%m', o.order_date) AS month,
        COUNT(DISTINCT o.order_id) AS order_count,
        SUM(o.total_amount) AS total_revenue,
        AVG(o.total_amount) AS average_order_value,
        COUNT(DISTINCT o.customer_id) AS unique_customers,
        SUM(o.shipping_cost) AS total_shipping,
        SUM(o.tax_amount) AS total_tax
    FROM orders o
    WHERE o.status != 'cancelled'
    GROUP BY strftime('%Y-%m', o.order_date)
    ORDER BY month DESC;
    
    -- 5. Office Performance Summary
    DROP VIEW IF EXISTS vw_office_performance_summary;
    CREATE VIEW vw_office_performance_summary AS
    SELECT
        o.office_id,
        o.name AS office_name,
        o.city,
        o.country,
        COUNT(DISTINCT e.employee_id) AS employee_count,
        AVG(e.salary) AS average_salary,
        COUNT(DISTINCT i.product_id) AS unique_products_stocked,
        SUM(i.quantity) AS total_inventory_units,
        COUNT(DISTINCT im.movement_id) AS inventory_movement_count,
        SUM(CASE WHEN im.movement_type = 'sale' THEN 1 ELSE 0 END) AS sales_count
    FROM offices o
    LEFT JOIN employees e ON o.office_id = e.office_id
    LEFT JOIN inventory i ON o.office_id = i.office_id
    LEFT JOIN inventory_movements im ON i.inventory_id = im.inventory_id
    GROUP BY o.office_id, o.name, o.city, o.country;
    
    -- 6. Product Review Statistics
    DROP VIEW IF EXISTS vw_product_review_stats;
    CREATE VIEW vw_product_review_stats AS
    SELECT
        p.product_id,
        p.name AS product_name,
        p.category,
        COUNT(r.review_id) AS review_count,
        AVG(r.rating) AS average_rating,
        SUM(CASE WHEN r.rating >= 4 THEN 1 ELSE 0 END) AS positive_reviews,
        SUM(CASE WHEN r.rating <= 2 THEN 1 ELSE 0 END) AS negative_reviews,
        MAX(r.review_date) AS last_review_date,
        SUM(r.likes) AS total_likes,
        SUM(r.helpful_count) AS total_helpful_count
    FROM products p
    LEFT JOIN product_reviews r ON p.product_id = r.product_id
    GROUP BY p.product_id, p.name, p.category;
    
    -- 7. Customer Activity Log Summary
    DROP VIEW IF EXISTS vw_customer_activity_summary;
    CREATE VIEW vw_customer_activity_summary AS
    SELECT
        tl.user_id AS customer_id,
        c.first_name || ' ' || c.last_name AS customer_name,
        COUNT(tl.log_id) AS activity_count,
        SUM(CASE WHEN tl.action = 'view' THEN 1 ELSE 0 END) AS view_count,
        SUM(CASE WHEN tl.action = 'update' THEN 1 ELSE 0 END) AS update_count,
        SUM(CASE WHEN tl.entity_type = 'product' THEN 1 ELSE 0 END) AS product_interactions,
        SUM(CASE WHEN tl.entity_type = 'order' THEN 1 ELSE 0 END) AS order_interactions,
        MAX(tl.timestamp) AS last_activity_date
    FROM transaction_logs tl
    JOIN customers c ON tl.user_id = c.customer_id
    WHERE tl.user_type = 'customer'
    GROUP BY tl.user_id, c.first_name, c.last_name;
    
    -- 8. Employee Performance Metrics
    DROP VIEW IF EXISTS vw_employee_performance_metrics;
    CREATE VIEW vw_employee_performance_metrics AS
    SELECT
        e.employee_id,
        e.first_name || ' ' || e.last_name AS employee_name,
        e.position,
        e.department,
        o.name AS office_name,
        COUNT(tl.log_id) AS activity_count,
        COUNT(DISTINCT pr.review_id) AS customer_responses,
        AVG(pr.rating) AS avg_rating_of_responses,
        COUNT(DISTINCT im.movement_id) AS inventory_movements_handled
    FROM employees e
    JOIN offices o ON e.office_id = o.office_id
    LEFT JOIN transaction_logs tl ON e.employee_id = tl.user_id AND tl.user_type = 'employee'
    LEFT JOIN product_reviews pr ON e.employee_id = pr.response_employee_id
    LEFT JOIN inventory_movements im ON e.employee_id = im.employee_id
    GROUP BY e.employee_id, e.first_name, e.last_name, e.position, e.department, o.name;
    
    -- Create supporting indexes for the views
    
    -- Indexes for Product Sales Summary
    CREATE INDEX IF NOT EXISTS idx_order_items_product_order ON order_items(product_id, order_id);
    
    -- Indexes for Monthly Sales Trends
    CREATE INDEX IF NOT EXISTS idx_orders_date_status ON orders(order_date, status);
    
    -- Indexes for Inventory Status
    CREATE INDEX IF NOT EXISTS idx_inventory_product_qty ON inventory(product_id, quantity);
    
    -- Indexes for Customer Purchase Summary
    CREATE INDEX IF NOT EXISTS idx_orders_customer_date ON orders(customer_id, order_date);
    
    -- Indexes for Product Review Statistics
    CREATE INDEX IF NOT EXISTS idx_reviews_product_rating ON product_reviews(product_id, rating);
    
    -- Indexes for Transaction Logs
    CREATE INDEX IF NOT EXISTS idx_transaction_logs_user_entity ON transaction_logs(user_id, user_type, entity_type);
    """)
    
    conn.commit()
    return

def seed_database(db_path=None):
    """Main function to seed the database with all tables."""
    if db_path is None:
        db_path = "example.sqlite"
        
    conn = sqlite3.connect(db_path)
    
    # Create schema
    print("Creating database schema...")
    create_database_schema(conn)
    create_database_schema_part2(conn)
    
    # Seed tables in proper order to maintain referential integrity
    print("Seeding offices...")
    seed_offices(conn)
    
    print("Seeding employees...")
    seed_employees(conn)
    
    print("Seeding customers...")
    seed_customers(conn)
    
    print("Seeding products...")
    seed_products(conn)
    
    print("Seeding inventory...")
    seed_inventory(conn)
    
    print("Seeding inventory movements...")
    seed_inventory_movements(conn)
    
    print("Seeding orders...")
    seed_orders(conn)
    
    print("Seeding order items...")
    seed_order_items(conn)
    
    print("Seeding product reviews...")
    seed_product_reviews(conn)
    
    print("Seeding transaction logs...")
    seed_transaction_logs(conn)
    
    # Create aggregated views
    print("Creating aggregated views...")
    create_aggregated_views(conn)
    
    print("Database seeding complete!")
    conn.close()
    return

if __name__ == "__main__":
    seed_database()
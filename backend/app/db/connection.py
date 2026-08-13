"""SQLite connection and initialization module."""

import os
import sqlite3

from app.config import get_settings


def get_db_path() -> str:
    """Extract the SQLite file path from database_url."""
    settings = get_settings()
    db_url = settings.database_url
    if db_url.startswith("sqlite:///"):
        return db_url.replace("sqlite:///", "")
    return "./data/app.db"


def ensure_data_dir() -> None:
    """Ensure the data directory exists."""
    db_path = get_db_path()
    data_dir = os.path.dirname(db_path)
    if data_dir:
        os.makedirs(data_dir, exist_ok=True)


def get_raw_connection() -> sqlite3.Connection:
    """Get a raw SQLite connection (check_same_thread=False for multi-threaded use)."""
    ensure_data_dir()
    return sqlite3.connect(get_db_path(), check_same_thread=False)


def init_sample_database() -> None:
    """Idempotently initialize the sample database: create tables and seed data."""
    ensure_data_dir()
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    # Business table: sales records
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            sale_date DATE NOT NULL,
            region TEXT NOT NULL
        )
        """
    )

    # Business table: employees
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            position TEXT NOT NULL,
            salary REAL NOT NULL,
            hire_date DATE NOT NULL
        )
        """
    )

    # Metadata table: sessions
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Metadata table: messages
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            sql_query TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
        )
        """
    )

    # Seed data: sales (only when the table is empty)
    cursor.execute("SELECT COUNT(*) FROM sales")
    if cursor.fetchone()[0] == 0:
        sales_data = [
            ("Laptop", "Electronics", 15, 5999.00, "2024-01-15", "East"),
            ("Wireless Mouse", "Electronics", 80, 99.00, "2024-01-15", "East"),
            ("Mechanical Keyboard", "Electronics", 45, 299.00, "2024-01-16", "North"),
            ("Monitor", "Electronics", 20, 1299.00, "2024-01-17", "South"),
            ("Office Chair", "Furniture", 30, 599.00, "2024-01-18", "East"),
            ("Office Desk", "Furniture", 15, 899.00, "2024-01-18", "North"),
            ("Printer Paper", "Office Supplies", 200, 29.00, "2024-01-19", "South"),
            ("Ballpoint Pen", "Office Supplies", 500, 5.00, "2024-01-19", "East"),
            ("Folder", "Office Supplies", 300, 15.00, "2024-01-20", "North"),
            ("Desk Lamp", "Furniture", 40, 199.00, "2024-01-20", "South"),
            ("Tablet", "Electronics", 25, 3299.00, "2024-01-21", "East"),
            ("Headphones", "Electronics", 60, 199.00, "2024-01-22", "North"),
            ("Projector", "Electronics", 8, 2999.00, "2024-01-23", "South"),
            ("Bookshelf", "Furniture", 12, 399.00, "2024-01-24", "East"),
            ("Whiteboard", "Office Supplies", 25, 149.00, "2024-01-25", "North"),
        ]
        cursor.executemany(
            "INSERT INTO sales (product_name, category, quantity, price, sale_date, region) VALUES (?, ?, ?, ?, ?, ?)",
            sales_data,
        )

    # Seed data: employees (only when the table is empty)
    cursor.execute("SELECT COUNT(*) FROM employees")
    if cursor.fetchone()[0] == 0:
        employees_data = [
            ("Alice Zhang", "Engineering", "Senior Engineer", 25000.00, "2020-03-15"),
            ("Bob Li", "Engineering", "Engineer", 18000.00, "2021-06-20"),
            ("Carol Wang", "Marketing", "Marketing Manager", 22000.00, "2019-08-10"),
            ("David Liu", "Marketing", "Marketing Specialist", 12000.00, "2022-01-05"),
            ("Eve Chen", "Finance", "Finance Lead", 20000.00, "2018-11-20"),
            ("Frank Zhao", "Finance", "Accountant", 15000.00, "2021-04-15"),
            ("Grace Sun", "HR", "HR Manager", 18000.00, "2020-07-01"),
            ("Henry Zhou", "Engineering", "Engineering Director", 35000.00, "2017-02-28"),
        ]
        cursor.executemany(
            "INSERT INTO employees (name, department, position, salary, hire_date) VALUES (?, ?, ?, ?, ?)",
            employees_data,
        )

    conn.commit()
    conn.close()
    print("Sample database initialized.")

"""SQLite connection and initialization module."""

import os
import random
import sqlite3

from app.config import get_settings


# ---------------------------------------------------------------------------
# Deterministic sample data
# ---------------------------------------------------------------------------

# (product_name, category, base_price, base_monthly_quantity)
_SALES_PRODUCTS: list[tuple[str, str, float, int]] = [
    # Electronics
    ("Wireless Mouse", "Electronics", 29.99, 90),
    ("Mechanical Keyboard", "Electronics", 79.99, 50),
    ('27" Monitor', "Electronics", 229.99, 25),
    ("Laptop", "Electronics", 899.99, 12),
    ("Tablet", "Electronics", 399.99, 18),
    ("Bluetooth Headphones", "Electronics", 89.99, 60),
    ("Bluetooth Speaker", "Electronics", 49.99, 45),
    ("Power Bank", "Electronics", 24.99, 80),
    # Office Supplies
    ("Printer Paper (500 ct)", "Office Supplies", 8.99, 220),
    ("Ballpoint Pens (Box of 12)", "Office Supplies", 4.99, 400),
    ("Sticky Notes (Pack)", "Office Supplies", 2.99, 150),
    ("Desk Organizer", "Office Supplies", 18.99, 60),
    ("Whiteboard Markers (Set)", "Office Supplies", 12.99, 90),
    ("Stapler", "Office Supplies", 7.99, 70),
    ("Binders (Pack of 6)", "Office Supplies", 3.99, 120),
    ("Precision Scissors", "Office Supplies", 5.99, 85),
    # Furniture
    ("Ergonomic Office Chair", "Furniture", 199.99, 25),
    ("Standing Desk", "Furniture", 449.99, 10),
    ("Bookshelf", "Furniture", 89.99, 15),
    ("LED Desk Lamp", "Furniture", 34.99, 40),
    ("Filing Cabinet", "Furniture", 129.99, 12),
    ("Ergonomic Footrest", "Furniture", 39.99, 30),
    # Appliances
    ("Air Fryer", "Appliances", 99.99, 20),
    ("Drip Coffee Maker", "Appliances", 79.99, 25),
    ("Electric Kettle", "Appliances", 29.99, 45),
    ("2-Slice Toaster", "Appliances", 39.99, 30),
    ("Countertop Blender", "Appliances", 59.99, 22),
    ("Compact Microwave", "Appliances", 149.99, 15),
    ("Robot Vacuum", "Appliances", 189.99, 12),
    ("Humidifier", "Appliances", 49.99, 28),
    # Sports & Outdoors
    ("Yoga Mat", "Sports & Outdoors", 19.99, 70),
    ("Adjustable Dumbbell Set", "Sports & Outdoors", 59.99, 25),
    ("Resistance Bands (Set)", "Sports & Outdoors", 14.99, 90),
    ("Jump Rope", "Sports & Outdoors", 9.99, 80),
    ("Insulated Water Bottle", "Sports & Outdoors", 14.99, 100),
    ("Hiking Backpack", "Sports & Outdoors", 79.99, 20),
    ("Camping Tent", "Sports & Outdoors", 129.99, 12),
    ("Outdoor Basketball", "Sports & Outdoors", 24.99, 35),
    # Toys & Games
    ("Building Blocks Set", "Toys & Games", 49.99, 40),
    ("1000-Piece Puzzle", "Toys & Games", 19.99, 55),
    ("Strategy Board Game", "Toys & Games", 39.99, 30),
    ("RC Off-Road Car", "Toys & Games", 29.99, 35),
    ("Plush Stuffed Bear", "Toys & Games", 15.99, 60),
    # Books
    ("Bestseller Novel", "Books", 14.99, 80),
    ("Cookbook", "Books", 24.99, 35),
    ("Programming Guide", "Books", 39.99, 30),
    ("Children's Storybook", "Books", 9.99, 90),
    # Clothing
    ("Cotton T-Shirt", "Clothing", 12.99, 120),
    ("Zip Hoodie", "Clothing", 39.99, 45),
    ("Slim-Fit Jeans", "Clothing", 49.99, 40),
    ("Running Shoes", "Clothing", 79.99, 30),
]

_SALES_REGIONS = ["East", "West", "North", "South"]
_SALES_MONTHS = [(year, month) for year in (2023, 2024) for month in range(1, 13)]

EXPECTED_SALES_ROWS = len(_SALES_PRODUCTS) * len(_SALES_MONTHS)

# (name, department, position, salary, hire_date)
_EMPLOYEES: list[tuple[str, str, str, float, str]] = [
    ("Alice Zhang", "Engineering", "Senior Engineer", 25000.0, "2020-03-15"),
    ("Bob Li", "Engineering", "Engineer", 18000.0, "2021-06-20"),
    ("Carol Wang", "Marketing", "Marketing Manager", 22000.0, "2019-08-10"),
    ("David Liu", "Marketing", "Marketing Specialist", 12000.0, "2022-01-05"),
    ("Eve Chen", "Finance", "Finance Lead", 20000.0, "2018-11-20"),
    ("Frank Zhao", "Finance", "Accountant", 15000.0, "2021-04-15"),
    ("Grace Sun", "HR", "HR Manager", 18000.0, "2020-07-01"),
    ("Henry Zhou", "Engineering", "Engineering Director", 35000.0, "2017-02-28"),
    ("Ivy Wu", "Sales", "Sales Director", 30000.0, "2019-05-12"),
    ("Jack Huang", "Sales", "Account Executive", 16000.0, "2023-02-01"),
    ("Karen Xu", "Operations", "Operations Manager", 19000.0, "2020-09-14"),
    ("Leo Tang", "Operations", "Supply Chain Analyst", 14000.0, "2022-08-08"),
    ("Mia Gao", "Finance", "Financial Analyst", 17000.0, "2021-11-01"),
    ("Nick Chen", "Engineering", "DevOps Engineer", 21000.0, "2022-04-18"),
]

EXPECTED_EMPLOYEE_ROWS = len(_EMPLOYEES)


def _seasonal_factor(category: str, month: int) -> float:
    """Holiday/season multipliers so time-series charts look realistic."""
    if category in ("Electronics", "Toys & Games") and month in (11, 12):
        return 1.8
    if category == "Sports & Outdoors" and month in (6, 7, 8):
        return 1.5
    if category == "Office Supplies" and month in (8, 9):
        return 1.3
    if category == "Books" and month in (5, 12):
        return 1.25
    if category == "Clothing" and month in (11, 12):
        return 1.4
    return 1.0


def build_sales_seed() -> list[tuple]:
    """Deterministic sales rows: one record per product per month (2023-01..2024-12)."""
    rng = random.Random(20240814)
    rows: list[tuple] = []
    for year, month in _SALES_MONTHS:
        for name, category, price, base_qty in _SALES_PRODUCTS:
            quantity = max(1, int(base_qty * _seasonal_factor(category, month) * rng.uniform(0.7, 1.3)))
            unit_price = round(price * rng.uniform(0.95, 1.05), 2)
            region = _SALES_REGIONS[rng.randrange(len(_SALES_REGIONS))]
            rows.append((name, category, quantity, unit_price, f"{year}-{month:02d}-01", region))
    return rows


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
            data_json TEXT,
            chart_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
        )
        """
    )
    _ensure_chat_message_columns(conn)
    _normalize_legacy_messages(conn)

    # Seed data: sales (only when the table is empty)
    cursor.execute("SELECT COUNT(*) FROM sales")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO sales (product_name, category, quantity, price, sale_date, region) VALUES (?, ?, ?, ?, ?, ?)",
            build_sales_seed(),
        )

    # Seed data: employees (only when the table is empty)
    cursor.execute("SELECT COUNT(*) FROM employees")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO employees (name, department, position, salary, hire_date) VALUES (?, ?, ?, ?, ?)",
            _EMPLOYEES,
        )

    conn.commit()
    conn.close()
    print("Sample database initialized.")


def _ensure_chat_message_columns(conn: sqlite3.Connection) -> None:
    """Idempotently add chart persistence columns to existing databases."""
    columns = {row[1] for row in conn.execute("PRAGMA table_info(chat_messages)")}
    if "data_json" not in columns:
        conn.execute("ALTER TABLE chat_messages ADD COLUMN data_json TEXT")
    if "chart_json" not in columns:
        conn.execute("ALTER TABLE chat_messages ADD COLUMN chart_json TEXT")
    conn.commit()


def _normalize_legacy_messages(conn: sqlite3.Connection) -> None:
    """Idempotently re-normalize persisted assistant messages (markdown).

    Messages written before the normalization fix can contain glued headings
    (e.g. ``"...execute it.## 1. Plan"``). Only rows whose content actually
    changes are updated, so repeated startups are no-ops.
    """
    from app.core.markdown import normalize_markdown

    rows = conn.execute(
        "SELECT id, content FROM chat_messages WHERE role = 'assistant'"
    ).fetchall()
    changed = 0
    for message_id, content in rows:
        normalized = normalize_markdown(content)
        if normalized != content:
            conn.execute(
                "UPDATE chat_messages SET content = ? WHERE id = ?",
                (normalized, message_id),
            )
            changed += 1
    if changed:
        conn.commit()
        print(f"Normalized {changed} legacy message(s).")

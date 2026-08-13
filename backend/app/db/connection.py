"""SQLite 连接与初始化模块。"""

import os
import sqlite3

from app.config import get_settings


def get_db_path() -> str:
    """从 database_url 提取 SQLite 文件路径。"""
    settings = get_settings()
    db_url = settings.database_url
    if db_url.startswith("sqlite:///"):
        return db_url.replace("sqlite:///", "")
    return "./data/app.db"


def ensure_data_dir() -> None:
    """确保数据目录存在。"""
    db_path = get_db_path()
    data_dir = os.path.dirname(db_path)
    if data_dir:
        os.makedirs(data_dir, exist_ok=True)


def get_raw_connection() -> sqlite3.Connection:
    """获取原生 SQLite 连接（check_same_thread=False 供多线程使用）。"""
    ensure_data_dir()
    return sqlite3.connect(get_db_path(), check_same_thread=False)


def init_sample_database() -> None:
    """幂等初始化示例数据库：创建业务表、元数据表并写入种子数据。"""
    ensure_data_dir()
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    # 业务表：销售记录
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

    # 业务表：员工
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

    # 元数据表：会话
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

    # 元数据表：消息
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

    # 种子数据：sales（仅在表为空时写入）
    cursor.execute("SELECT COUNT(*) FROM sales")
    if cursor.fetchone()[0] == 0:
        sales_data = [
            ("笔记本电脑", "电子产品", 15, 5999.00, "2024-01-15", "华东"),
            ("无线鼠标", "电子产品", 80, 99.00, "2024-01-15", "华东"),
            ("机械键盘", "电子产品", 45, 299.00, "2024-01-16", "华北"),
            ("显示器", "电子产品", 20, 1299.00, "2024-01-17", "华南"),
            ("办公椅", "家具", 30, 599.00, "2024-01-18", "华东"),
            ("办公桌", "家具", 15, 899.00, "2024-01-18", "华北"),
            ("打印纸", "办公用品", 200, 29.00, "2024-01-19", "华南"),
            ("签字笔", "办公用品", 500, 5.00, "2024-01-19", "华东"),
            ("文件夹", "办公用品", 300, 15.00, "2024-01-20", "华北"),
            ("台灯", "家具", 40, 199.00, "2024-01-20", "华南"),
            ("平板电脑", "电子产品", 25, 3299.00, "2024-01-21", "华东"),
            ("耳机", "电子产品", 60, 199.00, "2024-01-22", "华北"),
            ("投影仪", "电子产品", 8, 2999.00, "2024-01-23", "华南"),
            ("书架", "家具", 12, 399.00, "2024-01-24", "华东"),
            ("白板", "办公用品", 25, 149.00, "2024-01-25", "华北"),
        ]
        cursor.executemany(
            "INSERT INTO sales (product_name, category, quantity, price, sale_date, region) VALUES (?, ?, ?, ?, ?, ?)",
            sales_data,
        )

    # 种子数据：employees（仅在表为空时写入）
    cursor.execute("SELECT COUNT(*) FROM employees")
    if cursor.fetchone()[0] == 0:
        employees_data = [
            ("张伟", "技术部", "高级工程师", 25000.00, "2020-03-15"),
            ("李娜", "技术部", "工程师", 18000.00, "2021-06-20"),
            ("王芳", "市场部", "市场经理", 22000.00, "2019-08-10"),
            ("刘洋", "市场部", "市场专员", 12000.00, "2022-01-05"),
            ("陈明", "财务部", "财务主管", 20000.00, "2018-11-20"),
            ("赵丽", "财务部", "会计", 15000.00, "2021-04-15"),
            ("孙强", "人事部", "人事经理", 18000.00, "2020-07-01"),
            ("周杰", "技术部", "技术总监", 35000.00, "2017-02-28"),
        ]
        cursor.executemany(
            "INSERT INTO employees (name, department, position, salary, hire_date) VALUES (?, ?, ?, ?, ?)",
            employees_data,
        )

    conn.commit()
    conn.close()
    print("Sample database initialized.")

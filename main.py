from fastmcp import FastMCP
import sqlite3
from pathlib import Path
import json

# -----------------------------
# Storage location (writable)
# -----------------------------
APP_DIR = Path.home() / ".expense_tracker"
APP_DIR.mkdir(parents=True, exist_ok=True)

DB_NAME = "personal_expence_tracker.db"  
DB_FILE_PATH = str(APP_DIR / DB_NAME)

CATEGORIES_NAME = "categories.json"
CATEGORIES_PATH = APP_DIR / CATEGORIES_NAME

mcp = FastMCP("ExpenseTracker")


# -----------------------------
# SQLite helpers
# -----------------------------
def get_conn() -> sqlite3.Connection:
    """
    Opens SQLite in read/write/create mode (rwc) so permission issues show up immediately.
    Sets WAL mode for better concurrency & fewer locking issues.
    """
    conn = sqlite3.connect(f"file:{DB_FILE_PATH}?mode=rwc", uri=True, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn


def ensure_categories_file():
    if not CATEGORIES_PATH.exists():
        default = {
            "categories": [
                {"name": "Food", "subcategories": ["Groceries", "Dining", "Snacks"]},
                {"name": "Transport", "subcategories": ["Bus", "Train", "Fuel", "Taxi"]},
                {"name": "Rent", "subcategories": ["Rent"]},
                {"name": "Bills", "subcategories": ["Electric", "Gas", "Internet", "Phone"]},
                {"name": "Shopping", "subcategories": ["Clothes", "Electronics", "Other"]},
                {"name": "Health", "subcategories": ["Medicine", "Doctor", "Gym"]},
                {"name": "Other", "subcategories": ["Misc"]},
            ]
        }
        CATEGORIES_PATH.write_text(json.dumps(default, indent=2), encoding="utf-8")


def init_db():
    with get_conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS credits(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)


ensure_categories_file()
init_db()


# -----------------------------
# Tools: Expenses
# -----------------------------
@mcp.tool()
def add_expense(date: str, amount: float, category: str, subcategory: str = "", note: str = ""):
    """Add a new expense entry to the database."""
    try:
        with get_conn() as c:
            cur = c.execute(
                "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
                (date, amount, category, subcategory, note)
            )
            return {"status": "ok", "id": cur.lastrowid, "db_path": DB_FILE_PATH}
    except Exception as e:
        return {"status": "error", "error": repr(e), "db_path": DB_FILE_PATH}


@mcp.tool()
def list_expenses(start_date: str, end_date: str):
    """List expense entries within an inclusive date range."""
    try:
        with get_conn() as c:
            cur = c.execute(
                """
                SELECT id, date, amount, category, subcategory, note
                FROM expenses
                WHERE date BETWEEN ? AND ?
                ORDER BY id ASC
                """,
                (start_date, end_date)
            )
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        return {"status": "error", "error": repr(e), "db_path": DB_FILE_PATH}


@mcp.tool()
def remove_expenses(date: str, amount: float, category: str, subcategory: str = "", note: str = ""):
    """Delete expenses matching the specified criteria."""
    try:
        with get_conn() as c:
            cur = c.execute(
                """
                DELETE FROM expenses
                WHERE date = ? AND amount = ? AND category = ? AND subcategory = ? AND note = ?
                """,
                (date, amount, category, subcategory, note)
            )
            if cur.rowcount > 0:
                return {"status": "ok", "message": f"Deleted {cur.rowcount} expense(s)"}
            return {"status": "error", "message": "No matching expenses found"}
    except Exception as e:
        return {"status": "error", "error": repr(e), "db_path": DB_FILE_PATH}


@mcp.tool()
def edit_expenses(expense_id: int, date=None, amount=None, category=None, subcategory=None, note=None):
    """
    Edit an existing expense. Provide only fields you want to update.
    Example: edit_expenses(3, amount=12.50, note="updated")
    """
    try:
        update_fields = []
        params = []

        if date is not None:
            update_fields.append("date = ?")
            params.append(date)
        if amount is not None:
            update_fields.append("amount = ?")
            params.append(amount)
        if category is not None:
            update_fields.append("category = ?")
            params.append(category)
        if subcategory is not None:
            update_fields.append("subcategory = ?")
            params.append(subcategory)
        if note is not None:
            update_fields.append("note = ?")
            params.append(note)

        if not update_fields:
            return {"status": "error", "message": "No fields provided to update"}

        params.append(expense_id)
        query = f"UPDATE expenses SET {', '.join(update_fields)} WHERE id = ?"

        with get_conn() as c:
            cur = c.execute(query, params)
            if cur.rowcount > 0:
                return {"status": "ok", "message": f"Expense {expense_id} updated successfully"}
            return {"status": "error", "message": f"Expense {expense_id} not found"}

    except Exception as e:
        return {"status": "error", "error": repr(e), "db_path": DB_FILE_PATH}


@mcp.tool()
def summarize(start_date: str, end_date: str, category: str = None):
    """Summarize expenses by category within an inclusive date range."""
    try:
        with get_conn() as c:
            query = """
                SELECT category, SUM(amount) AS total_amount
                FROM expenses
                WHERE date BETWEEN ? AND ?
            """
            params = [start_date, end_date]

            if category:
                query += " AND category = ?"
                params.append(category)

            query += " GROUP BY category ORDER BY category ASC"
            cur = c.execute(query, params)
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        return {"status": "error", "error": repr(e), "db_path": DB_FILE_PATH}


# -----------------------------
# Tools: Credits
# -----------------------------
@mcp.tool()
def credit_amount(date: str, amount: float, category: str, subcategory: str = "", note: str = ""):
    """Add a new credit/income entry to the database."""
    try:
        with get_conn() as c:
            cur = c.execute(
                "INSERT INTO credits(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
                (date, amount, category, subcategory, note)
            )
            return {"status": "ok", "id": cur.lastrowid, "db_path": DB_FILE_PATH}
    except Exception as e:
        return {"status": "error", "error": repr(e), "db_path": DB_FILE_PATH}


@mcp.tool()
def list_credits(start_date: str, end_date: str):
    """List credits entries within an inclusive date range."""
    try:
        with get_conn() as c:
            cur = c.execute(
                """
                SELECT id, date, amount, category, subcategory, note
                FROM credits
                WHERE date BETWEEN ? AND ?
                ORDER BY id ASC
                """,
                (start_date, end_date)
            )
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        return {"status": "error", "error": repr(e), "db_path": DB_FILE_PATH}


@mcp.tool()
def remove_credits(date: str, amount: float, category: str, subcategory: str = "", note: str = ""):
    """Delete credits matching the specified criteria."""
    try:
        with get_conn() as c:
            cur = c.execute(
                """
                DELETE FROM credits
                WHERE date = ? AND amount = ? AND category = ? AND subcategory = ? AND note = ?
                """,
                (date, amount, category, subcategory, note)
            )
            if cur.rowcount > 0:
                return {"status": "ok", "message": f"Deleted {cur.rowcount} credit(s)"}
            return {"status": "error", "message": "No matching credits found"}
    except Exception as e:
        return {"status": "error", "error": repr(e), "db_path": DB_FILE_PATH}


@mcp.tool()
def edit_credits(credit_id: int, date=None, amount=None, category=None, subcategory=None, note=None):
    """Edit an existing credit. Provide only fields you want to update."""
    try:
        update_fields = []
        params = []

        if date is not None:
            update_fields.append("date = ?")
            params.append(date)
        if amount is not None:
            update_fields.append("amount = ?")
            params.append(amount)
        if category is not None:
            update_fields.append("category = ?")
            params.append(category)
        if subcategory is not None:
            update_fields.append("subcategory = ?")
            params.append(subcategory)
        if note is not None:
            update_fields.append("note = ?")
            params.append(note)

        if not update_fields:
            return {"status": "error", "message": "No fields provided to update"}

        params.append(credit_id)
        query = f"UPDATE credits SET {', '.join(update_fields)} WHERE id = ?"

        with get_conn() as c:
            cur = c.execute(query, params)
            if cur.rowcount > 0:
                return {"status": "ok", "message": f"Credit {credit_id} updated successfully"}
            return {"status": "error", "message": f"Credit {credit_id} not found"}

    except Exception as e:
        return {"status": "error", "error": repr(e), "db_path": DB_FILE_PATH}


@mcp.tool()
def summarize_credit(start_date: str, end_date: str, category: str = None):
    """Summarize credits by category within an inclusive date range."""
    try:
        with get_conn() as c:
            query = """
                SELECT category, SUM(amount) AS total_amount
                FROM credits
                WHERE date BETWEEN ? AND ?
            """
            params = [start_date, end_date]

            if category:
                query += " AND category = ?"
                params.append(category)

            query += " GROUP BY category ORDER BY category ASC"
            cur = c.execute(query, params)
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        return {"status": "error", "error": repr(e), "db_path": DB_FILE_PATH}


# -----------------------------
# Resource: Categories
# -----------------------------
@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    # Read fresh each time so you can edit without restarting
    ensure_categories_file()
    return CATEGORIES_PATH.read_text(encoding="utf-8")


# -----------------------------
# Run server
# -----------------------------
if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)

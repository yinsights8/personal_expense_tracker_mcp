from fastmcp import FastMCP
import aiosqlite
from pathlib import Path
import json
from contextlib import asynccontextmanager

# -----------------------------
# Storage location (writable)
# -----------------------------
APP_DIR = Path.home() / ".expense_tracker"
APP_DIR.mkdir(parents=True, exist_ok=True)

DB_NAME = "personal_expence_tracker.db"  # keep your original name
DB_FILE_PATH = APP_DIR / DB_NAME

CATEGORIES_NAME = "categories.json"
CATEGORIES_PATH = APP_DIR / CATEGORIES_NAME

mcp = FastMCP("ExpenseTracker")


# -----------------------------
# Helpers
# -----------------------------
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


@asynccontextmanager
async def get_conn():
    """
    Async SQLite connection. mode=rwc makes permission issues explicit.
    WAL improves reliability & reduces locking issues.
    """
    # Use URI for mode=rwc
    db_uri = f"file:{DB_FILE_PATH}?mode=rwc"
    conn = await aiosqlite.connect(db_uri, uri=True, timeout=30)
    conn.row_factory = aiosqlite.Row

    try:
        await conn.execute("PRAGMA foreign_keys = ON;")
        await conn.execute("PRAGMA journal_mode = WAL;")
        await conn.execute("PRAGMA synchronous = NORMAL;")
        yield conn
        await conn.commit()
    except:
        await conn.rollback()
        raise
    finally:
        await conn.close()


async def init_db():
    async with get_conn() as c:
        await c.execute("""
            CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)
        await c.execute("""
            CREATE TABLE IF NOT EXISTS credits(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)


def row_to_dict(row: aiosqlite.Row) -> dict:
    return dict(row) if row is not None else {}


# -----------------------------
# Tools: Expenses (async)
# -----------------------------
@mcp.tool()
async def add_expense(date: str, amount: float, category: str, subcategory: str = "", note: str = ""):
    """Add a new expense entry to the database."""
    try:
        async with get_conn() as c:
            cur = await c.execute(
                "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
                (date, amount, category, subcategory, note)
            )
            return {"status": "ok", "id": cur.lastrowid, "db_path": str(DB_FILE_PATH)}
    except Exception as e:
        return {"status": "error", "error": repr(e), "db_path": str(DB_FILE_PATH)}


@mcp.tool()
async def list_expenses(start_date: str, end_date: str):
    """List expense entries within an inclusive date range."""
    try:
        async with get_conn() as c:
            cur = await c.execute(
                """
                SELECT id, date, amount, category, subcategory, note
                FROM expenses
                WHERE date BETWEEN ? AND ?
                ORDER BY id ASC
                """,
                (start_date, end_date)
            )
            rows = await cur.fetchall()
            return [row_to_dict(r) for r in rows]
    except Exception as e:
        return {"status": "error", "error": repr(e), "db_path": str(DB_FILE_PATH)}


@mcp.tool()
async def remove_expenses(date: str, amount: float, category: str, subcategory: str = "", note: str = ""):
    """Delete expenses matching the specified criteria."""
    try:
        async with get_conn() as c:
            cur = await c.execute(
                """
                DELETE FROM expenses
                WHERE date = ? AND amount = ? AND category = ? AND subcategory = ? AND note = ?
                """,
                (date, amount, category, subcategory, note)
            )
            if cur.rowcount and cur.rowcount > 0:
                return {"status": "ok", "message": f"Deleted {cur.rowcount} expense(s)"}
            return {"status": "error", "message": "No matching expenses found"}
    except Exception as e:
        return {"status": "error", "error": repr(e), "db_path": str(DB_FILE_PATH)}


@mcp.tool()
async def edit_expenses(expense_id: int, date=None, amount=None, category=None, subcategory=None, note=None):
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

        async with get_conn() as c:
            cur = await c.execute(query, params)
            if cur.rowcount and cur.rowcount > 0:
                return {"status": "ok", "message": f"Expense {expense_id} updated successfully"}
            return {"status": "error", "message": f"Expense {expense_id} not found"}
    except Exception as e:
        return {"status": "error", "error": repr(e), "db_path": str(DB_FILE_PATH)}


@mcp.tool()
async def summarize(start_date: str, end_date: str, category: str = None):
    """Summarize expenses by category within an inclusive date range."""
    try:
        async with get_conn() as c:
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

            cur = await c.execute(query, params)
            rows = await cur.fetchall()
            return [row_to_dict(r) for r in rows]
    except Exception as e:
        return {"status": "error", "error": repr(e), "db_path": str(DB_FILE_PATH)}


# -----------------------------
# Tools: Credits (async)
# -----------------------------
@mcp.tool()
async def credit_amount(date: str, amount: float, category: str, subcategory: str = "", note: str = ""):
    """Add a new credit/income entry to the database."""
    try:
        async with get_conn() as c:
            cur = await c.execute(
                "INSERT INTO credits(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
                (date, amount, category, subcategory, note)
            )
            return {"status": "ok", "id": cur.lastrowid, "db_path": str(DB_FILE_PATH)}
    except Exception as e:
        return {"status": "error", "error": repr(e), "db_path": str(DB_FILE_PATH)}


@mcp.tool()
async def list_credits(start_date: str, end_date: str):
    """List credit entries within an inclusive date range."""
    try:
        async with get_conn() as c:
            cur = await c.execute(
                """
                SELECT id, date, amount, category, subcategory, note
                FROM credits
                WHERE date BETWEEN ? AND ?
                ORDER BY id ASC
                """,
                (start_date, end_date)
            )
            rows = await cur.fetchall()
            return [row_to_dict(r) for r in rows]
    except Exception as e:
        return {"status": "error", "error": repr(e), "db_path": str(DB_FILE_PATH)}


@mcp.tool()
async def remove_credits(date: str, amount: float, category: str, subcategory: str = "", note: str = ""):
    """Delete credits matching the specified criteria."""
    try:
        async with get_conn() as c:
            cur = await c.execute(
                """
                DELETE FROM credits
                WHERE date = ? AND amount = ? AND category = ? AND subcategory = ? AND note = ?
                """,
                (date, amount, category, subcategory, note)
            )
            if cur.rowcount and cur.rowcount > 0:
                return {"status": "ok", "message": f"Deleted {cur.rowcount} credit(s)"}
            return {"status": "error", "message": "No matching credits found"}
    except Exception as e:
        return {"status": "error", "error": repr(e), "db_path": str(DB_FILE_PATH)}


@mcp.tool()
async def edit_credits(credit_id: int, date=None, amount=None, category=None, subcategory=None, note=None):
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

        async with get_conn() as c:
            cur = await c.execute(query, params)
            if cur.rowcount and cur.rowcount > 0:
                return {"status": "ok", "message": f"Credit {credit_id} updated successfully"}
            return {"status": "error", "message": f"Credit {credit_id} not found"}
    except Exception as e:
        return {"status": "error", "error": repr(e), "db_path": str(DB_FILE_PATH)}


@mcp.tool()
async def summarize_credit(start_date: str, end_date: str, category: str = None):
    """Summarize credits by category within an inclusive date range."""
    try:
        async with get_conn() as c:
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

            cur = await c.execute(query, params)
            rows = await cur.fetchall()
            return [row_to_dict(r) for r in rows]
    except Exception as e:
        return {"status": "error", "error": repr(e), "db_path": str(DB_FILE_PATH)}


# -----------------------------
# Resource: Categories
# -----------------------------
@mcp.resource("expense://categories", mime_type="application/json")
async def categories():
    # Read fresh each time
    ensure_categories_file()
    return CATEGORIES_PATH.read_text(encoding="utf-8")


# -----------------------------
# Run server
# -----------------------------
# async def main():
#     ensure_categories_file()
#     await init_db()
#     # mcp.run() is typically blocking; init happens before it starts serving.
#     mcp.run(transport="http", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)

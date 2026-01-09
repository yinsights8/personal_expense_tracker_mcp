from fastmcp import FastMCP
from src.initialize_db import init_db
import sqlite3
import os

DB_PATH = "src"
DB_NAME = "personal_expence_tracker.db"
CATEGORIES = "categories.json"  # required

if not os.path.exists(DB_PATH):
    os.makedirs(DB_PATH, exist_ok=True)

DB_FILE_PATH = os.path.join(DB_PATH, DB_NAME)
CATEGORIES_PATH = os.path.join(DB_PATH, CATEGORIES)  # manually create categories to present auto selection by llm

mcp = FastMCP("ExpenseTracker")



init_db = init_db(db_path=DB_FILE_PATH)

@mcp.tool()
def add_expense(date, amount, category, subcategory="", note=""):
    '''Add a new expense entry to the database.'''
    with sqlite3.connect(DB_FILE_PATH) as c:
        cur = c.execute(
            "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
            (date, amount, category, subcategory, note)
        )
        return {"status": "ok", "id": cur.lastrowid}
    
@mcp.tool()
def list_expenses(start_date, end_date):
    '''List expense entries within an inclusive date range.'''
    with sqlite3.connect(DB_FILE_PATH) as c:
        cur = c.execute(
            """
            SELECT id, date, amount, category, subcategory, note
            FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY id ASC
            """,
            (start_date, end_date)
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

@mcp.tool()
def summarize(start_date, end_date, category=None):
    '''Summarize expenses by category within an inclusive date range.'''
    with sqlite3.connect(DB_FILE_PATH) as c:
        query = (
            """
            SELECT category, SUM(amount) AS total_amount
            FROM expenses
            WHERE date BETWEEN ? AND ?
            """
        )
        params = [start_date, end_date]

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " GROUP BY category ORDER BY category ASC"

        cur = c.execute(query, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    # Read fresh each time so you can edit the file without restarting
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        import json
        return json.load(f)

@mcp.tool()
def add_credit(date, amount, category, subcategory="", note=""):
    '''Add a new credit/income entry to the database.'''
    with sqlite3.connect(DB_FILE_PATH) as c:
        cur = c.execute(
            "INSERT INTO credits(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
            (date, amount, category, subcategory, note)
        )
        return {"status": "ok", "id": cur.lastrowid}

@mcp.tool()
def list_credits(start_date, end_date):
    '''List credit/income entries within an inclusive date range.'''
    with sqlite3.connect(DB_FILE_PATH) as c:
        cur = c.execute(
            """
            SELECT id, date, amount, category, subcategory, note
            FROM credits
            WHERE date BETWEEN ? AND ?
            ORDER BY id ASC
            """,
            (start_date, end_date)
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

@mcp.tool()
def delete_expense(expense_id):
    '''Delete an expense entry by ID.'''
    with sqlite3.connect(DB_FILE_PATH) as c:
        cur = c.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        if cur.rowcount > 0:
            return {"status": "ok", "message": f"Expense {expense_id} deleted successfully"}
        else:
            return {"status": "error", "message": f"Expense {expense_id} not found"}

@mcp.tool()
def edit_expense(expense_id, date=None, amount=None, category=None, subcategory=None, note=None):
    '''Edit an existing expense entry. Only provide values for fields you want to update.'''
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

    with sqlite3.connect(DB_FILE_PATH) as c:
        cur = c.execute(query, params)
        if cur.rowcount > 0:
            return {"status": "ok", "message": f"Expense {expense_id} updated successfully"}
        else:
            return {"status": "error", "message": f"Expense {expense_id} not found"}

@mcp.tool()
def edit_credit(credit_id, date=None, amount=None, category=None, subcategory=None, note=None):
    '''Edit an existing credit entry. Only provide values for fields you want to update.'''
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

    with sqlite3.connect(DB_FILE_PATH) as c:
        cur = c.execute(query, params)
        if cur.rowcount > 0:
            return {"status": "ok", "message": f"Credit {credit_id} updated successfully"}
        else:
            return {"status": "error", "message": f"Credit {credit_id} not found"}

@mcp.tool()
def delete_credit(credit_id):
    '''Delete a credit entry by ID.'''
    with sqlite3.connect(DB_FILE_PATH) as c:
        cur = c.execute("DELETE FROM credits WHERE id = ?", (credit_id,))
        if cur.rowcount > 0:
            return {"status": "ok", "message": f"Credit {credit_id} deleted successfully"}
        else:
            return {"status": "error", "message": f"Credit {credit_id} not found"}

@mcp.tool()
def summarize_credits(start_date, end_date, category=None):
    '''Summarize credits by category within an inclusive date range.'''
    with sqlite3.connect(DB_FILE_PATH) as c:
        query = (
            """
            SELECT category, SUM(amount) AS total_amount
            FROM credits
            WHERE date BETWEEN ? AND ?
            """
        )
        params = [start_date, end_date]

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " GROUP BY category ORDER BY category ASC"

        cur = c.execute(query, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

if __name__ == "__main__":
    mcp.run()
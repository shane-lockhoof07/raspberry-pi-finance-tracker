from fastapi import APIRouter, Depends
from psycopg2.extras import RealDictCursor
from scripts.db import get_db_connection

router = APIRouter()

@router.get("/budget")
def get_budget(conn = Depends(get_db_connection)):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT category as key, amount as value FROM budget")
        budget_items = cur.fetchall()
        
        for item in budget_items:
            if 'key' in item:
                item['key'] = item['key'].title()
        
        return budget_items

@router.post("/budget/add")
def add_budget(data: dict, conn = Depends(get_db_connection)):
    key_to_add = data.get("key", "").lower()
    new_value = float(data.get("value", 0))
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM budget WHERE category = %s", (key_to_add,))
        if cur.fetchone() is None and key_to_add != "work" and key_to_add != "payments":
            cur.execute(
                "INSERT INTO budget (category, amount) VALUES (%s, %s)",
                (key_to_add, new_value)
            )
            conn.commit()
        
        cur.execute("SELECT category as key, amount as value FROM budget")
        budget_items = cur.fetchall()
        
        for item in budget_items:
            if 'key' in item:
                item['key'] = item['key'].title()
        
        return budget_items

@router.patch("/budget/update")
def update_budget(data: dict, conn = Depends(get_db_connection)):
    key_to_update = data.get("key", "").lower()
    new_value = float(data.get("value", 0))
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "UPDATE budget SET amount = %s WHERE category = %s AND category != 'work' AND category != 'payments'",
            (new_value, key_to_update)
        )
        conn.commit()
        
        cur.execute("SELECT category as key, amount as value FROM budget")
        budget_items = cur.fetchall()
        
        for item in budget_items:
            if 'key' in item:
                item['key'] = item['key'].title()
        
        return budget_items

@router.post("/budget/delete")
def delete_budget(data: dict, conn = Depends(get_db_connection)):
    key_to_delete = data.get("key", "").lower()
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "DELETE FROM budget WHERE category = %s AND category != 'work' AND category != 'payments'",
            (key_to_delete,)
        )
        conn.commit()
        
        cur.execute("SELECT category as key, amount as value FROM budget")
        budget_items = cur.fetchall()
        
        for item in budget_items:
            if 'key' in item:
                item['key'] = item['key'].title()
        
        return budget_items

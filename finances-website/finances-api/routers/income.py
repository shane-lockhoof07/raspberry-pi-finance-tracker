from fastapi import APIRouter, Depends
import psycopg2
from psycopg2.extras import RealDictCursor
from scripts.db import get_db_connection

router = APIRouter()

@router.get("/income")
def get_income(conn = Depends(get_db_connection)):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT year, month, amount 
            FROM income 
            ORDER BY year, array_position(
                ARRAY['January', 'February', 'March', 'April', 'May', 'June', 'July', 
                      'August', 'September', 'October', 'November', 'December'], 
                month
            )
        """)
        
        income_data = {}
        for row in cur.fetchall():
            year = str(row['year'])
            month = row['month']
            amount = float(row['amount'])
            
            if year not in income_data:
                income_data[year] = {}
                
            income_data[year][month] = amount
            
        return income_data

@router.post("/income")
def add_income(data: dict, conn = Depends(get_db_connection)):
    year = data['year']
    month = data['month']
    amount = float(data['amount'])
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT amount FROM income WHERE year = %s AND month = %s", 
                   (year, month))
        existing = cur.fetchone()
        
        if existing:
            new_amount = float(existing['amount']) + amount
            cur.execute("UPDATE income SET amount = %s WHERE year = %s AND month = %s",
                       (new_amount, year, month))
        else:
            cur.execute("INSERT INTO income (year, month, amount) VALUES (%s, %s, %s)",
                       (year, month, amount))
        
        conn.commit()
        
        return get_income(conn)

@router.post("/income/update")
def update_income(data: dict, conn = Depends(get_db_connection)):
    year = data['year']
    month = data['month']
    amount = float(data['amount'])
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            INSERT INTO income (year, month, amount)
            VALUES (%s, %s, %s)
            ON CONFLICT (year, month) DO UPDATE
            SET amount = %s
        """, (year, month, amount, amount))
        
        conn.commit()
        
        return get_income(conn)

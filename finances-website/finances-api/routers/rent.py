from fastapi import APIRouter, Depends
import json
from psycopg2.extras import RealDictCursor
from scripts.db import get_db_connection


router = APIRouter()

@router.get("/rent")
def get_rent(conn = Depends(get_db_connection)):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT year, month, amount FROM rent ORDER BY year, month")
        
        rent_data = {}
        for row in cur.fetchall():
            year_str = str(row['year'])
            month = row['month']
            amount = float(row['amount'])
            
            if year_str not in rent_data:
                rent_data[year_str] = {}
                
            rent_data[year_str][month] = amount
            
        return rent_data

@router.post("/rent")
def add_rent(data: dict, conn = Depends(get_db_connection)):
    year = data['year']
    month = data['month']
    amount = float(data['amount'])
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT amount FROM rent WHERE year = %s AND month = %s", 
                   (year, month))
        existing = cur.fetchone()
        
        if existing:
            new_amount = float(existing['amount']) + amount
            cur.execute("UPDATE rent SET amount = %s WHERE year = %s AND month = %s",
                       (new_amount, year, month))
        else:
            cur.execute("INSERT INTO rent (year, month, amount) VALUES (%s, %s, %s)",
                       (year, month, amount))
        
        conn.commit()
        
        return get_rent(conn)

@router.post("/rent/update")
def update_rent(data: dict, conn = Depends(get_db_connection)):
    year = data['year']
    month = data['month']
    amount = float(data['amount'])
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            INSERT INTO rent (year, month, amount)
            VALUES (%s, %s, %s)
            ON CONFLICT (year, month) DO UPDATE
            SET amount = %s
        """, (year, month, amount, amount))
        
        conn.commit()
        
        return get_rent(conn)

"Database connection error: unsupported operand type(s) for +: 'decimal.Decimal' and 'float'"
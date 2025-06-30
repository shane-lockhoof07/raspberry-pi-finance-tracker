from fastapi import APIRouter, Depends
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import uuid
from scripts.db import get_db_connection


router = APIRouter()

@router.get("/moneytransfers")
def get_money_transfers(conn = Depends(get_db_connection)):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT id, date, year, month, amount, type, description 
            FROM money_transfers
            ORDER BY year, month
        """)
        
        transfers = cur.fetchall()
        
        output = {}
        for transfer in transfers:
            year = transfer['year']
            month_num = transfer['month']
            
            month_name = datetime(2000, month_num, 1).strftime("%B")
            
            if year not in output:
                output[year] = {}
            
            if month_name not in output[year]:
                output[year][month_name] = []
            
            output[year][month_name].append({
                "id": transfer['id'],
                "amount": float(transfer['amount']),
                "month": month_name,
                "year": year,
                "type": transfer['type'],
                "description": transfer['description']
            })
        
        return output

@router.post("/moneytransfers")
def add_money_transfers(data: dict, conn = Depends(get_db_connection)):
    year = int(data["year"])
    month = datetime.strptime(data["month"], "%B").month
    day = 1
    transfer_id = str(uuid.uuid4())
    amount = float(data["amount"])
    transfer_type = data["type"]
    description = data["description"]
    
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO money_transfers (id, date, year, month, amount, type, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            transfer_id,
            datetime(year, month, day),
            str(year),
            month,
            amount,
            transfer_type,
            description
        ))
        conn.commit()
    
    return get_money_transfers(conn)

@router.post("/moneytransfers/update")
def update_money_transfer(data: dict, conn = Depends(get_db_connection)):
    transfer_id = data.get("id")
    if not transfer_id:
        return {"error": "Transfer ID is required"}
    
    update_parts = []
    params = []
    
    if "amount" in data:
        update_parts.append("amount = %s")
        params.append(data["amount"])
    
    if "type" in data:
        update_parts.append("type = %s")
        params.append(data["type"])
    
    if "description" in data:
        update_parts.append("description = %s")
        params.append(data["description"])
    
    date_changed = False
    year = None
    month = None
    
    if "year" in data:
        update_parts.append("year = %s")
        year = data["year"]
        params.append(year)
        date_changed = True
    
    if "month" in data:
        update_parts.append("month = %s")
        month_name = data["month"]
        month = datetime.strptime(month_name, "%B").month
        params.append(month)
        date_changed = True
    
    if date_changed:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT year, month FROM money_transfers WHERE id = %s", (transfer_id,))
            current = cur.fetchone()
            
            if not year:
                year = current['year']
            
            if not month:
                month = current['month']
            
            update_parts.append("date = %s")
            params.append(datetime(int(year), int(month), 1))
    
    params.append(transfer_id)
    
    if update_parts:
        with conn.cursor() as cur:
            query = f"UPDATE money_transfers SET {', '.join(update_parts)} WHERE id = %s"
            cur.execute(query, params)
            conn.commit()
    
    return get_money_transfers(conn)


@router.post("/moneytransfers/delete/{item_id}")
def delete_money_transfer(item_id: str, conn = Depends(get_db_connection)):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM money_transfers WHERE id = %s", (item_id,))
        conn.commit()
    
    return get_money_transfers(conn)

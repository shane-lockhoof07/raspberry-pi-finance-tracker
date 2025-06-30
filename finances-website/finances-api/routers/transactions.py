from fastapi import APIRouter, Depends, HTTPException
import psycopg2
from psycopg2.extras import RealDictCursor
from scripts import transaction_parser
import uuid
import string
from datetime import datetime
from scripts.db import get_db_connection

router = APIRouter()


@router.get("/transactions/uncategorized")
async def get_uncategorized_transactions(conn = Depends(get_db_connection)):
    try:
        print("Starting transaction parsing")
        await transaction_parser.parse_transactions()
        print("Transaction parsing completed")
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            try:
                # Query for transactions with empty categories
                print("Querying for uncategorized transactions")
                cur.execute("""
                    SELECT id, card_issuer, date, month, day, year, amount, vendor, category, line_id
                    FROM transactions 
                    WHERE category = '' OR category IS NULL
                    ORDER BY date DESC
                """)
                
                uncategorized = cur.fetchall()
                print(f"Found {len(uncategorized)} uncategorized transactions")
                
                # Query for misformatted transactions
                print("Querying for misformatted transactions")
                cur.execute("SELECT id, data FROM misformatted_transactions")
                misformatted_rows = cur.fetchall()
                misformatted = [row['data'] for row in misformatted_rows]
                print(f"Found {len(misformatted)} misformatted transactions")
                
                return {
                    "transactions": uncategorized,
                    "misformatted_transactions": misformatted
                }
            except Exception as e:
                print(f"Database query error: {str(e)}")
                import traceback
                print(traceback.format_exc())
                return {
                    "transactions": [],
                    "misformatted_transactions": [],
                    "error": f"Database query error: {str(e)}"
                }
    except Exception as e:
        print(f"Transaction processing error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {
            "transactions": [],
            "misformatted_transactions": [],
            "error": f"Transaction processing error: {str(e)}"
        }


@router.get("/transactions")
async def get_all_transactions(conn = Depends(get_db_connection)):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT id, card_issuer, date, month, day, year, amount, vendor, category, line_id
            FROM transactions
            ORDER BY date DESC
        """)
        
        transactions = cur.fetchall()
        
        return {
            "transactions": transactions
        }


@router.post("/transactions")
async def update_transaction_category(transaction: dict, conn = Depends(get_db_connection)):
    try:
        with conn.cursor() as cur:
            # Update category in the transactions table
            cur.execute("""
                UPDATE transactions 
                SET category = %s
                WHERE id = %s
            """, (
                transaction["category"],
                transaction["id"]
            ))
            
            # Check if any rows were updated
            if cur.rowcount == 0:
                # If no rows updated, this is a new transaction - insert it
                cur.execute("""
                    INSERT INTO transactions 
                    (id, card_issuer, date, month, day, year, amount, vendor, category, line_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    transaction["id"],
                    transaction["card_issuer"],
                    transaction["date"],
                    transaction["month"],
                    transaction["day"],
                    transaction["year"],
                    transaction["amount"],
                    transaction["vendor"],
                    transaction["category"],
                    transaction["line_id"]
                ))
            
            conn.commit()
    
        return {"status": "success", "message": "Transaction category updated"}
    except psycopg2.errors.UniqueViolation as e:
        conn.rollback()
        if "unique_transaction" in str(e):
            return {"status": "success", "message": "Transaction already exists (no changes needed)"}
        else:
            raise HTTPException(status_code=409, detail=f"Conflict error: {str(e)}")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating transaction: {str(e)}")


@router.post("/transactions/add")
async def add_transaction(data: dict, conn = Depends(get_db_connection)):
    try:
        with conn.cursor() as cur:
            if "reference_data" in data and "index" in data:
                cur.execute("SELECT data FROM misformatted_transactions WHERE id = %s", (data["index"],))
                misformatted = cur.fetchone()[0]
                
                if misformatted == data["reference_data"]:
                    cur.execute("DELETE FROM misformatted_transactions WHERE id = %s", (data["index"],))
                    
                    day, month, year = data["date"].split("-")
                    date_obj = datetime(int(year), int(month), int(day))
                    
                    transaction_id = str(uuid.uuid4())
                    
                    cur.execute("""
                        INSERT INTO transactions 
                        (id, card_issuer, date, month, day, year, amount, vendor, category, line_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        transaction_id,
                        "misformatted",
                        date_obj,
                        int(month),
                        int(day),
                        int(year),
                        float(data["amount"]),
                        string.capwords(data["vendor"]),
                        data["category"],
                        -1
                    ))
                    
                    conn.commit()
                    
                    cur.execute("SELECT id, data FROM misformatted_transactions")
                    remaining = [row['data'] for row in cur.fetchall()]
                    
                    return remaining
                    
            raise HTTPException(status_code=417, detail="Reference data does not match misformatted transaction")
                
    except Exception as e:
        print(f"Error adding transaction: {str(e)}")
        raise HTTPException(status_code=417, detail=f"Failed to add transaction: {str(e)}")

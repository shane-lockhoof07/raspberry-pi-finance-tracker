from fastapi import APIRouter, Depends
import psycopg2
from psycopg2.extras import RealDictCursor
from scripts.db import get_db_connection
import calendar
from datetime import datetime, date, timedelta

router = APIRouter()

DEFAULTS = [
    {'day': 1, 'source': 'Wells Fargo', 'amount': 0},
    {'day': 1, 'source': 'Rent', 'amount': -2124.8},
    {'day': 10, 'source': 'Bank of America', 'amount': 0},
    {'day': 11, 'source': 'Apple', 'amount': -10},
    {'day': 11, 'source': 'Bilt', 'amount': -150},
    {'day': 12, 'source': 'Capital One Venture', 'amount': 0},
    {'day': 15, 'source': 'Shane Pay 1', 'amount': 2703.9},
    {'day': 17, 'source': 'AMEX Delta', 'amount': 0},
    {'day': 20, 'source': 'Discover', 'amount': 0},
    {'day': 21, 'source': 'Citi Double', 'amount': 0},
    {'day': 23, 'source': 'Capital One Venture X', 'amount': -2000},
    {'day': 28, 'source': 'Citi Custom', 'amount': -200},
    {'day': 30, 'source': 'AMEX Blue', 'amount': -600},
    {'day': 30, 'source': 'Shane Pay 2', 'amount': 2703.9},
]

def get_last_day_of_month(year, month):
    """Return the last day of the given month and year."""
    return calendar.monthrange(year, month)[1]

def get_valid_day_for_month(day, year, month):
    """Ensure the day is valid for the given month, return last day if not."""
    last_day = get_last_day_of_month(year, month)
    return min(day, last_day)

def generate_defaults_for_period(start_date, end_date):
    """Generate default transactions for the given date range."""
    defaults_for_period = []
    current_date = start_date
    
    added_sources_by_month = {}
    
    while current_date <= end_date:
        year = current_date.year
        month = current_date.month
        month_key = f"{year}-{month}"
        
        if month_key not in added_sources_by_month:
            added_sources_by_month[month_key] = set()
        
        for default in DEFAULTS:
            source = default['source']
            
            if source in added_sources_by_month[month_key]:
                continue
            
            valid_day = get_valid_day_for_month(default['day'], year, month)
            
            transaction_date = date(year, month, valid_day)
            
            if start_date <= transaction_date <= end_date:
                defaults_for_period.append({
                    'date': transaction_date.isoformat(),
                    'source': source,
                    'amount': default['amount']
                })
                
                added_sources_by_month[month_key].add(source)
    
        current_date += timedelta(days=1)
    
    return defaults_for_period

@router.get("/moneyschedule")
def get_money_schedule(conn = Depends(get_db_connection)):
    today = date.today()
    end_date = today + timedelta(days=45)
    
    statement = """
    SELECT * FROM money_schedule
    WHERE date >= CURRENT_DATE 
    AND date <= CURRENT_DATE + INTERVAL '45 days'
    AND source != 'Bank'
    ORDER BY date ASC
    """
    
    bank_statement = """
    SELECT amount, date FROM money_schedule
    WHERE source = 'Bank'
    ORDER BY date DESC
    LIMIT 1
    """

    intermediate_statement = f""""""
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(statement)
        existing_transactions = cursor.fetchall()
        
        cursor.execute(bank_statement)
        bank_data = cursor.fetchone()
        bank_amount = bank_data['amount'] if bank_data else None
        bank_date = bank_data['date'] if bank_data else None

        if bank_date:
            intermediate_statement = """
            SELECT amount FROM money_schedule
            WHERE date >= %s
            AND date < CURRENT_DATE
            AND source != 'Bank'
            """
            cursor.execute(intermediate_statement, (bank_date,))
            intermediate_transactions = cursor.fetchall()
            if intermediate_transactions:
                intermediate_amount = sum(txn['amount'] for txn in intermediate_transactions)
                bank_amount += intermediate_amount
        
        default_transactions = generate_defaults_for_period(today, end_date)
        
        existing_identifiers = {
            f"{txn['date']}_{txn['source']}" 
            for txn in existing_transactions
        }
        
        transactions_to_add = []
        for txn in default_transactions:
            identifier = f"{txn['date']}_{txn['source']}"
            if identifier not in existing_identifiers:
                transactions_to_add.append(txn)
        
        if transactions_to_add:
            insert_query = """
            INSERT INTO money_schedule (date, source, amount)
            VALUES (%(date)s, %(source)s, %(amount)s)
            RETURNING id, date, source, amount
            """
            
            newly_added = []
            for txn in transactions_to_add:
                cursor.execute(insert_query, txn)
                newly_added.append(cursor.fetchone())
            
            conn.commit()
            
            existing_transactions.extend(newly_added)
            
            existing_transactions.sort(key=lambda x: x['date'])
    
    return {
        'transactions': existing_transactions, 
        'bank_balance': bank_amount if bank_amount else 0
    }


@router.post("/moneyschedule/add")
def add_money_schedule(data: dict, conn = Depends(get_db_connection)):
    year, month, day = data['date'].split("-")
    date_obj = datetime(int(year), int(month), int(day))
    source = data['source'].title()
    amount = float(data['amount'])
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            INSERT INTO money_schedule (date, source, amount)
            VALUES (%s, %s, %s)
            RETURNING id, date, source, amount
        """, (date_obj, source, amount))
        
        conn.commit()
        
    return get_money_schedule(conn)


@router.post("/moneyschedule/update")
def update_money_schedule(data: dict, conn = Depends(get_db_connection)):
    id = data['id']
    year, month, day = data['date'].split("-")
    date_obj = datetime(int(year), int(month), int(day))
    source = data['source']
    amount = float(data['amount'])
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            UPDATE money_schedule
            SET date = %s, source = %s, amount = %s
            WHERE id = %s
            RETURNING id, date, source, amount
        """, (date_obj, source, amount, id))
        
        conn.commit()
        
    return get_money_schedule(conn)

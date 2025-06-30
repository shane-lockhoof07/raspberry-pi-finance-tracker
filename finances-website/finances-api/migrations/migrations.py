#!/usr/bin/env python3
import json
import psycopg2
from datetime import datetime
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "finances")
DB_USER = os.getenv("POSTGRES_USER", "finances")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

# JSON file paths
REFERENCE_DATA_PATH = os.getenv("REFERENCE_DATA_PATH", "./reference_data")

def connect_to_database():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        sys.exit(1)

def create_tables(conn):
    """Create database tables based on the JSON data structure"""
    with conn.cursor() as cur:
        # Create tables
        cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            card_issuer TEXT,
            date DATE,
            month INTEGER,
            day INTEGER,
            year INTEGER,
            amount NUMERIC(10,2),
            vendor TEXT,
            category TEXT,
            line_id INTEGER
        );
        """)
        
        cur.execute("""
        CREATE TABLE IF NOT EXISTS uncategorized_transactions (
            id TEXT PRIMARY KEY,
            card_issuer TEXT,
            date DATE,
            month INTEGER,
            day INTEGER,
            year INTEGER,
            amount NUMERIC(10,2),
            vendor TEXT,
            category TEXT,
            line_id INTEGER
        );
        """)
        
        cur.execute("""
        CREATE TABLE IF NOT EXISTS misformatted_transactions (
            id INTEGER PRIMARY KEY,
            data JSONB
        );
        """)
        
        cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            name TEXT PRIMARY KEY,
            rank INTEGER
        );
        """)
        
        cur.execute("""
        CREATE TABLE IF NOT EXISTS budget (
            category TEXT PRIMARY KEY,
            amount NUMERIC(10,2)
        );
        """)
        
        cur.execute("""
        CREATE TABLE IF NOT EXISTS income (
            year INTEGER,
            month TEXT,
            amount NUMERIC(10,2),
            PRIMARY KEY (year, month)
        );
        """)
        
        cur.execute("""
        CREATE TABLE IF NOT EXISTS rent (
            year INTEGER,
            month TEXT,
            amount NUMERIC(10,2),
            PRIMARY KEY (year, month)
        );
        """)
        
        cur.execute("""
        CREATE TABLE IF NOT EXISTS money_transfers (
            id TEXT PRIMARY KEY,
            date DATE,
            year TEXT,
            month INTEGER,
            amount NUMERIC(10,2),
            type TEXT,
            description TEXT
        );
        """)
        
        cur.execute("""
        CREATE TABLE IF NOT EXISTS net_worth (
            year TEXT,
            month TEXT,
            savings NUMERIC(10,2),
            investments NUMERIC(10,2),
            PRIMARY KEY (year, month)
        );
        """)
        
        cur.execute("""
        CREATE TABLE IF NOT EXISTS transaction_processing_state (
            card_name TEXT PRIMARY KEY,
            last_line INTEGER
        );
        """)
        
    print("Tables created successfully")

def migrate_transactions(conn):
    """Migrate transaction data from JSON to PostgreSQL"""
    file_path = os.path.join(REFERENCE_DATA_PATH, "categorized_transactions.json")
    
    try:
        with open(file_path, 'r') as f:
            transactions = json.load(f)
            
        with conn.cursor() as cur:
            for transaction in transactions:
                try:
                    # Convert date string to date object
                    date_str = transaction.get("date", "").replace('Z', '+00:00')
                    date_obj = datetime.fromisoformat(date_str) if date_str else None
                    
                    cur.execute("""
                    INSERT INTO transactions 
                    (id, card_issuer, date, month, day, year, amount, vendor, category, line_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """, (
                        transaction.get("id"),
                        transaction.get("card_issuer"),
                        date_obj,
                        transaction.get("month"),
                        transaction.get("day"),
                        transaction.get("year"),
                        transaction.get("amount"),
                        transaction.get("vendor"),
                        transaction.get("category"),
                        transaction.get("line_id")
                    ))
                except Exception as e:
                    print(f"Error inserting transaction {transaction.get('id')}: {str(e)}")
        
        print(f"Migrated {len(transactions)} transactions")
    except Exception as e:
        print(f"Error migrating transactions: {str(e)}")

def migrate_uncategorized_transactions(conn):
    """Migrate uncategorized transaction data from JSON to PostgreSQL"""
    file_path = os.path.join(REFERENCE_DATA_PATH, "uncategorized_transactions.json")
    
    try:
        with open(file_path, 'r') as f:
            transactions = json.load(f)
            
        with conn.cursor() as cur:
            for transaction in transactions:
                try:
                    # Convert date string to date object
                    date_str = transaction.get("date", "").replace('Z', '+00:00')
                    date_obj = datetime.fromisoformat(date_str) if date_str else None
                    
                    cur.execute("""
                    INSERT INTO uncategorized_transactions 
                    (id, card_issuer, date, month, day, year, amount, vendor, category, line_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """, (
                        transaction.get("id"),
                        transaction.get("card_issuer"),
                        date_obj,
                        transaction.get("month"),
                        transaction.get("day"),
                        transaction.get("year"),
                        transaction.get("amount"),
                        transaction.get("vendor"),
                        transaction.get("category", ""),
                        transaction.get("line_id")
                    ))
                except Exception as e:
                    print(f"Error inserting uncategorized transaction {transaction.get('id')}: {str(e)}")
        
        print(f"Migrated {len(transactions)} uncategorized transactions")
    except Exception as e:
        print(f"Error migrating uncategorized transactions: {str(e)}")

def migrate_misformatted_transactions(conn):
    """Migrate misformatted transaction data from JSON to PostgreSQL"""
    file_path = os.path.join(REFERENCE_DATA_PATH, "misformatted_transactions.json")
    
    try:
        with open(file_path, 'r') as f:
            transactions = json.load(f)
            
        with conn.cursor() as cur:
            for i, transaction in enumerate(transactions):
                try:
                    cur.execute("""
                    INSERT INTO misformatted_transactions (id, data)
                    VALUES (%s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """, (i, json.dumps(transaction)))
                except Exception as e:
                    print(f"Error inserting misformatted transaction {i}: {str(e)}")
        
        print(f"Migrated {len(transactions)} misformatted transactions")
    except Exception as e:
        print(f"Error migrating misformatted transactions: {str(e)}")

def migrate_categories(conn):
    """Migrate categories from JSON to PostgreSQL"""
    file_path = os.path.join(REFERENCE_DATA_PATH, "categories.json")
    
    try:
        with open(file_path, 'r') as f:
            categories = json.load(f)
            
        with conn.cursor() as cur:
            for category, rank in categories.items():
                try:
                    cur.execute("""
                    INSERT INTO categories (name, rank)
                    VALUES (%s, %s)
                    ON CONFLICT (name) DO UPDATE SET rank = EXCLUDED.rank
                    """, (category, rank))
                except Exception as e:
                    print(f"Error inserting category {category}: {str(e)}")
        
        print(f"Migrated {len(categories)} categories")
    except Exception as e:
        print(f"Error migrating categories: {str(e)}")

def migrate_budget(conn):
    """Migrate budget from JSON to PostgreSQL"""
    file_path = os.path.join(REFERENCE_DATA_PATH, "budget.json")
    
    try:
        with open(file_path, 'r') as f:
            budget = json.load(f)
            
        with conn.cursor() as cur:
            for category, amount in budget.items():
                try:
                    cur.execute("""
                    INSERT INTO budget (category, amount)
                    VALUES (%s, %s)
                    ON CONFLICT (category) DO UPDATE SET amount = EXCLUDED.amount
                    """, (category, amount))
                except Exception as e:
                    print(f"Error inserting budget {category}: {str(e)}")
        
        print(f"Migrated {len(budget)} budget items")
    except Exception as e:
        print(f"Error migrating budget: {str(e)}")

def migrate_income(conn):
    """Migrate income from JSON to PostgreSQL"""
    file_path = os.path.join(REFERENCE_DATA_PATH, "income.json")
    
    try:
        with open(file_path, 'r') as f:
            income = json.load(f)
            
        with conn.cursor() as cur:
            count = 0
            for year, months in income.items():
                for month, amount in months.items():
                    try:
                        cur.execute("""
                        INSERT INTO income (year, month, amount)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (year, month) DO UPDATE SET amount = EXCLUDED.amount
                        """, (year, month, amount))
                        count += 1
                    except Exception as e:
                        print(f"Error inserting income {year}/{month}: {str(e)}")
        
        print(f"Migrated {count} income records")
    except Exception as e:
        print(f"Error migrating income: {str(e)}")

def migrate_rent(conn):
    """Migrate rent from JSON to PostgreSQL"""
    file_path = os.path.join(REFERENCE_DATA_PATH, "rent.json")
    
    try:
        with open(file_path, 'r') as f:
            rent = json.load(f)
            
        with conn.cursor() as cur:
            count = 0
            for year, months in rent.items():
                for month, amount in months.items():
                    try:
                        cur.execute("""
                        INSERT INTO rent (year, month, amount)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (year, month) DO UPDATE SET amount = EXCLUDED.amount
                        """, (year, month, amount))
                        count += 1
                    except Exception as e:
                        print(f"Error inserting rent {year}/{month}: {str(e)}")
        
        print(f"Migrated {count} rent records")
    except Exception as e:
        print(f"Error migrating rent: {str(e)}")

def migrate_money_transfers(conn):
    """Migrate money transfers from JSON to PostgreSQL"""
    file_path = os.path.join(REFERENCE_DATA_PATH, "money_transfers.json")
    
    try:
        with open(file_path, 'r') as f:
            transfers = json.load(f)
            
        with conn.cursor() as cur:
            for transfer in transfers:
                try:
                    # Convert date string to date object
                    date_str = transfer.get("date", "").replace('Z', '+00:00')
                    date_obj = datetime.fromisoformat(date_str) if date_str else None
                    
                    cur.execute("""
                    INSERT INTO money_transfers (id, date, year, month, amount, type, description)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """, (
                        transfer.get("id"),
                        date_obj,
                        transfer.get("year"),
                        transfer.get("month"),
                        transfer.get("amount"),
                        transfer.get("type"),
                        transfer.get("description")
                    ))
                except Exception as e:
                    print(f"Error inserting money transfer {transfer.get('id')}: {str(e)}")
        
        print(f"Migrated {len(transfers)} money transfers")
    except Exception as e:
        print(f"Error migrating money transfers: {str(e)}")

def migrate_net_worth(conn):
    """Migrate net worth from JSON to PostgreSQL"""
    file_path = os.path.join(REFERENCE_DATA_PATH, "net_worth.json")
    
    try:
        with open(file_path, 'r') as f:
            net_worth = json.load(f)
            
        with conn.cursor() as cur:
            count = 0
            for year, months in net_worth.items():
                for month, values in months.items():
                    try:
                        cur.execute("""
                        INSERT INTO net_worth (year, month, savings, investments)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (year, month) DO UPDATE SET 
                            savings = EXCLUDED.savings,
                            investments = EXCLUDED.investments
                        """, (
                            year, 
                            month, 
                            values.get("savings", 0), 
                            values.get("investments", 0)
                        ))
                        count += 1
                    except Exception as e:
                        print(f"Error inserting net worth {year}/{month}: {str(e)}")
        
        print(f"Migrated {count} net worth records")
    except Exception as e:
        print(f"Error migrating net worth: {str(e)}")

def migrate_last_line(conn):
    """Migrate last line data from JSON to PostgreSQL"""
    file_path = os.path.join(REFERENCE_DATA_PATH, "last_line.json")
    
    try:
        with open(file_path, 'r') as f:
            last_lines = json.load(f)
            
        with conn.cursor() as cur:
            for card, line in last_lines.items():
                try:
                    cur.execute("""
                    INSERT INTO transaction_processing_state (card_name, last_line)
                    VALUES (%s, %s)
                    ON CONFLICT (card_name) DO UPDATE SET last_line = EXCLUDED.last_line
                    """, (card, line))
                except Exception as e:
                    print(f"Error inserting last line for {card}: {str(e)}")
        
        print(f"Migrated {len(last_lines)} card processing states")
    except Exception as e:
        print(f"Error migrating last line: {str(e)}")

def main():
    print("Starting database migration...")
    
    # Connect to database
    conn = connect_to_database()
    
    # Create tables
    create_tables(conn)
    
    # Migrate data
    migrate_transactions(conn)
    migrate_uncategorized_transactions(conn)
    migrate_misformatted_transactions(conn)
    migrate_categories(conn)
    migrate_budget(conn)
    migrate_income(conn)
    migrate_rent(conn)
    migrate_money_transfers(conn)
    migrate_net_worth(conn)
    migrate_last_line(conn)
    
    # Close connection
    conn.close()
    
    print("Migration completed successfully")

if __name__ == "__main__":
    main()
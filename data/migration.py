#!/usr/bin/env python3
import json
import psycopg2
from psycopg2.extras import execute_batch
import os
import sys
from datetime import datetime
import uuid

# Database connection parameters
DB_HOST = "10.43.223.207"
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "finances")
DB_USER = os.environ.get("DB_USER", "finances")
DB_PASSWORD = "postgres-password"

# Path to reference data directory
REFERENCE_DATA_PATH = os.environ.get("REFERENCE_DATA_PATH", "./finances-website/finances-api/reference_data")

def connect_to_db():
    """Establish a connection to the PostgreSQL database"""
    try:
        print(f"Connecting to database {DB_NAME} at {DB_HOST}:{DB_PORT} with user {DB_USER}")
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        print("Successfully connected to the database")
        return conn
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        sys.exit(1)

def read_json_file(file_path):
    """Read a JSON file and return its content"""
    try:
        with open(file_path, 'r') as f:
          return json.load(f)
    except Exception as e:
        print(f"Error reading {file_path}: {str(e)}")
        return None

def migrate_categories(conn, cur):
    """Migrate categories data"""
    print("\nMigrating categories data...")
    categories_file = os.path.join(REFERENCE_DATA_PATH, "categories.json")
    
    categories = read_json_file(categories_file)
    if not categories:
        return
    
    try:
        # Create a list of tuples for batch execution
        category_tuples = [(category, rank) for category, rank in categories.items()]
        
        # Insert categories using execute_batch
        execute_batch(cur, """
            INSERT INTO categories (name, rank)
            VALUES (%s, %s)
            ON CONFLICT (name) DO UPDATE SET
                rank = EXCLUDED.rank
        """, category_tuples)
        
        conn.commit()
        print(f"Successfully migrated {len(category_tuples)} categories")
    except Exception as e:
        conn.rollback()
        print(f"Error migrating categories: {str(e)}")

def migrate_budget(conn, cur):
    """Migrate budget data"""
    print("\nMigrating budget data...")
    budget_file = os.path.join(REFERENCE_DATA_PATH, "budget.json")
    
    budget = read_json_file(budget_file)
    if not budget:
        return
    
    try:
        # Create a list of tuples for batch execution
        budget_tuples = [(category, amount) for category, amount in budget.items()]
        
        # Insert budget items using execute_batch
        execute_batch(cur, """
            INSERT INTO budget (category, amount)
            VALUES (%s, %s)
            ON CONFLICT (category) DO UPDATE SET
                amount = EXCLUDED.amount
        """, budget_tuples)
        
        conn.commit()
        print(f"Successfully migrated {len(budget_tuples)} budget items")
    except Exception as e:
        conn.rollback()
        print(f"Error migrating budget: {str(e)}")

def migrate_income(conn, cur):
    """Migrate income data"""
    print("\nMigrating income data...")
    income_file = os.path.join(REFERENCE_DATA_PATH, "income.json")
    
    income_data = read_json_file(income_file)
    if not income_data:
        return
    
    try:
        # Create a list of tuples for batch execution
        income_tuples = []
        for year, months in income_data.items():
            for month, amount in months.items():
                income_tuples.append((int(year), month, amount))
        
        # Insert income records using execute_batch
        execute_batch(cur, """
            INSERT INTO income (year, month, amount)
            VALUES (%s, %s, %s)
            ON CONFLICT (year, month) DO UPDATE SET
                amount = EXCLUDED.amount
        """, income_tuples)
        
        conn.commit()
        print(f"Successfully migrated {len(income_tuples)} income records")
    except Exception as e:
        conn.rollback()
        print(f"Error migrating income data: {str(e)}")

def migrate_rent(conn, cur):
    """Migrate rent data"""
    print("\nMigrating rent data...")
    rent_file = os.path.join(REFERENCE_DATA_PATH, "rent.json")
    
    rent_data = read_json_file(rent_file)
    if not rent_data:
        return
    
    try:
        # Create a list of tuples for batch execution
        rent_tuples = []
        for year, months in rent_data.items():
            for month, amount in months.items():
                rent_tuples.append((int(year), month, amount))
        
        # Insert rent records using execute_batch
        execute_batch(cur, """
            INSERT INTO rent (year, month, amount)
            VALUES (%s, %s, %s)
            ON CONFLICT (year, month) DO UPDATE SET
                amount = EXCLUDED.amount
        """, rent_tuples)
        
        conn.commit()
        print(f"Successfully migrated {len(rent_tuples)} rent records")
    except Exception as e:
        conn.rollback()
        print(f"Error migrating rent data: {str(e)}")

def migrate_money_transfers(conn, cur):
    """Migrate money transfers data"""
    print("\nMigrating money transfers data...")
    transfers_file = os.path.join(REFERENCE_DATA_PATH, "money_transfers.json")
    
    transfers = read_json_file(transfers_file)
    if not transfers:
        return
    
    try:
        # Create a list of tuples for batch execution
        transfer_tuples = []
        for transfer in transfers:
            # Convert date string to datetime object
            date_str = transfer["date"]
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            
            transfer_tuples.append((
                transfer["id"],
                date_obj,
                transfer["year"],
                transfer["month"],
                float(transfer["amount"]),
                transfer["type"],
                transfer["description"]
            ))
        
        # Insert money transfers using execute_batch
        execute_batch(cur, """
            INSERT INTO money_transfers (id, date, year, month, amount, type, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                date = EXCLUDED.date,
                year = EXCLUDED.year,
                month = EXCLUDED.month,
                amount = EXCLUDED.amount,
                type = EXCLUDED.type,
                description = EXCLUDED.description
        """, transfer_tuples)
        
        conn.commit()
        print(f"Successfully migrated {len(transfer_tuples)} money transfers")
    except Exception as e:
        conn.rollback()
        print(f"Error migrating money transfers: {str(e)}")

def migrate_net_worth(conn, cur):
    """Migrate net worth data"""
    print("\nMigrating net worth data...")
    net_worth_file = os.path.join(REFERENCE_DATA_PATH, "net_worth.json")
    
    net_worth_data = read_json_file(net_worth_file)
    if not net_worth_data:
        return
    
    try:
        # Create a list of tuples for batch execution
        net_worth_tuples = []
        for year, months in net_worth_data.items():
            for month, values in months.items():
                savings = values.get("savings", 0)
                investments = values.get("investments", 0)
                # Only add non-zero entries
                if savings > 0 or investments > 0:
                    net_worth_tuples.append((year, month, savings, investments))
        
        # Insert net worth records using execute_batch
        execute_batch(cur, """
            INSERT INTO net_worth (year, month, savings, investments)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (year, month) DO UPDATE SET
                savings = EXCLUDED.savings,
                investments = EXCLUDED.investments
        """, net_worth_tuples)
        
        conn.commit()
        print(f"Successfully migrated {len(net_worth_tuples)} net worth records")
    except Exception as e:
        conn.rollback()
        print(f"Error migrating net worth data: {str(e)}")

def migrate_transaction_processing_state(conn, cur):
    """Migrate transaction processing state"""
    print("\nMigrating transaction processing state...")
    last_line_file = os.path.join(REFERENCE_DATA_PATH, "last_line.json")
    
    last_line_data = read_json_file(last_line_file)
    if not last_line_data:
        return
    
    try:
        # Create a list of tuples for batch execution
        state_tuples = [(card_name, last_line) for card_name, last_line in last_line_data.items()]
        
        # Insert processing state records using execute_batch
        execute_batch(cur, """
            INSERT INTO transaction_processing_state (card_name, last_line)
            VALUES (%s, %s)
            ON CONFLICT (card_name) DO UPDATE SET
                last_line = EXCLUDED.last_line
        """, state_tuples)
        
        conn.commit()
        print(f"Successfully migrated {len(state_tuples)} transaction processing states")
    except Exception as e:
        conn.rollback()
        print(f"Error migrating transaction processing state: {str(e)}")

def migrate_transactions(conn, cur, table_name, file_name):
    """Migrate transactions to the specified table"""
    print(f"\nMigrating {table_name} data...")
    transactions_file = os.path.join(REFERENCE_DATA_PATH, file_name)
    
    transactions = read_json_file(transactions_file)
    if not transactions:
        print(f"No {table_name} to migrate (empty or missing file)")
        return
    
    try:
        # Create a list of tuples for batch execution
        transaction_tuples = []
        
        # Handle both list and dictionary formats
        if isinstance(transactions, list):
            for trans in transactions:
                # Convert date string to datetime object if it's a string
                date = trans.get("date")
                if isinstance(date, str):
                    date = datetime.fromisoformat(date.replace('Z', '+00:00'))
                
                transaction_tuples.append((
                    trans["id"],
                    trans["card_issuer"],
                    date,
                    trans["month"],
                    trans["day"],
                    trans["year"],
                    float(trans["amount"]),
                    trans["vendor"],
                    trans.get("category", ""),  # Category might be empty for uncategorized
                    trans["line_id"]
                ))
        
        if transaction_tuples:
            # Insert transactions using execute_batch
            execute_batch(cur, f"""
                INSERT INTO {table_name} (id, card_issuer, date, month, day, year, amount, vendor, category, line_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    card_issuer = EXCLUDED.card_issuer,
                    date = EXCLUDED.date,
                    month = EXCLUDED.month,
                    day = EXCLUDED.day,
                    year = EXCLUDED.year,
                    amount = EXCLUDED.amount,
                    vendor = EXCLUDED.vendor,
                    category = EXCLUDED.category,
                    line_id = EXCLUDED.line_id
            """, transaction_tuples)
            
            conn.commit()
            print(f"Successfully migrated {len(transaction_tuples)} {table_name}")
        else:
            print(f"No {table_name} to migrate (empty data)")
            
    except Exception as e:
        conn.rollback()
        print(f"Error migrating {table_name}: {str(e)}")

def migrate_misformatted_transactions(conn, cur):
    """Migrate misformatted transactions"""
    print("\nMigrating misformatted transactions...")
    misformatted_file = os.path.join(REFERENCE_DATA_PATH, "misformatted_transactions.json")
    misformatted = read_json_file(misformatted_file)
    if not misformatted:
        return
    
    try:
        # Create a list of tuples for batch execution
        misformatted_tuples = []
        
        for i, trans in enumerate(misformatted):
            misformatted_tuples.append((i, json.dumps(trans)))
        
        # Insert misformatted transactions using execute_batch
        if misformatted_tuples:
            execute_batch(cur, """
                INSERT INTO misformatted_transactions (id, data)
                VALUES (%s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    data = EXCLUDED.data
            """, misformatted_tuples)
            
            conn.commit()
            print(f"Successfully migrated {len(misformatted_tuples)} misformatted transactions")
        else:
            print("No misformatted transactions to migrate")
            
    except Exception as e:
        conn.rollback()
        print(f"Error migrating misformatted transactions: {str(e)}")

def check_tables(conn, cur):
    """Check if all required tables exist"""
    required_tables = [
        'budget', 'categories', 'income', 'misformatted_transactions',
        'money_transfers', 'net_worth', 'rent', 'transaction_processing_state',
        'transactions', 'uncategorized_transactions'
    ]
    
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    
    existing_tables = [row[0] for row in cur.fetchall()]
    
    missing_tables = [table for table in required_tables if table not in existing_tables]
    
    if missing_tables:
        print(f"Warning: The following tables are missing: {', '.join(missing_tables)}")
        return False
    
    print("All required tables exist.")
    return True

def main():
    """Main function to run the migration"""
    print("Starting PostgreSQL data migration...")
    
    # Connect to the database
    conn = connect_to_db()
    cur = conn.cursor()
    
    try:
        # Check if all tables exist
        if not check_tables(conn, cur):
            print("Please ensure all tables exist before running this script.")
        
        # Migrate each type of data
        migrate_categories(conn, cur)
        migrate_budget(conn, cur)
        migrate_income(conn, cur)
        migrate_rent(conn, cur)
        migrate_money_transfers(conn, cur)
        migrate_net_worth(conn, cur)
        migrate_transaction_processing_state(conn, cur)
        
        # Migrate transactions data
        migrate_transactions(conn, cur, "transactions", "categorized_transactions.json")
        migrate_transactions(conn, cur, "uncategorized_transactions", "uncategorized_transactions.json")
        migrate_misformatted_transactions(conn, cur)
        
        print("\nMigration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {str(e)}")
    finally:
        # Close the database connection
        cur.close()
        conn.close()
        print("Database connection closed")

if __name__ == "__main__":
    main()

import os
import pandas as pd
from models import transactions
import uuid
from datetime import datetime
import json
import math
import string
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv

# Load environment variables for database connection
load_dotenv()

# Database connection parameters
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "finances")
DB_USER = os.getenv("POSTGRES_USER", "finances")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

def get_db_connection():
    """Establish a connection to PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        return None

async def parse_transactions():
    """Parse transactions from files and store in PostgreSQL"""
    # Database connection
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database. Cannot process transactions.")
        return
    
    cur = conn.cursor()
    
    # Get transaction data directory and print absolute path
    directory = os.getenv("TRANSACTION_DATA_PATH", "./transaction_data")
    abs_directory = os.path.abspath(directory)
    print(f"TRANSACTION DATA DIRECTORY: {abs_directory}")
    
    # Check if directory exists
    if not os.path.exists(abs_directory):
        print(f"WARNING: Directory does not exist: {abs_directory}")
        try:
            os.makedirs(abs_directory, exist_ok=True)
            print(f"Created directory: {abs_directory}")
        except Exception as e:
            print(f"Failed to create directory: {str(e)}")
            return
    
    # List all files in the directory
    try:
        all_files = os.listdir(abs_directory)
        print(f"Found {len(all_files)} files in directory:")
        for f in all_files:
            full_path = os.path.join(abs_directory, f)
            file_size = os.path.getsize(full_path) if os.path.isfile(full_path) else "N/A (directory)"
            print(f"  - {f} ({file_size} bytes)")
    except Exception as e:
        print(f"Error listing directory contents: {str(e)}")
    
    misformatted_transactions = []
    
    for filename in os.listdir(abs_directory):
        file_path = os.path.join(abs_directory, filename)
        print(f"\n=== PROCESSING FILE: {file_path} ===")
        
        if not os.path.isfile(file_path):
            print(f"Skipping non-file: {file_path}")
            continue
            
        trans = None
        mis_trans = None
                
        # File type detection and processing
        if "discover" in file_path.lower():
            print(f"Processing Discover file: {file_path}")
            try:
                df, mis_trans = read_csv_file(file_path=file_path, sep=",")
                print(f"Discover file read successful. DataFrame shape: {df.shape}")
                print(f"First row sample: {df.iloc[0].to_dict() if not df.empty else 'Empty DataFrame'}")
                
                trans = parse(
                        df=df, 
                        card_name="Discover",
                        date_key="Trans. Date",
                        date_conversion="%m/%d/%Y",
                        debit_key="Amount",
                        vendor_key="Description",
                    )
                print(f"Parsing complete. Transactions count: {len(trans) if trans else 0}")
            except Exception as e:
                print(f"Error processing Discover file: {str(e)}")
                import traceback
                print(traceback.format_exc())
        elif "amex" in file_path.lower():
            print(f"Processing AMEX file: {file_path}")
            try:
                card_name = "amex_blue" if "blue" in os.path.basename(file_path).lower() else "amex_delta"
                print(f"Identified as {card_name}")
                                
                df, mis_trans = read_csv_file(file_path=file_path, sep=",")
                print(f"AMEX file read status: DataFrame {'empty' if df.empty else f'shape={df.shape}'}")
                
                if not df.empty:
                    print(f"First row sample: {df.iloc[0].to_dict() if len(df) > 0 else 'No rows'}")
                
                trans = parse(
                        df=df, 
                        card_name=card_name,
                        date_key="Date",
                        date_conversion="%m/%d/%Y",
                        debit_key="Amount",
                        vendor_key="Description",
                    )
                print(f"Parsing complete. Transactions count: {len(trans) if trans else 0}")
            except Exception as e:
                print(f"Error processing AMEX file: {str(e)}")
                import traceback
                print(traceback.format_exc())
        elif "capone" in file_path.lower():
            print(f"Processing Capital One file: {file_path}")
            card_name = "capone_venture_x" if "x" in os.path.basename(file_path).lower() else "capone_venture"
            df, mis_trans = read_csv_file(file_path=file_path, sep=",")
            trans = parse(
                    df=df, 
                    card_name=card_name,
                    date_key="Transaction Date",
                    date_conversion="%Y-%m-%d",
                    debit_key="Debit",
                    vendor_key="Description",
                    credit_key="Credit",
                )
        elif "citi" in file_path.lower():
            print(f"Processing Citi file: {file_path}")
            card_name = "citi_custom" if "custom" in os.path.basename(file_path).lower() else "citi_double"
            df, mis_trans = read_csv_file(file_path=file_path, sep='\t\t')
            if not df.empty:
                df.columns = [col.strip() for col in df.columns]                    
                for col in df.columns:
                    if df[col].dtype == 'object':
                        df[col] = df[col].str.strip()
            trans = parse(
                    df=df, 
                    card_name=card_name,
                    date_key="Date",
                    date_conversion="%m/%d/%Y",
                    debit_key="Amount",
                    vendor_key="Description",
                )
        elif "wellsfargo" in file_path.lower() or "bilt" in file_path.lower():
            print(f"Processing Wells Fargo/Bilt file: {file_path}")
            card_name = "wells_fargo" if "wellsfargo" in os.path.basename(file_path).lower() else "bilt"
            df, mis_trans = read_csv_file(file_path=file_path, sep=",")
            trans = parse(
                    df=df, 
                    card_name=card_name,
                    date_key="Date",
                    debit_key="Amount",
                    vendor_key="Description",
                )
        else:
            print(f"Skipping unrecognized file: {file_path}")
            continue
                
        if trans or mis_trans:
            if mis_trans:
                print(f"Found {len(mis_trans)} misformatted transactions")
                misformatted_transactions.extend(mis_trans)
            
            if trans:
                transaction_tuples = []
                
                for transaction in trans:
                    transaction_tuple = (
                        transaction.id,
                        transaction.card_issuer,
                        transaction.date,
                        transaction.month,
                        transaction.day,
                        transaction.year,
                        transaction.amount,
                        transaction.vendor,
                        transaction.category,
                        transaction.line_id
                    )
                    transaction_tuples.append(transaction_tuple)
                
                try:
                    if transaction_tuples:
                        print(f"Attempting to insert {len(transaction_tuples)} transactions")
                        # First, try a batch INSERT with ON CONFLICT DO NOTHING
                        try:
                            execute_batch(cur, """
                                INSERT INTO transactions 
                                (id, card_issuer, date, month, day, year, amount, vendor, category, line_id)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT DO NOTHING
                            """, transaction_tuples)
                            conn.commit()
                            print(f"Successfully inserted transactions in batch")
                        except psycopg2.errors.UniqueViolation:
                            # If we get here, we have duplicates. Handle them one by one.
                            conn.rollback()  # Roll back the failed batch operation
                            print(f"Batch insert failed, processing transactions individually")
                            
                            # Process each transaction individually with ON CONFLICT DO NOTHING
                            successful = 0
                            for tup in transaction_tuples:
                                try:
                                    cur.execute("""
                                        INSERT INTO transactions 
                                        (id, card_issuer, date, month, day, year, amount, vendor, category, line_id)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                        ON CONFLICT DO NOTHING
                                    """, tup)
                                    conn.commit()
                                    successful += 1
                                except Exception as e:
                                    # Skip this duplicate
                                    conn.rollback()
                                    print(f"Error inserting transaction: {str(e)}")
                                    continue
                            print(f"Individually inserted {successful} out of {len(transaction_tuples)} transactions")
                                    
                except Exception as e:
                    # Log the error but continue
                    print(f"Error inserting transactions: {str(e)}")
                    conn.rollback()
    
    # Insert misformatted transactions into the database
    if misformatted_transactions:
        # Convert to a format that can be stored in PostgreSQL
        print(f"Inserting {len(misformatted_transactions)} misformatted transactions")
        for i, mis in enumerate(misformatted_transactions):
            cur.execute("""
                INSERT INTO misformatted_transactions (id, data)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (i, json.dumps(mis)))
    
    # Commit changes and close connection
    conn.commit()
    cur.close()
    conn.close()
    print("\nTransaction processing completed.")

# Improved CSV file reading function
def read_csv_file(file_path, sep=','):
    print(f"Reading file: {file_path} with separator: '{sep}'")
    try:
        # First try to use pandas directly
        try:
            if "citi" not in file_path.split("/")[-1]:
                df = pd.read_csv(file_path, sep=None, engine='python')
                print(f"Auto-detected CSV format. DataFrame shape: {df.shape}")
                return df, []
            else:
                raise Exception
        except Exception as e:
            print(f"Auto-detection failed: {str(e)}. Trying with specified separator.")
            
            # Read file contents
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            print(f"File read successfully. Total lines: {len(lines)}")
            
            if len(lines) == 0:
                print("Warning: Empty file")
                return pd.DataFrame(), []
                
            if sep == "\t\t":
                print("Using tab separator for parsing")
                try:
                    df = pd.read_csv(file_path, sep='\t\t', engine='python')
                    print(f"DataFrame created with shape: {df.shape}")
                    return df, []
                except Exception as e:
                    try:
                        df = pd.read_csv(file_path, sep=r'\s{2,}', engine='python')
                        print(f"DataFrame created with shape: {df.shape}")
                        return df, []
                    except Exception as e:
                        print(f"Error reading CSV with tabs: {str(e)}")
                        return pd.DataFrame(), []
            else:
                try:
                    # Try to determine the separator by checking first line
                    if sep == ',':
                        potential_seps = [',', ';', '\t', '|']
                        counts = {s: lines[0].count(s) for s in potential_seps}
                        most_common = max(counts, key=counts.get)
                        
                        if counts[most_common] > counts[sep] and counts[most_common] > 0:
                            print(f"Detected possible alternate separator: '{most_common}' (count: {counts[most_common]})")
                            print(f"Original separator count: '{sep}' (count: {counts[sep]})")
                            
                            # Try with the detected separator
                            try:
                                df = pd.read_csv(file_path, sep=most_common)
                                if len(df.columns) > 1:
                                    print(f"Successfully parsed with detected separator. Shape: {df.shape}")
                                    return df, []
                            except:
                                print("Failed with detected separator, continuing with original.")
                    
                    header = lines[0].strip().split(sep)
                    print(f"Header found: {header}")

                    # Get all rows and reverse them (newest first)
                    all_rows = [line.strip().split(sep) for line in lines[1:]]
                    print(f"Total rows (excluding header): {len(all_rows)}")
                    all_rows.reverse()  # Newest transactions first
                    
                    regular_rows = []
                    irregular_rows = []

                    for row in all_rows:
                        if len(row) == len(header):
                            regular_rows.append(row)
                        else:
                            print(f"Found irregular row: {row} (expected {len(header)} columns, got {len(row)})")
                            irregular_rows.append(row)

                    print(f"Regular rows: {len(regular_rows)}, Irregular rows: {len(irregular_rows)}")
                    if not regular_rows:
                        print("Warning: No regular rows found")
                        return pd.DataFrame(), irregular_rows
                        
                    regular_df = pd.DataFrame(regular_rows, columns=header)
                    print(f"Created DataFrame with shape: {regular_df.shape}")
                    
                    return regular_df, irregular_rows
                except Exception as e:
                    print(f"Error processing CSV: {str(e)}")
                    import traceback
                    print(traceback.format_exc())
                    return pd.DataFrame(), []
    except Exception as e:
        print(f"Error opening file: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return pd.DataFrame(), []
    
def parse(
        df: pd.DataFrame,
        card_name: str,
        date_key: str,
        date_conversion: str,
        debit_key: str,
        vendor_key: str,
        credit_key: str = "",
    ):
    print(f"Parsing DataFrame for {card_name}")
    print(f"Using keys - Date: '{date_key}', Debit: '{debit_key}', Vendor: '{vendor_key}', Credit: '{credit_key}'")
    
    if df.empty:
        print("Warning: Empty DataFrame, nothing to parse")
        return []
        
    # Check if the required columns exist
    required_columns = [date_key, vendor_key]
    if credit_key:
        required_columns.append(credit_key)
    else:
        required_columns.append(debit_key)
        
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"Error: Missing required columns: {missing_columns}")
        print(f"Available columns are: {df.columns.tolist()}")
        return []
    
    trans = []

    num_rows = len(df) - 1
    for index, row in df.iterrows():
        try:
            print(f"Processing row {index}")
            line_id = num_rows - index
            print(f"Line id {line_id}")
            try:
                date = datetime.strptime(row[date_key], date_conversion)
                print(f"Date parsed: {date}")
            except Exception as e:
                print(f"Error parsing date '{row[date_key]}' with format '{date_conversion}': {str(e)}")
                try:
                    date = row[date_key].to_pydatetime()
                    print(f"Fallback date parsing succeeded: {date}")
                except Exception as e2:
                    print(f"Fallback date parsing failed: {str(e2)}")
                    continue

            month = date.month
            day = date.day
            year = date.year
            
            if credit_key == "" or (debit_key in row and row[debit_key] != ''):
                try:
                    debit_value = str(row[debit_key]).replace('$', '').replace(' ', '')
                    print(f"Raw debit value: '{row[debit_key]}', Cleaned: '{debit_value}'")
                    cleaned_amount = float(debit_value)
                    
                    if cleaned_amount is not None and not math.isnan(cleaned_amount):
                        new_trans = transactions.TransactionData(
                                id=str(uuid.uuid4()),
                                card_issuer=card_name,
                                date=date, 
                                year=year,
                                month=month,
                                day=day,
                                amount=float(cleaned_amount),
                                vendor=string.capwords(row[vendor_key].replace("\t", " ")),
                                category="" ,
                                line_id=line_id
                            )
                        print(f"Created transaction: {new_trans.vendor}, ${new_trans.amount:.2f}")
                        trans.append(new_trans)
                    else:
                        print(f"Skipping row with NaN amount: {row[debit_key]}")
                except Exception as e:
                    print(f"Error parsing debit amount '{row[debit_key]}': {str(e)}")
                    continue
            elif credit_key != "" and credit_key in row and row[credit_key] is not None:
                try:
                    credit_value = str(row[credit_key]).replace('$', '').replace(' ', '')
                    print(f"Raw credit value: '{row[credit_key]}', Cleaned: '{credit_value}'")
                    cleaned_amount = float(credit_value)
                    
                    new_trans = transactions.TransactionData(
                        id=str(uuid.uuid4()),
                        card_issuer=card_name,
                        date=date, 
                        year=year,
                        month=month,
                        day=day,
                        amount=float(cleaned_amount) * -1,
                        vendor=string.capwords(row[vendor_key].replace("\t", " ")),
                        category="" ,
                        line_id=index
                    )
                    print(f"Created credit transaction: {new_trans.vendor}, ${new_trans.amount:.2f}")
                    trans.append(new_trans)
                except Exception as e:
                    print(f"Error parsing credit amount '{row[credit_key]}': {str(e)}")
                    continue
            else:
                print(f"Skipping row - no valid amount found: {row.to_dict()}")
        except Exception as e:
            print(f"Error processing row {index}: {str(e)}")
            import traceback
            print(traceback.format_exc())
    
    print(f"Finished parsing. Created {len(trans)} transactions.")
    return trans

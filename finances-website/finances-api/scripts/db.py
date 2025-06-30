import os
import psycopg2
from fastapi import HTTPException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "finances")
DB_USER = os.getenv("POSTGRES_USER", "finances")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

def get_db_connection():
    """Dependency function to get database connection"""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        # Make the connection a dependency
        try:
            yield conn
        finally:
            conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")
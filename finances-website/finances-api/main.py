import time
from uuid import uuid4
import os

from fastapi import FastAPI, Request, status, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Import database module
from scripts.db import get_db_connection
import psycopg2
from dotenv import load_dotenv

from routers import (
    budget,
    categories,
    money_schedule,
    money_transfers,
    net_worth,
    income,
    rent,
    retirement,
    spending,
    transactions
)

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Finance API",
    description="Personal Finance Tracking API",
    version="1.0.0",
    debug=True
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(budget.router, tags=["Budget"])
app.include_router(categories.router, tags=["Categories"])
app.include_router(money_schedule.router, tags=["Money Schedule"])
app.include_router(money_transfers.router, tags=["Money Transfers"])
app.include_router(net_worth.router, tags=["Net Worth"])
app.include_router(income.router, tags=["Income"])
app.include_router(rent.router, tags=["Rent"])
app.include_router(retirement.router, tags=["Retirement"])
app.include_router(spending.router, tags=["Spending"])
app.include_router(transactions.router, tags=["Transactions"])

@app.middleware("http")
async def log_requests(request: Request, call_next):
    rid = uuid4()
    start_time = time.time()

    response = await call_next(request)

    process_time = int((time.time() - start_time) * 1000)
    
    # Enhanced logging
    print(f"Request {rid}: {request.method} {request.url.path} - {response.status_code} - {process_time}ms")

    return response

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log info which describes why an entity was unprocessable in the case of error."""

    exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
    content = {"status_code": 10422, "message": exc_str, "data": None}
    return JSONResponse(
        content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    print(f"Unhandled exception: {str(exc)}")
    content = {"status_code": 500, "message": "Internal server error", "data": None}
    return JSONResponse(
        content=content, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

# Add health check endpoint
@app.get("/health", tags=["Health"])
async def health_check(conn = Depends(get_db_connection)):
    """Health check endpoint to verify API and database are working"""
    try:
        # Test database connection
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
            db_status = "connected" if result and result[0] == 1 else "error"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "database": db_status,
        "timestamp": time.time()
    }

# Add database initialization on startup
@app.on_event("startup")
async def startup_db_client():
    """Initialize database tables if they don't exist"""
    try:
        # Database connection parameters
        DB_HOST = os.getenv("DB_HOST", "localhost")
        DB_PORT = os.getenv("DB_PORT", "5432")
        DB_NAME = os.getenv("POSTGRES_DB", "finances")
        DB_USER = os.getenv("POSTGRES_USER", "finances")
        DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
        
        # Connect to database
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.autocommit = True
        
        # Create tables if they don't exist
        with conn.cursor() as cur:
            # Transactions table
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
            )
            """)
            
            # Uncategorized transactions table
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
            )
            """)
            
            # Misformatted transactions table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS misformatted_transactions (
                id INTEGER PRIMARY KEY,
                data JSONB
            )
            """)
            
            # Categories table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                name TEXT PRIMARY KEY,
                rank INTEGER
            )
            """)
            
            # Budget table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS budget (
                category TEXT PRIMARY KEY,
                amount NUMERIC(10,2)
            )
            """)
            
            # Income table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS income (
                year INTEGER,
                month TEXT,
                amount NUMERIC(10,2),
                PRIMARY KEY (year, month)
            )
            """)
            
            # Rent table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS rent (
                year INTEGER,
                month TEXT,
                amount NUMERIC(10,2),
                PRIMARY KEY (year, month)
            )
            """)
            
            # Money transfers table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS money_transfers (
                id TEXT PRIMARY KEY,
                date DATE,
                year TEXT,
                month INTEGER,
                amount NUMERIC(10,2),
                type TEXT,
                description TEXT
            )
            """)
            
            # Net worth table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS net_worth (
                year TEXT,
                month TEXT,
                savings NUMERIC(10,2),
                investments NUMERIC(10,2),
                PRIMARY KEY (year, month)
            )
            """)
            
            # Transaction processing state table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS transaction_processing_state (
                card_name TEXT PRIMARY KEY,
                last_line INTEGER
            )
            """)
            
        # Close connection
        conn.close()
        
        print("Database tables initialized successfully")
        
    except Exception as e:
        print(f"Error initializing database: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
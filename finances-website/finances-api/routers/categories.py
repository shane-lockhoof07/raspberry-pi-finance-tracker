from fastapi import APIRouter, Depends
import psycopg2
from psycopg2.extras import RealDictCursor
from scripts.db import get_db_connection

router = APIRouter()

@router.get("/categories")
async def get_categories(conn = Depends(get_db_connection)):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT name, rank FROM categories")
        categories = {row['name']: row['rank'] for row in cur.fetchall()}
        return categories

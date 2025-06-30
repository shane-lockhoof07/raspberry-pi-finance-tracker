from fastapi import APIRouter, Depends
import json
from psycopg2.extras import RealDictCursor
from scripts.db import get_db_connection
from datetime import datetime
from dateutil.relativedelta import relativedelta


router = APIRouter()

@router.get("/networth")
def get_net_worth(conn = Depends(get_db_connection)):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT year, month, savings, investments 
            FROM net_worth 
            ORDER BY year, array_position(
                ARRAY['January', 'February', 'March', 'April', 'May', 'June', 'July', 
                    'August', 'September', 'October', 'November', 'December'], 
                month
            )
        """)
        
        net_worth_data = cur.fetchall()
        
        output = {}
        for item in net_worth_data:
            year = item['year']
            month = item['month']
            
            if year not in output:
                output[year] = []
            
            output[year].append({
                "month": month,
                "savings": round(float(item['savings']), 0),
                "investments": round(float(item['investments']), 0)
            })
        
        return output

@router.post("/networth")
def add_net_worth(data: dict, conn = Depends(get_db_connection)):
    try:
        year = data["year"]
        month = data["month"]
        type_key = data["type"].lower()
        amount = float(data["amount"])
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM net_worth WHERE year = %s AND month = %s", (year, month))
            existing = cur.fetchone()
            
            if existing:
                if type_key == "savings":
                    cur.execute("""
                        UPDATE net_worth 
                        SET savings = savings + %s
                        WHERE year = %s AND month = %s
                    """, (amount, year, month))
                elif type_key == "investments":
                    cur.execute("""
                        UPDATE net_worth 
                        SET investments = investments + %s
                        WHERE year = %s AND month = %s
                    """, (amount, year, month))
                else:
                    return {"error": f"Invalid type: {type_key}. Must be 'savings' or 'investments'."}
            else:
                if type_key == "savings":
                    cur.execute("""
                        INSERT INTO net_worth (year, month, savings, investments)
                        VALUES (%s, %s, %s, 0)
                    """, (year, month, amount))
                elif type_key == "investments":
                    cur.execute("""
                        INSERT INTO net_worth (year, month, savings, investments)
                        VALUES (%s, %s, 0, %s)
                    """, (year, month, amount))
                else:
                    return {"error": f"Invalid type: {type_key}. Must be 'savings' or 'investments'."}
            
            conn.commit()
            
            return get_net_worth(conn)
            
    except Exception as e:
        return {"error": str(e)}


@router.get("/networth/stockvesting")
def get_net_worth_stock_vesting(conn = Depends(get_db_connection)):
    today = datetime.now().strftime("%Y-%m-%d")
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT * 
            FROM stock_vesting_schedule 
            ORDER BY vesting_date DESC
        """)
        
        stocks_vesting = cur.fetchall()
        
        cur.execute("""
            SELECT SUM(shares) as vested_shares
            FROM stock_vesting_schedule
            WHERE vesting_date <= %s
        """, (today,))
        
        vested_result = cur.fetchone()
        total_vested_shares = vested_result['vested_shares'] if vested_result and vested_result['vested_shares'] else 0
        
        schedule_output = {}
        for item in stocks_vesting:
            date = item['vesting_date']
            
            if date not in schedule_output:
                schedule_output[date] = item['shares']
            else:
                schedule_output[date] += item['shares']
        
        return {
            "vesting_schedule": schedule_output,
            "total_vested_shares": total_vested_shares
        }


@router.post("/networth/stockvesting")
def add_net_worth_stock_vesting(data: dict, conn = Depends(get_db_connection)):
    try:
        
        start_date = data["start"]
        end_date = data["end"]
        schedule = data["schedule"].lower()
        cliff_months = int(data["cliff"])
        total_shares = int(data["shares"])
        
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            print(f"Parsed dates: start={start}, end={end}")
        except ValueError as e:
            print(f"Date parsing error: {str(e)}")
            return {"error": f"Invalid date format. Expected YYYY-MM-DD. Error: {str(e)}"}
        
        frequency_map = {
            "monthly": 1,
            "quarterly": 3,
            "semi-annually": 6,
            "annually": 12
        }
        
        if schedule not in frequency_map:
            print(f"Invalid schedule: {schedule}")
            return {"error": f"Invalid schedule: {schedule}. Must be one of {list(frequency_map.keys())}"}
            
        frequency_months = frequency_map[schedule]
        vesting_entries = []
        
        total_duration_months = ((end.year - start.year) * 12) + (end.month - start.month)
        if end.day >= start.day:
            total_duration_months += 1
        
        
        cliff_date = start + relativedelta(months=cliff_months)
                
        if cliff_months > 0:
            cliff_percentage = cliff_months / total_duration_months
            rounded_percentage = round(cliff_percentage * 20) / 20  # Rounds to nearest 0.05 (5%)
            cliff_shares = int(total_shares * rounded_percentage)
            
            print(f"Cliff percentage: {cliff_percentage:.2%}, rounded to {rounded_percentage:.2%}")
            print(f"Cliff shares: {cliff_shares}")
            
            remaining_shares = total_shares - cliff_shares
            
            periods_after_cliff = (total_duration_months - cliff_months) // frequency_months
            
            shares_per_period = remaining_shares // periods_after_cliff
            
            vesting_entries.append((cliff_date.strftime("%Y-%m-%d"), cliff_shares))
            
            current_date = cliff_date
            for i in range(periods_after_cliff):
                current_date = current_date + relativedelta(months=frequency_months)
                
                if current_date > end:
                    current_date = end
                
                if i == periods_after_cliff - 1:
                    remaining_count = remaining_shares - (shares_per_period * periods_after_cliff)
                    shares_to_add = shares_per_period + remaining_count
                else:
                    shares_to_add = shares_per_period
                
                vesting_entries.append((current_date.strftime("%Y-%m-%d"), shares_to_add))
                
                if current_date >= end:
                    break
        else:
            periods = total_duration_months // frequency_months
            shares_per_period = total_shares // periods
            remaining_count = total_shares - (shares_per_period * periods)
            
            current_date = start
            for i in range(periods):
                current_date = current_date + relativedelta(months=frequency_months)
                
                if current_date > end:
                    current_date = end
                
                if i == periods - 1:
                    shares_to_add = shares_per_period + remaining_count
                else:
                    shares_to_add = shares_per_period
                
                vesting_entries.append((current_date.strftime("%Y-%m-%d"), shares_to_add))
                
                if current_date >= end:
                    break
        
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'stock_vesting_schedule'
                );
            """)
            table_exists = cur.fetchone()['exists']
            
            if not table_exists:
                print("stock_vesting_schedule table does not exist!")
                return {"error": "The stock_vesting_schedule table does not exist in the database."}
            
            for date, shares in vesting_entries:
                cur.execute("""
                    INSERT INTO stock_vesting_schedule (vesting_date, shares)
                    VALUES (%s, %s) RETURNING id
                """, (date, shares))
                inserted_id = cur.fetchone()['id']
            
            conn.commit()
            print("All entries inserted and committed successfully")
            
            return get_net_worth_stock_vesting(conn)
            
    except Exception as e:
        print(f"Error in add_net_worth_stock_vesting: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
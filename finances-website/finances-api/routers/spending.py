from fastapi import APIRouter, Depends
import psycopg2
from psycopg2.extras import RealDictCursor
import calendar
from datetime import datetime
from scripts.db import get_db_connection

router = APIRouter()

@router.get("/spending/thismonth")
def get_spending_this_month(conn = Depends(get_db_connection)):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT c.name, b.amount as budget_amount
            FROM categories c
            LEFT JOIN budget b ON c.name = b.category
            WHERE c.name NOT IN ('payments', 'housing')
            ORDER BY c.rank
        """)
        
        categories = cur.fetchall()
        output = {}
        
        net = 0
        for cat in categories:
            output[cat['name']] = [0, cat['budget_amount'] or 0]
            net += float(cat['budget_amount'])

        
        this_month = datetime.now().month
        this_year = str(datetime.now().year)
        
        cur.execute("""
            SELECT category, amount
            FROM transactions
            WHERE month = %s AND year = %s AND category NOT IN ('payments', 'housing') AND category != '' AND category IS NOT NULL
        """, (this_month, this_year))
        
        transactions = cur.fetchall()
        
        for trans in transactions:
            category = trans['category']
            amount = float(trans['amount'])
            
            if category in output:
                output[category][0] += amount
        
        month_name = calendar.month_name[this_month]
        cur.execute("""
            SELECT amount FROM rent
            WHERE year = %s AND month = %s
        """, (this_year, month_name))
        
        rent_row = cur.fetchone()
        rent_amount = float(rent_row['amount']) if rent_row else 0
        
        for key in output:
            output[key][0] = round(output[key][0], 0)
        
        for category in output:
            net -= output[category][0]
                
        return {"spending": output, "net": round(net, 0)}

@router.get("/spending/lastmonth")
def get_spending_last_month(conn = Depends(get_db_connection)):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT c.name, b.amount as budget_amount
            FROM categories c
            LEFT JOIN budget b ON c.name = b.category
            WHERE c.name NOT IN ('payments', 'housing')
            ORDER BY c.rank
        """)
        
        categories = cur.fetchall()
        output = {}
        
        net = 0
        for cat in categories:
            output[cat['name']] = [0, cat['budget_amount'] or 0]
            net += float(cat['budget_amount'])
        
        current_month = datetime.now().month
        last_month = current_month - 1 if current_month > 1 else 12
        this_year = str(datetime.now().year)
        
        if last_month == 12:
            this_year = str(int(this_year) - 1)
        
        cur.execute("""
            SELECT category, amount
            FROM transactions
            WHERE month = %s AND year = %s AND category NOT IN ('payments', 'housing') AND category != '' AND category IS NOT NULL
        """, (last_month, this_year))
        
        transactions = cur.fetchall()
        
        for trans in transactions:
            category = trans['category']
            amount = float(trans['amount'])
            
            if category in output:
                output[category][0] += amount
        
        month_name = calendar.month_name[last_month]
        cur.execute("""
            SELECT amount FROM rent
            WHERE year = %s AND month = %s
        """, (this_year, month_name))
        
        rent_row = cur.fetchone()
        rent_amount = float(rent_row['amount']) if rent_row else 0
        
        for key in output:
            output[key][0] = round(output[key][0], 0)
                
        for category in output:
            net -= output[category][0]
                
        return {"spending": output, "net": round(net, 0)}
    

@router.get("/spending/specific/{month}/{year}")
def get_specific_month_spending(month: int, year: str, conn = Depends(get_db_connection)):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT c.name, b.amount as budget_amount
            FROM categories c
            LEFT JOIN budget b ON c.name = b.category
            WHERE c.name NOT IN ('payments', 'housing')
            ORDER BY c.rank
        """)
        
        categories = cur.fetchall()
        output = {}
        
        net = 0
        for cat in categories:
            output[cat['name']] = [0, cat['budget_amount'] or 0]
            net += float(cat['budget_amount'])
        
        # Convert month and year to the right types
        month_int = int(month)
        year_str = str(year)
        
        cur.execute("""
            SELECT category, amount
            FROM transactions
            WHERE month = %s AND year = %s AND category NOT IN ('payments', 'housing') 
            AND category != '' AND category IS NOT NULL
        """, (month_int, year_str))
        
        transactions = cur.fetchall()
        
        for trans in transactions:
            category = trans['category']
            amount = float(trans['amount'])
            
            if category in output:
                output[category][0] += amount
        
        month_name = calendar.month_name[month_int]
        cur.execute("""
            SELECT amount FROM rent
            WHERE year = %s AND month = %s
        """, (year_str, month_name))
        
        rent_row = cur.fetchone()
        rent_amount = float(rent_row['amount']) if rent_row else 0
        
        for key in output:
            output[key][0] = round(output[key][0], 0)
        
        # Get income value, defaults to 7513 if not found
        cur.execute("""
            SELECT amount FROM income
            WHERE year = %s AND month = %s
        """, (year_str, month_name))
        
        income_row = cur.fetchone()
        net = float(income_row['amount']) if income_row else 7513
        
        for category in output:
            net -= output[category][0]
                
        return {"spending": output, "net": round(net, 0)}
    

@router.get("/spending/yeartodate")
def get_spending_year_to_date(conn = Depends(get_db_connection)):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:

        year = int(datetime.now().year)
        statement = f"""
            SELECT year, month, category, amount
            FROM transactions
            WHERE category NOT IN ('payments', 'work') AND category != '' AND category IS NOT NULL
            AND year = '{year}'
            ORDER BY year, month
        """
        cur.execute(statement)
        
        transactions = cur.fetchall()

        cur.execute("""
            SELECT c.name, b.amount as budget_amount
            FROM categories c
            LEFT JOIN budget b ON c.name = b.category
            WHERE c.name NOT IN ('payments', 'housing')
            ORDER BY c.rank
        """)
        
        categories = cur.fetchall()
        output = {}
        
        net = 0
        for cat in categories:
            net += float(cat['budget_amount'])
                
        month_dict = {i: calendar.month_name[i] for i in range(1, 13)}
        output = {}
        base = {}
        count = {}
        avg_net = {}
        
        for month in month_dict.values():
            base[month] = [0, 0]
                
        for trans in transactions:
            comp_year = str(trans['year'])
            comp_month = month_dict[trans['month']]
            category = trans['category']
            amount = float(trans['amount'])
            
            if category != 'payments' and category != 'work':
                if comp_year not in output:
                    output[comp_year] = base.copy()
                    avg_net[comp_year] = 0
                    count[comp_year] = 0
                
                output[comp_year][comp_month][0] += amount
        
        current_month = datetime.now().month
        current_year = str(datetime.now().year)
        
        for year in output:
            for month in output[year]:
                if output[year][month][0] > 0:
                    month_number = list(calendar.month_name).index(month)
                    
                    
                    if not (current_month == month_number and current_year == year):
                        count[year] += 1
                        output[year][month][1] = round(net, 0)
                        avg_net[year] += (net - output[year][month][0])
                    
                    output[year][month][1] = round(net, 0)
                    output[year][month][0] = round(output[year][month][0], 0)
        
        for year in avg_net:
            if count[year] > 0:
                avg_net[year] = round(avg_net[year] / count[year], 0)
            else:
                avg_net[year] = 0
        
        return {"spending": output, "avg": avg_net}

@router.get("/spending/yeartodate/categorized")
def get_spending_categorized(conn = Depends(get_db_connection)):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT c.name, b.amount as budget
            FROM categories c
            LEFT JOIN budget b ON c.name = b.category
            WHERE c.name NOT IN ('payments', 'housing')
        """)
        
        categories = cur.fetchall()
        
        base = {}
        for cat in categories:
            base[cat['name']] = [0, cat['budget'] or 0]
        
        cur.execute("""
            SELECT year, extract(month from date) as month_num, to_char(date, 'Month') as month_name,
                   category, amount
            FROM transactions
            WHERE category NOT IN ('payments', 'housing') AND category != '' AND category IS NOT NULL
            ORDER BY year, month_num
        """)
        
        transactions = cur.fetchall()
        
        current_month = datetime.now().month
        current_year = str(datetime.now().year)
        current_month_name = calendar.month_name[current_month]
        
        output = {}
        months = {}
        
        for trans in transactions:
            year = str(trans['year'])
            month_name = trans['month_name'].strip()
            category = trans['category']
            amount = float(trans['amount'])
            
            if month_name == current_month_name and year == current_year:
                continue
                
            if year not in output:
                output[year] = base.copy()
                months[year] = set()
            
            months[year].add(month_name)
            
            if category in output[year]:
                output[year][category][0] += amount
        
        for year in output:
            for category in output[year]:
                if len(months[year]) > 0:
                    output[year][category][0] = output[year][category][0] / len(months[year])
                    output[year][category][0] = round(output[year][category][0], 0)
        
        return output

@router.get("/spending/yeartodate/realtivetoincome")
def get_spending_relative_to_income(conn = Depends(get_db_connection)):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT year, extract(month from date) as month_num, to_char(date, 'Month') as month_name,
                   category, amount
            FROM transactions
            WHERE category NOT IN ('payments', 'work') AND category != '' AND category IS NOT NULL
            ORDER BY year, month_num
        """)
        
        transactions = cur.fetchall()
        
        cur.execute("SELECT year, month, amount FROM income ORDER BY year, month")
        income_records = cur.fetchall()
        
        cur.execute("SELECT year, month, amount FROM rent ORDER BY year, month")
        rent_records = cur.fetchall()
        
        cur.execute("""
            SELECT year, extract(month from date) as month_num, to_char(date, 'Month') as month_name,
                   amount
            FROM money_transfers
            ORDER BY year, month_num
        """)
        
        transfers = cur.fetchall()
        
        investments = 1166
        
        month_dict = {i: calendar.month_name[i] for i in range(1, 13)}
        
        monthly = {}
        for month in month_dict.values():
            monthly[month] = {
                "month": month,
                "disposableIncome": 0,
                "extraIncome": 0,
                "investments": investments,
                "spending": 0,
                "moneyTransfers": 0,
                "rent": 0
            }
        
        output = {}
        net = {}
        count = {}
        
        current_year = datetime.now().year
        years = list(range(2025, current_year + 1))
        
        for year in years:
            year_str = str(year)
            output[year_str] = {m: monthly[m].copy() for m in monthly}
            net[year_str] = 0
            count[year_str] = 0
        
        for trans in transactions:
            year = str(trans['year'])
            month_name = trans['month_name'].strip()
            category = trans['category']
            amount = float(trans['amount'])
            
            if year in output and category != 'payments' and category != 'work':
                output[year][month_name]["spending"] += amount
        
        for transfer in transfers:
            year = str(transfer['year'])
            month_name = transfer['month_name'].strip()
            amount = float(transfer['amount'])
            
            if year in output:
                output[year][month_name]["moneyTransfers"] += amount
        
        for rent in rent_records:
            year = str(rent['year'])
            month_name = rent['month'].strip()
            amount = float(rent['amount'])
            
            if year in output:
                output[year][month_name]["rent"] = amount
        
        for income in income_records:
            year = str(income['year'])
            month_name = income['month'].strip()
            amount = float(income['amount'])
            if amount <= 5407.8:
                disposable_amt = amount
                extra_amt = 0
            else:
                flexible = (amount - 5407.8) * 0.48
                disposable_amt = 5407.8 + flexible
                extra_amt = amount - disposable_amt
            
            if year in output:
                output[year][month_name]["disposableIncome"] = round(disposable_amt, 2)
                output[year][month_name]["extraIncome"] = round(extra_amt, 2)
        
        current_month = datetime.now().month
        current_year = str(datetime.now().year)
        current_month_name = calendar.month_name[current_month]
        
        for year in output:
            for month in output[year]:
                if not (month == current_month_name and year == current_year):
                    month_net = (
                        output[year][month]["disposableIncome"] - 
                        output[year][month]["spending"] - 
                        output[year][month]["rent"] - 
                        output[year][month]["investments"] - 
                        output[year][month]["moneyTransfers"]
                    )
                    
                    if (output[year][month]["disposableIncome"] > 0 or 
                        output[year][month]["spending"] > 0 or 
                        output[year][month]["rent"] > 0):
                        net[year] += month_net
                        count[year] += 1
                
                output[year][month]["spending"] = round(output[year][month]["spending"], 0)
                output[year][month]["moneyTransfers"] = round(output[year][month]["moneyTransfers"], 0)
        
        avg_net = {}
        for year in net:
            if count[year] > 0:
                avg_net[year] = round(net[year] / count[year], 0)
            else:
                avg_net[year] = 0
        
        return {"data": output, "avg": avg_net}

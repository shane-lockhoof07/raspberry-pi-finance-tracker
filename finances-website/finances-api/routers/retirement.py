from fastapi import APIRouter, Depends
from scripts.db import get_db_connection
from typing import List, Dict, Any
from datetime import datetime

router = APIRouter()

assumptions_to_sum = [
    "Food (Monthly)",
    "Travel (International)",
    "Travel (Domestic)",
    "Hobbies",
    "Other Spending"
]
mortgage_rates = [2, 3, 4, 5, 6, 7]
term = 30*12
property_tax_rate = 0.018
home_ins = 2110/12
current_year = datetime.now().year
target_year = 2060
years_diff = target_year - current_year


def retirement_forecast(data: List[Dict[str, Any]]):
    inflation_rate = 0.025
    expenses = 0
    mortgage = 600000
    buffer = 0
    withdrawal_rate = 0.04
    current_value = 120000
    return_rate = 0.08/12
    for ele in data:
        if ele["assumption"] == "Inflation Rate (%)":
            inflation_rate = float(ele["value"]) / 100
        elif ele["assumption"] == "Mortgage":
            mortgage = int(ele["value"])
        elif ele["assumption"] == "Buffer (%)":
            buffer = float(ele["value"]) / 100
        elif ele["assumption"] == "Withdrawal Rate (%)":
            buffer = float(ele["value"]) / 100
        elif ele["assumption"] == "Rate of Return (%)":
            return_rate = float(ele["value"]) / 100 / 12
        elif ele["assumption"] == "Current Investments":
            current_value = float(ele["value"])
        elif ele["assumption"] in assumptions_to_sum:
            expenses += int(ele["value"])

    base_housing = property_tax_rate*mortgage/12 + home_ins
    expenses += base_housing
    expenses = expenses * (1 + buffer)
    fv = expenses * (1+inflation_rate)**years_diff
    pmt = (fv/withdrawal_rate - current_value * (1 + return_rate)**(years_diff*12)) / (((1 + return_rate)**(years_diff*12) - 1)/(return_rate)) + 0.005
    retirement = [
        {"row": "No Mortgage", "current_value": round(expenses, 0), "future_value": round(fv, 0), "nest_egg": round(fv/withdrawal_rate,0), "pmt": round(pmt, 0)}
    ]

    for rate in mortgage_rates:
        conv_rate = rate / 100 / 12
        payment = mortgage * (conv_rate*(1+conv_rate)**term) / ((1+conv_rate)**term - 1)
        pv = expenses + payment*12
        fv = pv * (1+inflation_rate)**years_diff
        pmt = (fv/withdrawal_rate - current_value * (1 + return_rate)**(years_diff*12)) / (((1 + return_rate)**(years_diff*12) - 1)/(return_rate)) + 0.005
        retirement.append({"row": f"{rate}% Mortgage", "current_value": round(pv, 0), "future_value": round(fv, 0), "nest_egg": round(fv/withdrawal_rate,0), "pmt": round(pmt, 0)})

    headers = [
        { "title": "Mortgage Rate", "key": "row", "align": "center" },
        { "title": "Annual Expenses in Today's Dollars", "key": "current_value", "align": "center" },
        { "title": "Annual Expenses in 2060's Dollars", "key": "future_value", "align": "center" },
        { "title": "Nest Egg Needed in 2060", "key": "nest_egg", "align": "center" },
        { "title": "Monthly Contribution for Nest Egg in 2060", "key": "pmt", "align": "center" }
    ]
    return {"headers": headers, "data": retirement}


def retirement_coast(data: List[Dict[str, Any]]):
    retirement_data = retirement_forecast(data)
    return_rate = 0.08/12
    current_year = datetime.now().year
    current_value = 120000
    headers = [
        { "title": "Mortgage Rate", "key": "row", "align": "center" },
    ]
    for ele in data:
        if ele["assumption"] == "Current Investments":
            current_value = float(ele["value"])
        elif ele["assumption"] == "Rate of Return (%)":
            return_rate = float(ele["value"]) / 100 / 12

    
    if return_rate <= 0:
        return_rate = 0.08/12
    data = []
    for row in retirement_data["data"]:
        if current_year % 5 == 0:
            year = current_year + 5
        else:
            year = current_year + current_year % 5
        new_row = {"row": row["row"]}
        while year <= 2060:
            print(year)
            year_diff = 2060 - year
            future_diff = (year - current_year) * 12
            print(future_diff)
            print((1 + return_rate)**future_diff)
            print(return_rate)
            pv = row["nest_egg"] / (1 + (return_rate*12))**year_diff
            pmt = (pv - current_value * (1 + return_rate)**future_diff) / (((1 + return_rate)**future_diff - 1)/(return_rate)) + 0.005
            print(f"Value: {pv}, payment: {pmt}")
            new_header = { "title": f"Coast Fire in {year}", "key": year, "align": "center" }
            if new_header not in headers:
                headers.append(
                    { "title": f"Coast Fire in {year}", "key": year, "align": "center" }
                )
            new_row[year] = {"text": f"${pmt:,.0f} -> ${pv:,.0f}", "pmt": round(pmt,2)}
            year += 5
        data.append(new_row)
    
    return {"headers": headers, "data": data}

    


@router.post("/retirement/forecast")
def get_retirment_forecast(data: List[Dict[str, Any]]):
    return retirement_forecast(data)

@router.post("/retirement/coast")
def get_retirment_coast(data: List[Dict[str, Any]]):    
    return retirement_coast(data)

#python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
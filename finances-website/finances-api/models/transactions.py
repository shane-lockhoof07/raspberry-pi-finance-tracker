from enum import Enum
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import json


class TransactionData:
    def __init__(
        self,
        id: str,
        card_issuer: str,
        date: datetime,
        month: int,
        day: int,
        amount: float,
        vendor: str,
        category: Optional[str] = None,
        line_id: Optional[int] = None,
        year: Optional[str] = None
    ):
        self.id = id
        self.card_issuer = card_issuer
        self.date = date
        self.month = month
        self.day = day
        self.amount = amount
        self.vendor = vendor
        self.category = category
        self.line_id = line_id
        self.year = year

    def __eq__(self, other):
        if not isinstance(other, TransactionData):
            print("Not both instances")
            return False  # Ensure we only compare with other TransactionData objects
        
        # Fields to include in the comparison (excluding 'category')
        fields_to_compare = {field for field in vars(self)}
        fields_to_compare.remove("id")
        fields_to_compare.remove("category")
        
        # Iterate through all fields to compare
        for field in fields_to_compare:
            self_value = getattr(self, field)
            other_value = getattr(other, field)
            
            # Special handling for 'date' field
            if field == "date":
                if isinstance(self_value, str):
                    self_value = datetime.fromisoformat(self_value.replace("T", " "))
                if isinstance(other_value, str):
                    other_value = datetime.fromisoformat(other_value.replace("T", " "))
            
            if self_value != other_value:
                print(f"Field '{field}' is not equal: {self_value} != {other_value}")
                return False
        
        return True

    def __repr__(self):
        return (
            f"TransactionData(id={self.id}, card_issuer={self.card_issuer}, "
            f"date={self.date}, month={self.month}, day={self.day}, "
            f"amount={self.amount}, vendor={self.vendor}, category={self.category}, "
            f"line_id={self.line_id})"
        )
    

class TransactionEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, TransactionData):
            # Convert TransactionData to a dictionary
            return {
                'id': obj.id,
                'card_issuer': obj.card_issuer,
                'date': obj.date.isoformat(),  # Convert datetime to string
                'month': obj.month,
                'day': obj.day,
                'amount': obj.amount,
                'vendor': obj.vendor,
                'category': obj.category,
                'line_id': obj.line_id,
                'year': obj.year
            }
        elif isinstance(obj, datetime):
            # Handle any stray datetime objects
            return obj.isoformat()
        return super().default(obj)
    

class TransactionDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)
    
    def object_hook(self, obj):
        if 'id' in obj and 'date' in obj and 'amount' in obj:
            try:
                year = obj['year']
            except:
                year = str(datetime.fromisoformat(obj['date']).year)
            return TransactionData(
                id=obj['id'],
                card_issuer=obj['card_issuer'],
                date=datetime.fromisoformat(obj['date']),
                month=obj['month'],
                day=obj['day'],
                amount=obj['amount'],
                vendor=obj['vendor'],
                category=obj['category'],
                line_id=obj['line_id'],
                year=year
            )
        return obj
    

class TransactionList:
    def __init__(self, transactions: list[TransactionData], misformatted_transactions: list = []):
        self.transactions = transactions
        self.misformatted_transactions = misformatted_transactions

from enum import Enum
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import json


class MoneyTransfer:
    def __init__(
        self,
        id: str,
        date: datetime,
        year: str,
        month: int,
        amount: float,
        type: str,
        description: Optional[str]
    ):
        self.id = id
        self.date = date
        self.year = year
        self.month = month
        self.amount = amount
        self.type = type
        self.description = description


class MoneyTransferEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, MoneyTransfer):
            return {
                'id': obj.id,
                'date': obj.date.isoformat(),  # Convert datetime to string
                'year': obj.year,
                'month': obj.month,
                'amount': obj.amount,
                'type': obj.type,
                'description': obj.description,
            }
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)
    

class MoneyTransferDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)
    
    def object_hook(self, obj):
        if 'id' in obj and 'date' in obj and 'amount' in obj:
            return MoneyTransfer(
                id=obj['id'],
                date=datetime.fromisoformat(obj['date']),
                year=obj['year'],
                month=obj['month'],
                amount=obj['amount'],
                type=obj['type'],
                description=obj.get('description')
            )
        return obj

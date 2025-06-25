from pydantic import BaseModel, Field, validator
from typing import Optional, Union
from datetime import datetime
from enum import Enum

class ExpenseCategory(str, Enum):
    FOOD = "food"
    TRANSPORT = "transport"
    SHOPPING = "shopping"
    ENTERTAINMENT = "entertainment"
    BILLS = "bills"
    HEALTHCARE = "healthcare"
    OTHER = "other"

class ExpenseCreate(BaseModel):
    amount: float = Field(..., gt=0, description="Amount must be positive")
    description: str = Field(..., min_length=1, max_length=255)
    category: ExpenseCategory
    date: Union[datetime, str]  # Accept both datetime and string
    receipt_image_url: Optional[str] = None

    @validator('date', pre=True)
    def parse_date(cls, v):
        if isinstance(v, str):
            # Handle different date formats
            try:
                # Try parsing date-only format first
                if len(v) == 10:  # YYYY-MM-DD
                    return datetime.strptime(v, "%Y-%m-%d")
                else:
                    # Try parsing full datetime
                    return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError('Invalid date format. Use YYYY-MM-DD or ISO datetime format')
        return v

class ExpenseUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    description: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[ExpenseCategory] = None
    date: Optional[Union[datetime, str]] = None
    receipt_image_url: Optional[str] = None

    @validator('date', pre=True)
    def parse_date(cls, v):
        if isinstance(v, str) and v:
            try:
                if len(v) == 10:  # YYYY-MM-DD
                    return datetime.strptime(v, "%Y-%m-%d")
                else:
                    return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError('Invalid date format. Use YYYY-MM-DD or ISO datetime format')
        return v

class ExpenseResponse(BaseModel):
    id: str
    user_id: str
    amount: float
    description: str
    category: ExpenseCategory
    date: datetime
    receipt_image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class ExpenseFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    category: Optional[ExpenseCategory] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None

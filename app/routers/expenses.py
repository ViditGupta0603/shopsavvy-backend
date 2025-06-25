from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.dependencies import get_current_user
from app.models.expense import ExpenseCreate
from typing import List, Optional, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/expenses", tags=["expenses"])

# In-memory expense storage (for testing)
expenses_db = []

@router.post("/")
async def create_expense(
    expense: ExpenseCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new expense"""
    try:
        # Create expense with auto-generated ID
        expense_id = f"exp_{len(expenses_db) + 1}"
        expense_data = {
            "id": expense_id,
            "user_id": current_user["id"],
            "amount": expense.amount,
            "description": expense.description,
            "category": expense.category.value,
            "date": expense.date.isoformat() if hasattr(expense.date, 'isoformat') else str(expense.date),
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Store expense
        expenses_db.append(expense_data)
        
        return {
            "success": True,
            "id": expense_id,
            "message": "Expense created successfully!",
            "expense": expense_data
        }
    except Exception as e:
        logger.error(f"Error creating expense: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create expense: {str(e)}")

@router.get("/")
async def get_expenses(current_user: dict = Depends(get_current_user)):
    """Get user expenses"""
    user_expenses = [exp for exp in expenses_db if exp["user_id"] == current_user["id"]]
    return {
        "expenses": user_expenses,
        "count": len(user_expenses)
    }

@router.get("/test")
async def test_expenses():
    """Test endpoint"""
    return {"message": "Expenses router is working!", "total_expenses": len(expenses_db)}

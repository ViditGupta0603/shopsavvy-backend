from fastapi import APIRouter, Depends, Query
from app.core.dependencies import get_current_user
from app.services.firebase_service import firebase_service
from typing import Optional
from datetime import datetime, timedelta

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/monthly")
async def get_monthly_analytics(
    year: Optional[int] = Query(None, description="Year for analytics"),
    current_user: dict = Depends(get_current_user)
):
    """Get monthly expense analytics"""
    if not year:
        year = datetime.now().year
    
    # Get expenses for the year
    expenses = firebase_service.get_expenses(current_user["uid"])
    
    # Process monthly data
    monthly_data = {}
    total_amount = 0
    
    for expense in expenses:
        expense_date = expense.get("date", "")
        if expense_date.startswith(str(year)):
            month = expense_date[:7]  # YYYY-MM format
            amount = expense.get("amount", 0)
            
            if month not in monthly_data:
                monthly_data[month] = {"total": 0, "count": 0}
            monthly_data[month]["total"] += amount
            monthly_data[month]["count"] += 1
            total_amount += amount
    
    return {
        "year": year,
        "monthly_data": monthly_data,
        "total_expenses": total_amount,
        "total_transactions": sum(data["count"] for data in monthly_data.values())
    }

@router.get("/categories")
async def get_category_analytics(
    days: Optional[int] = Query(30, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user)
):
    """Get expense breakdown by categories"""
    expenses = firebase_service.get_expenses(current_user["uid"])
    
    # Process category data
    category_data = {}
    for expense in expenses:
        category = expense.get("category", "other")
        amount = expense.get("amount", 0)
        
        if category not in category_data:
            category_data[category] = {"total": 0, "count": 0}
        category_data[category]["total"] += amount
        category_data[category]["count"] += 1
    
    return {
        "period_days": days,
        "category_breakdown": category_data,
        "total_categories": len(category_data)
    }

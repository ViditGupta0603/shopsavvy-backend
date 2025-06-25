from app.database.mongodb import get_database
from bson import ObjectId
from datetime import datetime
from typing import List, Dict

class ExpenseService:
    def __init__(self):
        self.db = get_database()
        self.collection = "expenses"
    
    async def create_expense(self, user_id: str, expense_data: Dict) -> str:
        expense_doc = {
            **expense_data,
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await self.db[self.collection].insert_one(expense_doc)
        return str(result.inserted_id)
    
    async def get_expenses(self, user_id: str, filters: Dict = None) -> List[Dict]:
        query = {"user_id": user_id}
        
        if filters:
            if filters.get("category"):
                query["category"] = filters["category"]
            # Add more filters as needed
        
        cursor = self.db[self.collection].find(query)
        expenses = []
        async for expense in cursor:
            expense["id"] = str(expense["_id"])
            del expense["_id"]
            expenses.append(expense)
        
        return expenses

expense_service = ExpenseService()

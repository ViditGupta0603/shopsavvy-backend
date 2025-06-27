from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from api.core.dependencies import get_current_user
from api.services.ocr_service import ocr_service
from api.models.expense import ExpenseCreate, ExpenseCategory
from typing import Dict
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/receipts", tags=["Receipts"])

# In-memory storage for receipts (same as expenses)
from api.routers.expenses import expenses_db

@router.post("/parse")
async def parse_receipt(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Parse receipt image and extract expense data"""
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Parse receipt using OCR
        result = await ocr_service.parse_receipt(file)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "raw_text": result["raw_text"],
            "parsed_data": result["parsed_data"],
            "message": "Receipt parsed successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Receipt parsing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to parse receipt: {str(e)}")

@router.post("/parse-and-save")
async def parse_and_save_receipt(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Parse receipt image and automatically save as expense"""
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Parse receipt using OCR
        result = await ocr_service.parse_receipt(file)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        parsed_data = result["parsed_data"]
        
        # Check if we extracted enough data to create an expense
        if not parsed_data.get("amount"):
            return {
                "success": False,
                "message": "Could not extract amount from receipt",
                "raw_text": result["raw_text"],
                "parsed_data": parsed_data
            }
        
        # Create expense from parsed data
        expense_id = f"exp_{len(expenses_db) + 1}"
        expense_data = {
            "id": expense_id,
            "user_id": current_user["id"],
            "amount": parsed_data["amount"],
            "description": parsed_data.get("description", "Receipt expense"),
            "category": parsed_data.get("category", "other"),
            "date": parsed_data.get("date", datetime.now().strftime("%Y-%m-%d")),
            "merchant": parsed_data.get("merchant"),
            "items": parsed_data.get("items", []),
            "source": "receipt_ocr",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Store expense
        expenses_db.append(expense_data)
        
        return {
            "success": True,
            "expense_id": expense_id,
            "expense": expense_data,
            "raw_text": result["raw_text"],
            "parsed_data": parsed_data,
            "message": "Receipt parsed and expense created successfully!"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Receipt parsing and saving error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to parse and save receipt: {str(e)}")

@router.get("/test")
async def test_receipts():
    """Test receipts endpoint"""
    return {"message": "Receipts router is working!"}

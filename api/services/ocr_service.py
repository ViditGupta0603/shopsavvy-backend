import cv2
import numpy as np
import pytesseract
from typing import Dict, List, Optional
import re
import logging
from fastapi import UploadFile
import os

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self):
        # Configure Tesseract path for Windows
        import shutil
        if not shutil.which('tesseract'):
            possible_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break
    
    async def parse_receipt(self, file: UploadFile) -> Dict:
        """Extract text from receipt image and parse expense data"""
        try:
            # Read image safely
            image = await self._read_image_safely(file)
            
            if image is None:
                return {
                    "success": False,
                    "error": "Could not read image file",
                    "raw_text": "",
                    "parsed_data": {}
                }
            
            # Preprocess image for better OCR
            processed_image = self._preprocess_image(image)
            
            # Extract text using OCR
            raw_text = pytesseract.image_to_string(processed_image)
            logger.info(f"OCR extracted text: {raw_text}")
            
            # Parse expense data from text
            parsed_data = self._parse_expense_data(raw_text)
            
            return {
                "success": True,
                "raw_text": raw_text,
                "parsed_data": parsed_data
            }
        except Exception as e:
            logger.error(f"OCR parsing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "raw_text": "",
                "parsed_data": {}
            }
    
    async def _read_image_safely(self, file: UploadFile) -> Optional[np.ndarray]:
        """Safely read uploaded image file"""
        try:
            # Read file contents
            contents = await file.read()
            
            # Convert to numpy array
            nparr = np.frombuffer(contents, np.uint8)
            
            # Decode image
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None or image.size == 0:
                logger.error("Failed to decode image")
                return None
                
            return image
        except Exception as e:
            logger.error(f"Error reading image: {e}")
            return None
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Enhance image for better OCR results"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Apply threshold for better text recognition
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            return thresh
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            return image
    
    def _parse_expense_data(self, text: str) -> Dict:
        """Parse expense information from OCR text"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Extract total amount
        amount = self._extract_amount(text)
        
        # Extract date
        date = self._extract_date(text)
        
        # Extract merchant name
        merchant = self._extract_merchant(lines)
        
        # Extract items
        items = self._extract_items(lines)
        
        # Determine category based on merchant or items
        category = self._determine_category(merchant, items)
        
        return {
            "amount": amount,
            "date": date,
            "merchant": merchant,
            "items": items,
            "category": category,
            "description": f"Receipt from {merchant}" if merchant else "Receipt expense"
        }
    
    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract total amount from receipt text"""
        # Common patterns for total amounts
        patterns = [
            r'(?:total|amount|sum|grand total|subtotal)[:\s]*\$?(\d+\.?\d*)',
            r'total[:\s]*(\d+\.\d{2})',
            r'\$(\d+\.\d{2})',
            r'(\d+\.\d{2})\s*(?:total|$)',
            r'(\d+\.\d{2})'
        ]
        
        amounts = []
        text_lower = text.lower()
        
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                try:
                    amount = float(match)
                    if 0.01 <= amount <= 10000:  # Reasonable amount range
                        amounts.append(amount)
                except ValueError:
                    continue
        
        # Return the largest reasonable amount (likely the total)
        return max(amounts) if amounts else None
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date from receipt text"""
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
            r'(\d{1,2}\s+\w+\s+\d{4})',
            r'(\w+\s+\d{1,2},?\s+\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    def _extract_merchant(self, lines: List[str]) -> str:
        """Extract merchant name from receipt lines"""
        # Usually the merchant name is in the first few lines
        for line in lines[:5]:
            # Skip lines that are clearly not merchant names
            if re.match(r'^\d+[/-]\d+', line) or len(line) < 3:
                continue
            # Skip lines with only numbers or special characters
            if re.match(r'^[\d\s\-\.\$]+$', line):
                continue
            return line
        return "Unknown Merchant"
    
    def _extract_items(self, lines: List[str]) -> List[Dict]:
        """Extract individual items from receipt"""
        items = []
        for line in lines:
            # Look for lines with price patterns
            price_matches = re.findall(r'\$?(\d+\.\d{2})', line)
            if price_matches:
                # Remove price from line to get item name
                item_name = re.sub(r'\$?\d+\.\d{2}', '', line).strip()
                # Clean up item name
                item_name = re.sub(r'[^\w\s]', ' ', item_name).strip()
                
                if item_name and len(item_name) > 2:
                    items.append({
                        "name": item_name,
                        "price": float(price_matches[-1])  # Use last price found
                    })
        return items[:10]  # Limit to 10 items
    
    def _determine_category(self, merchant: str, items: List[Dict]) -> str:
        """Determine expense category based on merchant and items"""
        merchant_lower = merchant.lower() if merchant else ""
        
        # Food-related keywords
        food_keywords = ['restaurant', 'cafe', 'coffee', 'pizza', 'burger', 'food', 'dining', 'kitchen', 'bistro', 'grill']
        if any(keyword in merchant_lower for keyword in food_keywords):
            return "food"
        
        # Shopping keywords
        shopping_keywords = ['store', 'shop', 'market', 'mall', 'retail', 'walmart', 'target', 'amazon']
        if any(keyword in merchant_lower for keyword in shopping_keywords):
            return "shopping"
        
        # Transport keywords
        transport_keywords = ['gas', 'fuel', 'station', 'uber', 'taxi', 'bus', 'metro', 'parking']
        if any(keyword in merchant_lower for keyword in transport_keywords):
            return "transport"
        
        # Bills keywords
        bills_keywords = ['electric', 'water', 'internet', 'phone', 'utility', 'bill', 'payment']
        if any(keyword in merchant_lower for keyword in bills_keywords):
            return "bills"
        
        # Healthcare keywords
        health_keywords = ['pharmacy', 'hospital', 'clinic', 'medical', 'doctor', 'health']
        if any(keyword in merchant_lower for keyword in health_keywords):
            return "healthcare"
        
        return "other"

ocr_service = OCRService()

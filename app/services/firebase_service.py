import firebase_admin
from firebase_admin import credentials, firestore, auth
from app.core.config import settings
from typing import Dict, List, Optional
import logging
from datetime import datetime  # Add this line

logger = logging.getLogger(__name__)

class FirebaseService:
    def __init__(self):
        if not firebase_admin._apps:
            # Use Application Default Credentials instead of file path
            try:
                # Try to use Application Default Credentials first
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred)
            except Exception:
                # Fallback to certificate file if ADC not available
                cred = credentials.Certificate(settings.firebase_credentials_path)
                firebase_admin.initialize_app(cred)
        
        self.db = firestore.client()
    
    def verify_token(self, token: str) -> Dict:
        """Verify Firebase ID token and return user info"""
        try:
            decoded_token = auth.verify_id_token(token)
            return decoded_token
        except auth.InvalidIdTokenError as e:
            logger.error(f"Invalid ID token: {e}")
            raise ValueError("Invalid token")
        except auth.ExpiredIdTokenError as e:
            logger.error(f"Expired ID token: {e}")
            raise ValueError("Token expired")
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise ValueError("Token verification failed")
    
    def create_expense(self, user_id: str, expense_data: Dict) -> str:
        """Create new expense in Firestore"""
        try:
            logger.info(f"Creating expense for user {user_id}")
            doc_ref = self.db.collection('expenses').document()
            
            # Convert datetime objects to strings for Firestore
            if isinstance(expense_data.get('date'), datetime):
                expense_data['date'] = expense_data['date'].isoformat()
            
            expense_data['user_id'] = user_id
            expense_data['id'] = doc_ref.id
            expense_data['created_at'] = firestore.SERVER_TIMESTAMP
            expense_data['updated_at'] = firestore.SERVER_TIMESTAMP
            
            logger.info(f"Setting document with data")
            doc_ref.set(expense_data)
            logger.info(f"Created expense {doc_ref.id} for user {user_id}")
            
            # Return just the ID, not the data with Sentinel values
            return doc_ref.id
        except Exception as e:
            logger.error(f"Failed to create expense: {e}")
            raise Exception(f"Database error: {str(e)}")


    
    def get_expenses(self, user_id: str, filters: Dict = None) -> List[Dict]:
        """Get user expenses with optional filters"""
        try:
            query = self.db.collection('expenses').where('user_id', '==', user_id)
            
            if filters:
                if filters.get('category'):
                    query = query.where('category', '==', filters['category'])
                if filters.get('start_date'):
                    query = query.where('date', '>=', filters['start_date'])
                if filters.get('end_date'):
                    query = query.where('date', '<=', filters['end_date'])
            
            docs = query.stream()
            expenses = [doc.to_dict() for doc in docs]
            logger.info(f"Retrieved {len(expenses)} expenses for user {user_id}")
            return expenses
        except Exception as e:
            logger.error(f"Failed to get expenses: {e}")
            raise
    
    def update_expense(self, expense_id: str, user_id: str, update_data: Dict) -> bool:
        """Update expense if it belongs to the user"""
        try:
            doc_ref = self.db.collection('expenses').document(expense_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                logger.warning(f"Expense {expense_id} not found")
                return False
            
            expense_data = doc.to_dict()
            if expense_data.get('user_id') != user_id:
                logger.warning(f"User {user_id} attempted to update expense {expense_id} belonging to another user")
                return False
            
            doc_ref.update(update_data)
            logger.info(f"Updated expense {expense_id} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update expense: {e}")
            raise
    
    def delete_expense(self, expense_id: str, user_id: str) -> bool:
        """Delete expense if it belongs to the user"""
        try:
            doc_ref = self.db.collection('expenses').document(expense_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                logger.warning(f"Expense {expense_id} not found")
                return False
            
            expense_data = doc.to_dict()
            if expense_data.get('user_id') != user_id:
                logger.warning(f"User {user_id} attempted to delete expense {expense_id} belonging to another user")
                return False
            
            doc_ref.delete()
            logger.info(f"Deleted expense {expense_id} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete expense: {e}")
            raise

firebase_service = FirebaseService()

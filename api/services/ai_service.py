import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        pass
    
    def analyze_spending_trends(self, expenses: List[Dict]) -> Dict[str, Any]:
        """Analyze spending trends from expense data"""
        if not expenses:
            return {
                "trends": [],
                "insights": ["No expense data available for analysis"],
                "recommendations": []
            }
        
        try:
            # Convert to DataFrame for easier analysis
            df = pd.DataFrame(expenses)
            
            # Ensure amount column exists and is numeric
            if 'amount' not in df.columns:
                return {"error": "No amount data found in expenses"}
            
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
            df = df.dropna(subset=['amount'])
            
            # Analyze trends
            trends = self._calculate_trends(df)
            insights = self._generate_insights(df)
            recommendations = self._generate_trend_recommendations(df)
            
            return {
                "trends": trends,
                "insights": insights,
                "recommendations": recommendations,
                "total_analyzed": len(df)
            }
        
        except Exception as e:
            logger.error(f"Error analyzing spending trends: {e}")
            return {
                "error": str(e),
                "trends": [],
                "insights": [],
                "recommendations": []
            }
    
    def generate_recommendations(self, expenses: List[Dict]) -> Dict[str, Any]:
        """Generate AI-powered budget recommendations"""
        if not expenses:
            return {
                "recommendations": ["Start tracking your expenses to get personalized recommendations"],
                "budget_suggestions": {},
                "savings_opportunities": []
            }
        
        try:
            df = pd.DataFrame(expenses)
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
            df = df.dropna(subset=['amount'])
            
            # Calculate category-wise spending
            category_spending = df.groupby('category')['amount'].agg(['sum', 'mean', 'count']).to_dict('index')
            
            # Generate recommendations
            recommendations = self._generate_budget_recommendations(category_spending)
            budget_suggestions = self._suggest_budget_limits(category_spending)
            savings_opportunities = self._identify_savings_opportunities(df)
            
            return {
                "recommendations": recommendations,
                "budget_suggestions": budget_suggestions,
                "savings_opportunities": savings_opportunities,
                "analysis_period": "Last 90 days"
            }
        
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return {
                "error": str(e),
                "recommendations": [],
                "budget_suggestions": {},
                "savings_opportunities": []
            }
    
    def _calculate_trends(self, df: pd.DataFrame) -> List[Dict]:
        """Calculate spending trends"""
        trends = []
        
        # Monthly trend
        if 'date' in df.columns:
            df['month'] = pd.to_datetime(df['date'], errors='coerce').dt.to_period('M')
            monthly_spending = df.groupby('month')['amount'].sum()
            
            if len(monthly_spending) > 1:
                trend_direction = "increasing" if monthly_spending.iloc[-1] > monthly_spending.iloc[0] else "decreasing"
                trends.append({
                    "type": "monthly",
                    "direction": trend_direction,
                    "change_percent": ((monthly_spending.iloc[-1] - monthly_spending.iloc[0]) / monthly_spending.iloc[0] * 100)
                })
        
        # Category trends
        category_totals = df.groupby('category')['amount'].sum().sort_values(ascending=False)
        trends.append({
            "type": "top_categories",
            "data": category_totals.head(5).to_dict()
        })
        
        return trends
    
    def _generate_insights(self, df: pd.DataFrame) -> List[str]:
        """Generate spending insights"""
        insights = []
        
        total_spending = df['amount'].sum()
        avg_transaction = df['amount'].mean()
        top_category = df.groupby('category')['amount'].sum().idxmax()
        
        insights.append(f"Total spending analyzed: ${total_spending:.2f}")
        insights.append(f"Average transaction amount: ${avg_transaction:.2f}")
        insights.append(f"Top spending category: {top_category}")
        
        # High spending days
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            daily_spending = df.groupby(df['date'].dt.date)['amount'].sum()
            if len(daily_spending) > 0:
                max_day = daily_spending.idxmax()
                max_amount = daily_spending.max()
                insights.append(f"Highest spending day: {max_day} (${max_amount:.2f})")
        
        return insights
    
    def _generate_budget_recommendations(self, category_spending: Dict) -> List[str]:
        """Generate budget recommendations based on spending patterns"""
        recommendations = []
        
        for category, stats in category_spending.items():
            total = stats['sum']
            avg = stats['mean']
            count = stats['count']
            
            if total > 500:  # High spending category
                recommendations.append(f"Consider setting a monthly budget limit for {category} (current: ${total:.2f})")
            
            if avg > 100:  # High average transaction
                recommendations.append(f"Review {category} expenses - high average transaction of ${avg:.2f}")
        
        if not recommendations:
            recommendations.append("Your spending patterns look reasonable. Keep tracking to maintain good habits!")
        
        return recommendations
    
    def _suggest_budget_limits(self, category_spending: Dict) -> Dict[str, float]:
        """Suggest budget limits for each category"""
        budget_suggestions = {}
        
        for category, stats in category_spending.items():
            current_spending = stats['sum']
            # Suggest 10% reduction as a starting point
            suggested_limit = current_spending * 0.9
            budget_suggestions[category] = round(suggested_limit, 2)
        
        return budget_suggestions
    
    def _identify_savings_opportunities(self, df: pd.DataFrame) -> List[Dict]:
        """Identify potential savings opportunities"""
        opportunities = []
        
        # Frequent small transactions
        small_frequent = df[df['amount'] < 20].groupby('category').size()
        for category, count in small_frequent.items():
            if count > 10:
                opportunities.append({
                    "type": "frequent_small_purchases",
                    "category": category,
                    "suggestion": f"Consider consolidating {category} purchases to reduce impulse spending",
                    "frequency": count
                })
        
        # High single transactions
        high_transactions = df[df['amount'] > df['amount'].quantile(0.9)]
        if len(high_transactions) > 0:
            for _, transaction in high_transactions.iterrows():
                opportunities.append({
                    "type": "high_value_transaction",
                    "category": transaction.get('category', 'Unknown'),
                    "amount": transaction['amount'],
                    "suggestion": "Review if this high-value expense was necessary"
                })
        
        return opportunities

# Create the service instance
ai_service = AIService()

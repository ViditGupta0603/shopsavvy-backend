from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth_working as auth, expenses, receipts  # Add receipts
from app.database.mongodb import connect_to_mongo, close_mongo_connection
import logging

logging.basicConfig(level=logging.DEBUG)

app = FastAPI(
    title="ShopSavvy API",
    description="Personal expense tracking with AI-powered insights",
    version="1.0.0",
    debug=True
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()
    print("✅ MongoDB connected successfully!")

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

# Include all routers
app.include_router(auth.router)
app.include_router(expenses.router)
app.include_router(receipts.router)  # Add receipts router

@app.get("/")
async def root():
    return {"message": "ShopSavvy API with OCR is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ShopSavvy API"}

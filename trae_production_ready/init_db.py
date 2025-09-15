#!/usr/bin/env python3
"""
Database initialization script
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import engine, Base
from app.models import user, base  # Import models to register them

def init_database():
    """Initialize the database and create all tables"""
    print("Creating database tables...")
    
    # Create the database file if it doesn't exist
    db_path = "app.db"
    if not os.path.exists(db_path):
        open(db_path, 'a').close()
        print(f"Created database file: {db_path}")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_database()
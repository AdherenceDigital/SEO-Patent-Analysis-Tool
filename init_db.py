# init_db.py
from database.db_manager import init_db

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialization complete.")

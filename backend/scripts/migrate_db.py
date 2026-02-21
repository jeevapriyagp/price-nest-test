import sys
import os
from sqlalchemy import text
from pathlib import Path

# Add the project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

try:
    from backend.app.core.database import engine
except ImportError:
    # Try alternative import path
    sys.path.append(str(BASE_DIR / "backend"))
    from app.core.database import engine

def migrate():
    print("🚀 Starting database migration...")
    
    # List of expected columns and their types for specific tables
    # Format: (table_name, column_name, column_type)
    migrations = [
        ("alerts", "last_alerted_price", "FLOAT"),
        ("alerts", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        # Add more here if needed
    ]

    with engine.connect() as conn:
        for table, column, col_type in migrations:
            try:
                # Check if column exists
                # This syntax works for PostgreSQL (Neon)
                check_query = text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='{table}' AND column_name='{column}';
                """)
                result = conn.execute(check_query).fetchone()
                
                if not result:
                    print(f"➕ Adding column '{column}' to table '{table}'...")
                    alter_query = text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type};")
                    conn.execute(alter_query)
                    conn.commit()
                    print(f"✅ Column '{column}' added successfully.")
                else:
                    print(f"ℹ️ Column '{column}' already exists in table '{table}'.")
            except Exception as e:
                print(f"❌ Error migrating {table}.{column}: {e}")

    print("🏁 Migration finished.")

if __name__ == "__main__":
    migrate()

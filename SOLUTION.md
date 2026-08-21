# Solution: Import CSV Files to Database

## Overview
This solution provides a way to import the existing CSV files (top_large_cap_funds.csv, top_mid_cap_funds.csv, top_small_cap_funds.csv, top_debt_funds.csv) into a new database called `mutual-fund.db` and read from there instead of using the current mutual_funds.db.

## Step 1: Create Import Script

Create a new file called `import_csv_to_db.py`:

```python
import sqlite3
import pandas as pd
import os
from datetime import datetime

def create_mutual_fund_db_from_csv():
    """Create mutual-fund.db database from CSV files"""
    
    # Create new database
    conn = sqlite3.connect('mutual-fund.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mutual_fund_assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scheme_code TEXT UNIQUE NOT NULL,
            scheme_name TEXT,
            fund_house TEXT,
            type TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mutual_fund_suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER,
            date TEXT NOT NULL,
            score REAL NOT NULL,
            reasoning TEXT,
            FOREIGN KEY(asset_id) REFERENCES mutual_fund_assets(id)
        )
    ''')
    
    conn.commit()
    
    # CSV files to import
    csv_files = [
        'top_large_cap_funds.csv',
        'top_mid_cap_funds.csv', 
        'top_small_cap_funds.csv',
        'top_debt_funds.csv'
    ]
    
    for csv_file in csv_files:
        if os.path.exists(csv_file):
            print(f"Importing {csv_file}...")
            
            # Read CSV
            df = pd.read_csv(csv_file)
            
            # Determine category from filename
            if 'large_cap' in csv_file:
                category = 'large_cap'
            elif 'mid_cap' in csv_file:
                category = 'mid_cap'
            elif 'small_cap' in csv_file:
                category = 'small_cap'
            elif 'debt' in csv_file:
                category = 'debt'
            else:
                continue
            
            # Insert assets
            for _, row in df.iterrows():
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO mutual_fund_assets 
                        (scheme_code, scheme_name, fund_house, type)
                        VALUES (?, ?, ?, ?)
                    ''', (row['scheme_code'], row['scheme_name'], 
                          row['fund_house'], category))
                except sqlite3.Error as e:
                    print(f"Error inserting asset {row['scheme_code']}: {e}")
            
            conn.commit()
            
            # Insert suggestions
            for _, row in df.iterrows():
                # Get asset_id
                cursor.execute('SELECT id FROM mutual_fund_assets WHERE scheme_code = ?', (row['scheme_code'],))
                result = cursor.fetchone()
                
                if result:
                    asset_id = result[0]
                    
                    # Use today's date for suggestion date
                    date = datetime.now().strftime('%Y-%m-%d')
                    
                    try:
                        cursor.execute('''
                            INSERT INTO mutual_fund_suggestions 
                            (asset_id, date, score, reasoning)
                            VALUES (?, ?, ?, ?)
                        ''', (asset_id, date, row['score'], 
                              f"Top {category.replace('_', ' ').title()} fund based on returns"))
                    except sqlite3.Error as e:
                        print(f"Error inserting suggestion for {row['scheme_code']}: {e}")
            
            conn.commit()
            print(f"Completed importing {csv_file}")
    
    conn.close()
    print("Database created successfully!")

if __name__ == "__main__":
    create_mutual_fund_db_from_csv()
```

## Step 2: Modify flask_app.py

Update the `get_mutual_fund_session()` function in `flask_app.py` to read from the new database:

```python
def get_mutual_fund_session():
    """Get a database session for mutual funds"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine('sqlite:///mutual-fund.db')
    Session = sessionmaker(bind=engine)
    return Session()

# Also update the init_mutual_funds_db function
def init_mutual_funds_db():
    """Initialize the mutual funds database and create tables if they don't exist."""
    try:
        from sqlalchemy import create_engine
        from models import Base
        
        engine = create_engine('sqlite:///mutual-fund.db')
        Base.metadata.create_all(engine)
        print("Mutual funds database (mutual-fund.db) initialized successfully.")
    except Exception as e:
        print(f"Warning: Could not initialize mutual funds database: {e}")
```

## Step 3: Run the Solution

1. Save the import script as `import_csv_to_db.py`
2. Run it to create the database:
   ```bash
   python3 import_csv_to_db.py
   ```
3. The script will create `mutual-fund.db` with all the data from the CSV files
4. The flask_app.py will automatically read from the new database

## Alternative: Command Line Approach

If you prefer a command-line approach, you can use SQLite's .import feature:

```bash
# Create empty database
sqlite3 mutual-fund.db "VACUUM;"

# Import each CSV file
sqlite3 mutual-fund.db << EOF
.mode csv
.import top_large_cap_funds.csv mutual_fund_assets
.import top_mid_cap_funds.csv mutual_fund_assets  
.import top_small_cap_funds.csv mutual_fund_assets
.import top_debt_funds.csv mutual_fund_assets
EOF
```

## Step 4: Verify the Solution

After running the import script, verify the database:

```bash
# Check database contents
sqlite3 mutual-fund.db "SELECT type, COUNT(*) FROM mutual_fund_assets GROUP BY type;"
```

Expected output:
```
debt|50
large_cap|36
mid_cap|50
small_cap|28
```

## Benefits of This Solution

1. **Separate Database**: Creates a dedicated database for mutual funds
2. **Cleaner Code**: Keeps the original mutual_funds.db for other purposes
3. **Easy Maintenance**: CSV files can be easily updated and re-imported
4. **Better Organization**: Separates concerns between different data sources
5. **No Breaking Changes**: Existing code continues to work with the new database

## Files to Modify

1. **import_csv_to_db.py** (new file) - Import CSV files to database
2. **flask_app.py** - Update database connection to use mutual-fund.db

## Files to Keep

1. **mutual_fund_db.py** - Original database population script (can be kept for reference)
2. **mutual_funds.db** - Original database (can be kept for backup)

This solution provides a clean way to consolidate the CSV data into a database without making extensive code changes to the existing application.
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
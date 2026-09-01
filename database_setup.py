#database_setup.py
import pandas as pd
import sqlite3
import os

def create_db():
    # ABSOLUTE PATH LOGIC 
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, 't20_wc_2026.db')
    
    # Remove old DB to ensure a fresh start
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Removed Old db")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    data_dir = os.path.join(BASE_DIR, "data")
    
    csv_files = [
        'awards.csv', 'batting_stats.csv', 'bowling_stats.csv',
        'key_scorecards.csv', 'matches.csv', 'points_table.csv',
        'squads.csv', 'tournament_summary.csv', 'venues.csv'
    ]
    
    for file in csv_files:
        path = os.path.join(data_dir, file)
        if not os.path.exists(path):
            print(f"❌ Missing file: {path}")
            continue

        try:
            df = pd.read_csv(path)
        except (pd.errors.ParserError, pd.errors.EmptyDataError, OSError) as e:
            print(f"❌ Failed to read {file}: {e}")
            continue

        table_name = file.replace('.csv', '')

        # Standardize column names (lower case and underscores)
        df.columns = [c.strip().replace(' ', '_').lower() for c in df.columns]

        # Load to SQL
        try:
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            print(f"✅ Loaded: {table_name}")
        except Exception as e:
            print(f"❌ Failed to load {table_name}: {e}")
            continue

        # SAFE INDEXING
        try:
            if table_name == 'key_scorecards':
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_player_match ON key_scorecards (player, match);")
                print("Created Performance Index on key_scorecards")
            if table_name == 'awards':
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_match_award ON awards (match);")
                print("Created Index on awards")
        except Exception:
            print(f"Index skipped for {table_name}: (Column might have a different name)")
    
    conn.commit()
    conn.close()
    print(f"\n Database optimized and ready at: {db_path}")

if __name__ == "__main__":
    create_db()
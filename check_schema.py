import sqlite3

def check_schema():
    DATABASE = 'data/steam_reviews_with_authors.db'
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    
    try:
        # Get table names
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cur.fetchall()
        print("\nTables in database:", [t[0] for t in tables])
        
        # Get schema for each table
        for table in tables:
            print(f"\nSchema for table {table[0]}:")
            cur.execute(f"PRAGMA table_info({table[0]})")
            columns = cur.fetchall()
            for col in columns:
                print(f"Column: {col[1]}, Type: {col[2]}")
            
            # Get sample data
            print(f"\nSample data from {table[0]}:")
            cur.execute(f"SELECT * FROM {table[0]} LIMIT 1")
            sample = cur.fetchone()
            if sample:
                for col, val in zip([c[1] for c in columns], sample):
                    print(f"{col}: {val}")
                    
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        cur.close()
        con.close()

if __name__ == '__main__':
    check_schema()

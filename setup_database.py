import sqlite3

def setup_database():
    """
    Sets up the SQLite database by creating the necessary tables if they do not exist.
    
    Tables:
        trades (id, coin_name, position, mode, date, leverage, entry_price, exit_price)
        notes (id, title, content, date)
    """
    # Connect to the SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect("trade_data.db")  # Database name
    cursor = conn.cursor()

    try:
        # Create 'trades' table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coin_name TEXT NOT NULL,
                position TEXT NOT NULL,
                mode TEXT NOT NULL,
                date TEXT NOT NULL,
                leverage REAL NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL NOT NULL
            )
        ''')

        # Create 'notes' table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE,
                content TEXT NOT NULL,
                date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("Tables created successfully!")

    except sqlite3.Error as e:
        print(f"Database error: {e}")

    finally:
        conn.commit()
        conn.close()

if __name__ == "__main__":
    setup_database()

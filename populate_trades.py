import sqlite3
import random
from datetime import datetime

def populate_trades():
    """
    Resets the 'trades' table in the SQLite database and populates it with 200 random trades.
    Ensures that each coin has between 5 and 40 trades and that trade prices are within specified ranges.
    """
    # Connect to the SQLite database
    conn = sqlite3.connect("trade_data.db")
    cursor = conn.cursor()

    # 1. Reset the 'trades' table
    cursor.execute("DROP TABLE IF EXISTS trades")
    conn.commit()

    # 2. Recreate the 'trades' table
    cursor.execute("""
        CREATE TABLE trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            coin_name TEXT NOT NULL,
            position TEXT NOT NULL,
            leverage INTEGER NOT NULL,
            entry_price REAL NOT NULL,
            exit_price REAL NOT NULL,
            mode TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)
    conn.commit()

    # 3. Define coin price ranges
    coins = {
        "btc": (75000, 108000),
        "eth": (2500, 4000),
        "near": (4, 7),
        "xrp": (1.5, 3),
        "bnb": (400, 700),
        "sol": (130, 250),
        "ada": (0.85, 1.20),
        "avax": (20.50, 50),  
        "sui": (2, 5),
        "link": (10, 30)
    }

    # 4. Define minimum and maximum number of trades per coin
    min_trades_per_coin = 5
    max_trades_per_coin = 40
    total_trades = 200

    # Initialize trade distribution with minimum trades per coin
    trades_distribution = {coin: min_trades_per_coin for coin in coins}
    remaining_trades = total_trades - (min_trades_per_coin * len(coins))

    # Distribute remaining trades randomly among coins, ensuring max limit
    coin_names = list(coins.keys())
    while remaining_trades > 0:
        coin = random.choice(coin_names)
        if trades_distribution[coin] < max_trades_per_coin:
            trades_distribution[coin] += 1
            remaining_trades -= 1

    # 5. Define possible positions and modes
    positions = ["long", "short"]
    modes = ["real", "demo"]

    # All trades will have today's date
    today_str = datetime.now().strftime("%Y-%m-%d")

    for coin, num_trades in trades_distribution.items():
        min_price, max_price = coins[coin]

        # If min and max price are the same, add a small buffer to create a price range
        if min_price == max_price:
            buffer = 0.05  # 5% buffer
            min_price = min_price * (1 - buffer)
            max_price = max_price * (1 + buffer)

        for _ in range(num_trades):
            position = random.choice(positions)
            mode = random.choice(modes)
            leverage = random.randint(1, 20)
            entry_price = round(random.uniform(min_price, max_price), 2)

            # Determine exit price based on position
            if position == "long":
                # 70% chance exit price is higher than entry price, 30% lower
                if random.random() < 0.7 and entry_price < coins[coin][1]:
                    exit_price = round(random.uniform(entry_price, coins[coin][1]), 2)
                else:
                    exit_price = round(random.uniform(coins[coin][0], entry_price), 2)
            else:
                # 70% chance exit price is lower than entry price, 30% higher
                if random.random() < 0.7 and entry_price > coins[coin][0]:
                    exit_price = round(random.uniform(coins[coin][0], entry_price), 2)
                else:
                    exit_price = round(random.uniform(entry_price, coins[coin][1]), 2)

            trade_date = today_str  # All trades have today's date

            # Insert the trade into the database
            cursor.execute("""
                INSERT INTO trades (coin_name, position, leverage, entry_price, exit_price, mode, date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                coin,
                position,
                leverage,
                entry_price,
                exit_price,
                mode,
                trade_date
            ))

    # 6. Commit changes and close the connection
    conn.commit()
    conn.close()

    print("Database reset and 200 random trades added successfully.")

if __name__ == "__main__":
    populate_trades()

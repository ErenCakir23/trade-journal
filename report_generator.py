import os
import sqlite3
from datetime import datetime
from fpdf import FPDF
from collections import Counter

def generate_full_report_with_recommendations(conn):
    """
    Generates a comprehensive PDF report including general and daily reports, detailed analysis,
    recommendation sections, and a comparison between Spot (1x) and Leveraged Trades.

    Parameters:
    conn (sqlite3.Connection): The SQLite database connection.
    """
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d")

    # Ensure the reports directory exists
    os.makedirs("reports", exist_ok=True)
    pdf_name = f"report_{today_str}.pdf"
    pdf_path = os.path.join("reports", pdf_name)

    # Fetch all trades
    cursor.execute("""
        SELECT coin_name, position, leverage, entry_price, exit_price, mode, date
        FROM trades
    """)
    all_trades = cursor.fetchall()

    # Fetch today's trades
    cursor.execute("""
        SELECT coin_name, position, leverage, entry_price, exit_price, mode, date
        FROM trades
        WHERE date = ?
    """, (today_str,))
    daily_trades = cursor.fetchall()

    ############################################################################
    # 1) GENERAL + DAILY METRICS CALCULATION
    ############################################################################
    def calculate_metrics(trades):
        """
        Calculates various trading metrics based on the provided trades.

        Parameters:
        trades (list of tuple): List of trade records.

        Returns:
        dict: A dictionary containing calculated metrics.
        """
        if not trades:
            return {
                "total_trades": 0,
                "top_coin": "None",
                "top_coin_count": 0,
                "top_position": "None",
                "top_leverage": 0,
                "best_coin": "None",
                "best_coin_avg_pnl": 0.0,
                "worst_coin": "None",
                "worst_coin_avg_pnl": 0.0,
                "max_pnl": 0.0,
                "min_pnl": 0.0,
                "net_pnl": 0.0,
            }

        total_trades = len(trades)

        # Most traded coin
        coin_counter = Counter([t[0] for t in trades])  # coin_name
        top_coin, top_coin_count = coin_counter.most_common(1)[0]

        # Most used position
        position_counter = Counter([t[1].lower() for t in trades])
        top_position, _ = position_counter.most_common(1)[0]

        # Most used leverage
        leverage_counter = Counter([t[2] for t in trades])
        top_leverage, _ = leverage_counter.most_common(1)[0]

        # Calculate PnL
        def get_pnl(position, leverage, entry_price, exit_price):
            if entry_price == 0:
                return 0
            if position.lower() == "long":
                return ((exit_price - entry_price) / entry_price) * 100 * leverage
            else:  # short
                return ((entry_price - exit_price) / entry_price) * 100 * leverage

        coin_pnl_dict = {}
        all_pnl_list = []

        for (coin, pos, lev, entry, exit_, mode_, dte) in trades:
            pnl = get_pnl(pos, lev, entry, exit_)
            coin_pnl_dict.setdefault(coin, []).append(pnl)
            all_pnl_list.append(pnl)

        if all_pnl_list:
            max_pnl = max(all_pnl_list)
            min_pnl = min(all_pnl_list)
            net_pnl = sum(all_pnl_list)
        else:
            max_pnl = 0.0
            min_pnl = 0.0
            net_pnl = 0.0

        # Best and worst coins based on average PnL
        best_coin = "None"
        best_coin_avg_pnl = float("-inf")
        worst_coin = "None"
        worst_coin_avg_pnl = float("inf")

        for c, pnls in coin_pnl_dict.items():
            avg_pnl = sum(pnls) / len(pnls)
            if avg_pnl > best_coin_avg_pnl:
                best_coin_avg_pnl = avg_pnl
                best_coin = c
            if avg_pnl < worst_coin_avg_pnl:
                worst_coin_avg_pnl = avg_pnl
                worst_coin = c

        return {
            "total_trades": total_trades,
            "top_coin": top_coin,
            "top_coin_count": top_coin_count,
            "top_position": top_position,
            "top_leverage": top_leverage,
            "best_coin": best_coin,
            "best_coin_avg_pnl": best_coin_avg_pnl,
            "worst_coin": worst_coin,
            "worst_coin_avg_pnl": worst_coin_avg_pnl,
            "max_pnl": max_pnl,
            "min_pnl": min_pnl,
            "net_pnl": net_pnl,
        }

    all_time_stats = calculate_metrics(all_trades)
    daily_stats = calculate_metrics(daily_trades)

    ############################################################################
    # 2) DETAILED ANALYSIS
    ############################################################################
    def get_pnl(position, leverage, entry_price, exit_price):
        """
        Calculates the leveraged PnL for a trade.

        Parameters:
        position (str): 'long' or 'short'.
        leverage (int): The leverage used.
        entry_price (float): Entry price of the trade.
        exit_price (float): Exit price of the trade.

        Returns:
        float: The PnL percentage.
        """
        if entry_price == 0:
            return None
        if position.lower() == "long":
            return ((exit_price - entry_price) / entry_price) * 100 * leverage
        else:  # short
            return ((entry_price - exit_price) / entry_price) * 100 * leverage

    def get_spot_pnl(position, entry_price, exit_price):
        """
        Calculates the spot (1x) PnL for a trade.

        Parameters:
        position (str): 'long' or 'short'.
        entry_price (float): Entry price of the trade.
        exit_price (float): Exit price of the trade.

        Returns:
        float: The PnL percentage.
        """
        if entry_price == 0:
            return None
        if position.lower() == "long":
            return ((exit_price - entry_price) / entry_price) * 100
        else:
            return ((entry_price - exit_price) / entry_price) * 100

    real_count = real_win = real_loss = 0
    demo_count = demo_win = demo_loss = 0
    long_count = long_win = long_loss = 0
    short_count = short_win = short_loss = 0
    low_count = low_win = low_loss = 0
    high_count = high_win = high_loss = 0

    long_trades = []
    short_trades = []

    # Calculate average Spot and Leveraged PnL
    spot_pnl_list = []
    leverage_pnl_list = []

    # Coin success analysis: coin -> (win_count, total_count)
    coin_success_dict = {}

    for (coin, position, lev, entry, exit_, mode_, dte) in all_trades:
        actual_pnl = get_pnl(position, lev, entry, exit_)
        spot_pnl = get_spot_pnl(position, entry, exit_)

        # Add to PnL lists if valid
        if actual_pnl is not None and spot_pnl is not None:
            leverage_pnl_list.append(actual_pnl)
            spot_pnl_list.append(spot_pnl)

        # Track coin success ratio
        if coin not in coin_success_dict:
            coin_success_dict[coin] = [0, 0]  # [win_count, total_count]

        # REAL vs DEMO
        if actual_pnl is not None:
            if mode_.lower() == "real":
                real_count += 1
                if actual_pnl > 0:
                    real_win += 1
                    coin_success_dict[coin][0] += 1
                elif actual_pnl < 0:
                    real_loss += 1
                coin_success_dict[coin][1] += 1
            else:
                demo_count += 1
                if actual_pnl > 0:
                    demo_win += 1
                    coin_success_dict[coin][0] += 1
                elif actual_pnl < 0:
                    demo_loss += 1
                coin_success_dict[coin][1] += 1

        # LONG vs SHORT
        if actual_pnl is not None:
            if position.lower() == "long":
                long_count += 1
                if actual_pnl > 0:
                    long_win += 1
                elif actual_pnl < 0:
                    long_loss += 1
                long_trades.append((coin, actual_pnl, entry, exit_))
            else:
                short_count += 1
                if actual_pnl > 0:
                    short_win += 1
                elif actual_pnl < 0:
                    short_loss += 1
                short_trades.append((coin, actual_pnl, entry, exit_))

        # Low vs High leverage
        if actual_pnl is not None:
            if lev <= 5:
                low_count += 1
                if actual_pnl > 0:
                    low_win += 1
                elif actual_pnl < 0:
                    low_loss += 1
            else:
                high_count += 1
                if actual_pnl > 0:
                    high_win += 1
                elif actual_pnl < 0:
                    high_loss += 1

    # Top 3 and worst 3 Long trades
    long_trades_sorted = sorted(long_trades, key=lambda x: x[1], reverse=True)
    top3_long = long_trades_sorted[:3]
    worst3_long = long_trades_sorted[-3:]

    # Top 3 and worst 3 Short trades
    short_trades_sorted = sorted(short_trades, key=lambda x: x[1], reverse=True)
    top3_short = short_trades_sorted[:3]
    worst3_short = short_trades_sorted[-3:]

    # Calculate average PnLs
    avg_spot_pnl = sum(spot_pnl_list) / len(spot_pnl_list) if spot_pnl_list else 0
    avg_lev_pnl = sum(leverage_pnl_list) / len(leverage_pnl_list) if leverage_pnl_list else 0

    ############################################################################
    # 3) RECOMMENDATION SECTION
    ############################################################################
    # coin_success_dict = { coin: [win_count, total_count] }
    coin_recommendations = []
    for c, (win_count, total_count) in coin_success_dict.items():
        if total_count > 0:
            sr = win_count / total_count
            coin_recommendations.append((c, sr, total_count))

    coin_recommendations.sort(key=lambda x: x[1], reverse=True)

    # Position type success ratios
    long_ratio = long_win / long_count if long_count > 0 else 0
    short_ratio = short_win / short_count if short_count > 0 else 0

    # Leverage success ratios
    low_ratio = low_win / low_count if low_count > 0 else 0
    high_ratio = high_win / high_count if high_count > 0 else 0

    ############################################################################
    # 4) PDF CREATION
    ############################################################################
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)

    # Title
    pdf.cell(200, 10, txt="CRYPTO TRADING REPORT", align="C", ln=1)
    pdf.ln(5)

    # --- GENERAL REPORT ---
    pdf.cell(200, 10, txt="[GENERAL REPORT]", align="L", ln=1)
    pdf.cell(200, 8, txt=f"Total Trades: {all_time_stats['total_trades']}", align="L", ln=1)
    pdf.cell(200, 8, txt=f"Most Traded Coin: {all_time_stats['top_coin']} ({all_time_stats['top_coin_count']} trades)", align="L", ln=1)
    pdf.cell(200, 8, txt=f"Most Used Position: {all_time_stats['top_position']}", align="L", ln=1)
    pdf.cell(200, 8, txt=f"Most Used Leverage: {all_time_stats['top_leverage']}x", align="L", ln=1)
    pdf.cell(200, 8, txt=f"Best Performing Coin (Average PnL): {all_time_stats['best_coin']} ({all_time_stats['best_coin_avg_pnl']:.2f}%)", align="L", ln=1)
    pdf.cell(200, 8, txt=f"Worst Performing Coin (Average PnL): {all_time_stats['worst_coin']} ({all_time_stats['worst_coin_avg_pnl']:.2f}%)", align="L", ln=1)
    pdf.cell(200, 8, txt=f"Highest Single Trade PnL: {all_time_stats['max_pnl']:.2f}%", align="L", ln=1)
    pdf.cell(200, 8, txt=f"Lowest Single Trade PnL: {all_time_stats['min_pnl']:.2f}%", align="L", ln=1)
    pdf.cell(200, 8, txt=f"Net PnL (Total): {all_time_stats['net_pnl']:.2f}%", align="L", ln=1)
    pdf.ln(5)

    # --- DAILY REPORT ---
    pdf.cell(200, 10, txt=f"[DAILY REPORT] - Date: {today_str}", align="L", ln=1)
    pdf.cell(200, 8, txt=f"Total Trades: {daily_stats['total_trades']}", align="L", ln=1)
    if daily_stats['total_trades'] > 0:
        pdf.cell(200, 8, txt=f"Most Traded Coin: {daily_stats['top_coin']} ({daily_stats['top_coin_count']} trades)", align="L", ln=1)
        pdf.cell(200, 8, txt=f"Most Used Position: {daily_stats['top_position']}", align="L", ln=1)
        pdf.cell(200, 8, txt=f"Most Used Leverage: {daily_stats['top_leverage']}x", align="L", ln=1)
        pdf.cell(200, 8, txt=f"Best Performing Coin (Average PnL): {daily_stats['best_coin']} ({daily_stats['best_coin_avg_pnl']:.2f}%)", align="L", ln=1)
        pdf.cell(200, 8, txt=f"Worst Performing Coin (Average PnL): {daily_stats['worst_coin']} ({daily_stats['worst_coin_avg_pnl']:.2f}%)", align="L", ln=1)
        pdf.cell(200, 8, txt=f"Highest Single Trade PnL: {daily_stats['max_pnl']:.2f}%", align="L", ln=1)
        pdf.cell(200, 8, txt=f"Lowest Single Trade PnL: {daily_stats['min_pnl']:.2f}%", align="L", ln=1)
        pdf.cell(200, 8, txt=f"Net PnL (Total): {daily_stats['net_pnl']:.2f}%", align="L", ln=1)
    else:
        pdf.cell(200, 8, txt="No trades recorded today.", align="L", ln=1)
    pdf.ln(5)

    # --- DETAILED ANALYSIS ---
    pdf.cell(200, 10, txt="[DETAILED ANALYSIS]", align="L", ln=1)
    pdf.ln(2)

    # (Real / Demo)
    pdf.cell(200, 8, txt=f"Real Trades: {real_count} (Wins: {real_win}, Losses: {real_loss})", align="L", ln=1)
    pdf.cell(200, 8, txt=f"Demo Trades: {demo_count} (Wins: {demo_win}, Losses: {demo_loss})", align="L", ln=1)
    pdf.ln(3)

    # (Long / Short)
    pdf.cell(200, 8, txt=f"Long Trades: {long_count} (Wins: {long_win}, Losses: {long_loss})", align="L", ln=1)
    pdf.cell(200, 8, txt=f"Short Trades: {short_count} (Wins: {short_win}, Losses: {short_loss})", align="L", ln=1)
    pdf.ln(3)

    # Top 3 and worst 3 Long trades
    pdf.cell(200, 8, txt="Top 3 Long Trades:", align="L", ln=1)
    if top3_long:
        for (coin, pnl, entry, exit_) in top3_long:
            pdf.cell(200, 8, txt=f"  {coin} -> {pnl:.2f}%", align="L", ln=1)
    else:
        pdf.cell(200, 8, txt="  No data.", align="L", ln=1)
    pdf.ln(3)

    pdf.cell(200, 8, txt="Worst 3 Long Trades:", align="L", ln=1)
    if worst3_long:
        for (coin, pnl, entry, exit_) in worst3_long:
            pdf.cell(200, 8, txt=f"  {coin} -> {pnl:.2f}%", align="L", ln=1)
    else:
        pdf.cell(200, 8, txt="  No data.", align="L", ln=1)
    pdf.ln(3)

    # Top 3 and worst 3 Short trades
    pdf.cell(200, 8, txt="Top 3 Short Trades:", align="L", ln=1)
    if top3_short:
        for (coin, pnl, entry, exit_) in top3_short:
            pdf.cell(200, 8, txt=f"  {coin} -> {pnl:.2f}%", align="L", ln=1)
    else:
        pdf.cell(200, 8, txt="  No data.", align="L", ln=1)
    pdf.ln(3)

    pdf.cell(200, 8, txt="Worst 3 Short Trades:", align="L", ln=1)
    if worst3_short:
        for (coin, pnl, entry, exit_) in worst3_short:
            pdf.cell(200, 8, txt=f"  {coin} -> {pnl:.2f}%", align="L", ln=1)
    else:
        pdf.cell(200, 8, txt="  No data.", align="L", ln=1)
    pdf.ln(3)

    # Low vs High leverage
    pdf.cell(200, 8, txt=f"Low Leverage (1-5x): {low_count} (Wins: {low_win}, Losses: {low_loss})", align="L", ln=1)
    pdf.cell(200, 8, txt=f"High Leverage (5x+): {high_count} (Wins: {high_win}, Losses: {high_loss})", align="L", ln=1)
    pdf.ln(5)

    # --- SPOT vs LEVERAGED PnL COMPARISON ---
    pdf.cell(200, 10, txt="[SPOT (1x) vs LEVERAGED PnL COMPARISON]", align="L", ln=1)
    pdf.ln(2)
    pdf.cell(200, 8, txt=f"Average Spot PnL: {avg_spot_pnl:.2f}%", align="L", ln=1)
    pdf.cell(200, 8, txt=f"Average Leveraged PnL: {avg_lev_pnl:.2f}%", align="L", ln=1)
    if avg_spot_pnl != 0:
        ratio = avg_lev_pnl / avg_spot_pnl
        pdf.cell(200, 8, txt=f"Leverage/Spot Ratio: {ratio:.2f}x", align="L", ln=1)
    pdf.ln(5)

    # --- RECOMMENDATION SECTION ---
    pdf.cell(200, 10, txt="[RECOMMENDATION SECTION]", align="L", ln=1)
    pdf.ln(2)

    # a) Coin Recommendations
    pdf.cell(200, 8, txt="Which coins should be focused on / avoided?", align="L", ln=1)
    pdf.ln(2)
    if not coin_recommendations:
        pdf.cell(200, 8, txt="No recommendations due to lack of trade data.", align="L", ln=1)
    else:
        # Top 5 successful coins
        best_coins = coin_recommendations[:5]
        # Bottom 5 successful coins
        worst_coins = coin_recommendations[-5:]

        pdf.cell(200, 8, txt="Top Performing Coins (Success Rate):", align="L", ln=1)
        for (c, sr, count_) in best_coins:
            pdf.cell(200, 8, txt=f"  {c}: {sr:.2f} (Total {count_} trades)", align="L", ln=1)
        pdf.ln(3)

        pdf.cell(200, 8, txt="Worst Performing Coins (Success Rate):", align="L", ln=1)
        for (c, sr, count_) in worst_coins:
            pdf.cell(200, 8, txt=f"  {c}: {sr:.2f} (Total {count_} trades)", align="L", ln=1)
        pdf.ln(3)

    # b) Preferred Position Type
    pdf.cell(200, 8, txt="Which position type should be preferred?", align="L", ln=1)
    pdf.ln(2)
    pdf.cell(200, 8, txt=f"Long Success Rate: {long_ratio:.2f}", align="L", ln=1)
    pdf.cell(200, 8, txt=f"Short Success Rate: {short_ratio:.2f}", align="L", ln=1)
    if long_ratio > short_ratio:
        pdf.cell(200, 8, txt="Recommendation: Long positions seem more successful.", align="L", ln=1)
    elif short_ratio > long_ratio:
        pdf.cell(200, 8, txt="Recommendation: Short positions seem more successful.", align="L", ln=1)
    else:
        pdf.cell(200, 8, txt="Recommendation: Long and Short positions are similar or data is insufficient.", align="L", ln=1)
    pdf.ln(5)

    # c) Leverage Recommendation
    pdf.cell(200, 8, txt="Which leverage level should be preferred?", align="L", ln=1)
    pdf.ln(2)
    pdf.cell(200, 8, txt=f"Low Leverage (1-5x) Success Rate: {low_ratio:.2f}", align="L", ln=1)
    pdf.cell(200, 8, txt=f"High Leverage (5x+) Success Rate: {high_ratio:.2f}", align="L", ln=1)
    if low_ratio > high_ratio:
        pdf.cell(200, 8, txt="Recommendation: Low leverage seems more successful.", align="L", ln=1)
    elif high_ratio > low_ratio:
        pdf.cell(200, 8, txt="Recommendation: High leverage seems more successful.", align="L", ln=1)
    else:
        pdf.cell(200, 8, txt="Recommendation: Leverage comparison is inconclusive or data is insufficient.", align="L", ln=1)

    # Save the PDF
    pdf.output(pdf_path)
    print(f"Report generated: {pdf_path}")

# Example usage (outside GUI):
if __name__ == "__main__":
    connection = sqlite3.connect("trade_data.db")
    generate_full_report_with_recommendations(connection)
    connection.close()

import sqlite3
import time

start_time = time.time()
conn = sqlite3.connect('state/market_cache.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute("SELECT symbol, date, open, close, high, low, volume FROM price_bar ORDER BY symbol, date ASC")
rows = c.fetchall()
print(f"Query took {time.time() - start_time:.2f} seconds")

data = {}
for r in rows:
    if r['open'] is None or r['close'] is None:
        continue
    sym = r['symbol']
    if sym not in data:
        data[sym] = []
    data[sym].append(dict(r))

oversold = []
overbought = []

for sym, bars in data.items():
    if len(bars) < 10:
        continue
        
    consecutive_red = 0
    consecutive_green = 0
    
    for b in reversed(bars):
        if b['close'] < b['open']:
            if consecutive_green > 0: break
            consecutive_red += 1
        elif b['close'] > b['open']:
            if consecutive_red > 0: break
            consecutive_green += 1
        else:
            break
            
    if consecutive_red >= 3 or consecutive_green >= 3:
        is_oversold = consecutive_red >= 3
        target_consecutive = consecutive_red if is_oversold else consecutive_green
        
        occurrences = 0
        wins = 0
        sum_returns = 0
        
        curr_streak = 0
        for i in range(len(bars) - 1):
            b = bars[i]
            if is_oversold:
                if b['close'] < b['open']: curr_streak += 1
                else: curr_streak = 0
            else:
                if b['close'] > b['open']: curr_streak += 1
                else: curr_streak = 0
                
            if curr_streak == target_consecutive:
                next_b = bars[i+1]
                occurrences += 1
                
                if b['close'] > 0:
                    next_return = (next_b['close'] - b['close']) / b['close'] * 100
                else:
                    next_return = 0
                sum_returns += next_return
                
                if is_oversold and next_b['close'] > b['close']:
                    wins += 1
                elif not is_oversold and next_b['close'] < b['close']:
                    wins += 1
                    
        if occurrences > 0:
            win_rate = (wins / occurrences) * 100
            avg_return = sum_returns / occurrences
            
            if occurrences >= 3 and win_rate > 50.0:
                latest = bars[-1]
                item = {
                    "symbol": sym,
                    "consecutive": target_consecutive,
                    "occurrences": occurrences,
                    "win_rate": round(win_rate, 2),
                    "avg_return": round(avg_return, 2),
                    "latest": latest
                }
                if is_oversold:
                    oversold.append(item)
                else:
                    overbought.append(item)

print(f"Total time: {time.time() - start_time:.2f} seconds")
print(f"Oversold: {len(oversold)}")
print(f"Overbought: {len(overbought)}")
if oversold:
    print("Sample oversold:", oversold[0])

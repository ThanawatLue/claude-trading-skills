import os
import glob
import re

search_pattern = r'print\("WARNING: Rate limit exceeded\. Waiting 60 seconds\.\.\.", file=sys\.stderr\)\s*time\.sleep\(60\)\s*return self\._rate_limited_get\(url, params, quiet=quiet\)'
replace_content = '''print("ERROR: Daily API rate limit reached (429).", file=sys.stderr)
                    self.rate_limit_reached = True
                    return None'''

files = glob.glob('d:/ex_work/tong_trading/skills/*/scripts/fmp_client.py')
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    new_content = re.sub(search_pattern, replace_content, content, flags=re.MULTILINE)
    
    # Also for the one with no file=sys.stderr (like in references)
    if 'time.sleep(60)' in new_content:
        new_content = re.sub(
            r'print\("WARNING: Rate limit exceeded\. Waiting 60 seconds\.\.\."\)\s*time\.sleep\(60\)\s*return self\._rate_limited_get\(url, params\)',
            '''print("ERROR: Daily API rate limit reached (429).", file=sys.stderr)\\n                    self.rate_limit_reached = True\\n                    return None''',
            new_content, flags=re.MULTILINE
        )

    if new_content != content:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f"Fixed {f}")
    else:
        print(f"No changes needed or pattern not found in {f}")

# Fix screen_dividend_growth_rsi.py, screen_dividend_stocks.py too
extra_files = [
    'd:/ex_work/tong_trading/skills/dividend-growth-pullback-screener/scripts/screen_dividend_growth_rsi.py',
    'd:/ex_work/tong_trading/skills/dividend-growth-pullback-screener/scripts/screen_dividend_growth.py',
    'd:/ex_work/tong_trading/skills/value-dividend-screener/scripts/screen_dividend_stocks.py'
]

for f in extra_files:
    if os.path.exists(f):
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
        
        new_content = re.sub(search_pattern, replace_content, content, flags=re.MULTILINE)
        if new_content != content:
            with open(f, 'w', encoding='utf-8') as file:
                file.write(new_content)
            print(f"Fixed {f}")

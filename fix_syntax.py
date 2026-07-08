import glob

def fix_syntax_error():
    files = glob.glob('d:/ex_work/tong_trading/skills/*/scripts/fmp_client.py')
    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        target = """                self.rate_limit_reached = True
                return None
                else:
                    print("ERROR: Daily API rate limit reached.", file=sys.stderr)
                    self.rate_limit_reached = True
                    return None
            else:"""
            
        replacement = """                self.rate_limit_reached = True
                return None
            else:"""
            
        if target in content:
            content = content.replace(target, replacement)
            
        target2 = """                self.rate_limit_reached = True
                return None
                else:
                    print(
                        "ERROR: Daily API rate limit reached. Stopping analysis.", file=sys.stderr
                    )
                    self.rate_limit_reached = True
                    return None
            else:"""
        
        if target2 in content:
            content = content.replace(target2, replacement)
            
        if content != original_content:
            with open(file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'Fixed {file}')
        else:
            print(f'No fix needed for {file}')

fix_syntax_error()

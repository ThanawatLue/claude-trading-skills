import os, sys, glob, re

def patch_fmp_client():
    files = glob.glob('d:/ex_work/tong_trading/skills/*/scripts/fmp_client.py')
    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        # We want to catch 401 and 403 as well
        content = re.sub(r'elif response\.status_code == 429:', r'elif response.status_code in (401, 403, 429):', content)
        
        # We need to make it print the status code and error message for 401/403, but still set rate_limit_reached
        # The block looks like:
        #             elif response.status_code in (401, 403, 429):
        #                 self.retry_count += 1
        #                 if self.retry_count <= self.max_retries:
        #                     print("ERROR: Daily API rate limit reached (429).", file=sys.stderr)
        #                     self.rate_limit_reached = True
        #                     return None
        #                 else:
        #                     print("ERROR: Daily API rate limit reached.", file=sys.stderr)
        #                     self.rate_limit_reached = True
        #                     return None
        
        # Let's replace the inner part of elif
        pattern = re.compile(r'elif response\.status_code in \(401, 403, 429\):\n(.*?)(?=\n\s*else:)', re.DOTALL)
        
        replacement = r'''elif response.status_code in (401, 403, 429):
                self.retry_count += 1
                if response.status_code == 429:
                    msg = "ERROR: Daily API rate limit reached (429)."
                else:
                    msg = f"ERROR: API request failed: {response.status_code} - {response.text[:200]}"
                
                if self.retry_count <= self.max_retries and response.status_code == 429:
                    print(msg, file=sys.stderr)
                else:
                    print(msg, file=sys.stderr)
                    
                self.rate_limit_reached = True
                return None'''
        
        content = pattern.sub(replacement, content)
        
        if content != original_content:
            with open(file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'Patched {file}')
        else:
            print(f'No changes for {file}')

patch_fmp_client()

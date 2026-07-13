#!/usr/bin/env python3
"""
Unified Market Analysis Runner
Runs the full analysis pipeline for both US and TH markets and saves the results to the database.
Can be executed standalone or via scheduled tasks.
"""
import os
import sys
import json
from datetime import datetime

# Add the project root and dashboard to the path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Load environment variables from .env manually
env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                val = val.strip().strip("'").strip('"')
                os.environ[key.strip()] = val

dashboard_dir = os.path.join(BASE_DIR, "dashboard")
if dashboard_dir not in sys.path:
    sys.path.insert(0, dashboard_dir)


try:
    from dashboard.app import app, api_run, db_load_run
except ImportError as e:
    print(f"Error importing dashboard app: {e}", file=sys.stderr)
    sys.exit(1)

def safe_print(msg: str, file=sys.stdout):
    try:
        print(msg, file=file)
    except UnicodeEncodeError:
        safe_msg = msg.replace("✓", "[SUCCESS]").replace("✗", "[ERROR]")
        try:
            print(safe_msg, file=file)
        except Exception:
            print(msg.encode('ascii', errors='replace').decode('ascii'), file=file)

def run_market_analysis(market: str):
    safe_print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting {market} Market Analysis...")
    
    # Use Flask test request context to run the api_run view function
    with app.test_request_context(query_string={"market": market}):
        try:
            response = api_run()
            result = response.get_json()
            
            if result and result.get("status") == "success":
                safe_print(f"✓ {market} Market Analysis completed successfully.")
                safe_print(f"  Snapshot saved to DB at: {result.get('run_at')}")
                
                # Print a small summary of the exposure
                snapshot = db_load_run(market)
                if snapshot and snapshot.get("exposure"):
                    exp = snapshot["exposure"]
                    recommendation = exp.get("recommendation", "N/A")
                    if isinstance(recommendation, dict):
                        rec = recommendation.get("exposure_posture", "N/A")
                    else:
                        rec = str(recommendation)
                    score = exp.get("composite_score", "N/A")
                    safe_print(f"  Exposure Posture: {rec} (Score: {score})")
                return True
            else:
                safe_print(f"✗ {market} Market Analysis failed or was incomplete.")
                if result and "log" in result:
                    for entry in result["log"]:
                        if not entry.get("ok"):
                            safe_print(f"    - Command failed: {entry.get('cmd')}")
                            safe_print(f"      Error: {entry.get('err')}")
                return False
        except Exception as ex:
            safe_print(f"✗ Exception occurred during {market} analysis: {ex}", file=sys.stderr)
            return False

def main():
    market = "ALL"
    if len(sys.argv) > 1:
        arg = sys.argv[1].upper()
        if arg in ["TH", "US", "ALL"]:
            market = arg
            
    safe_print("=" * 60)
    if market == "ALL":
        safe_print("TRADING INTELLIGENCE - DUAL MARKET ANALYSIS PIPELINE")
    else:
        safe_print(f"TRADING INTELLIGENCE - {market} MARKET ANALYSIS PIPELINE")
    safe_print("=" * 60)
    
    if market == "TH":
        th_ok = run_market_analysis("TH")
        sys.exit(0 if th_ok else 1)
    elif market == "US":
        us_ok = run_market_analysis("US")
        sys.exit(0 if us_ok else 1)
    else:
        us_ok = run_market_analysis("US")
        th_ok = run_market_analysis("TH")
        
        safe_print("\n" + "=" * 60)
        if us_ok and th_ok:
            safe_print("✓ All markets analyzed successfully.")
            sys.exit(0)
        else:
            safe_print("✗ One or more market analysis runs failed.")
            sys.exit(1)

if __name__ == "__main__":
    main()

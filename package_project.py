import os
import sys
import zipfile
from pathlib import Path

# Color codes for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

def print_status(msg, status="info"):
    if status == "success":
        print(f"{GREEN}[OK] {msg}{RESET}")
    elif status == "warning":
        print(f"{YELLOW}[!] {msg}{RESET}")
    elif status == "error":
        print(f"{RED}[ERR] {msg}{RESET}")
    else:
        print(f"[*] {msg}")

def package_project(include_git=False):
    root_dir = Path(__file__).parent.resolve()
    zip_filename = "claude-trading-skills.zip"
    zip_path = root_dir / zip_filename
    
    # Standard directories and files to exclude completely
    exclude_dirs = {
        ".venv",
        "venv",
        "env",
        ".pytest_cache",
        ".ruff_cache",
        ".uv-cache",
        "__pycache__",
        "reports",
        "state",
        "logs",
        "scratch",
        "dist_build",
        "claude_trading_skills.egg-info"
    }
    
    if not include_git:
        exclude_dirs.add(".git")
        exclude_dirs.add(".github")
        exclude_dirs.add(".claude")
        exclude_dirs.add(".codex")
    
    exclude_files = {
        zip_filename,
        "localtunnel-5050-new.log",
        "localtunnel-5050.log",
        "lt.txt",
        "tunnel.txt",
        "market_breadth_history.json",
        ".secrets.baseline"
    }
    
    # We will also exclude any market_breadth_2026*.json or custom user MD/JSON files in the root
    
    print_status(f"Starting to pack project from: {root_dir}")
    print_status(f"Excluding directories: {', '.join(exclude_dirs)}")
    
    count_files = 0
    total_bytes = 0
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(root_dir):
                root_path = Path(root)
                
                # Filter out excluded directories in-place to prevent os.walk from entering them
                dirs[:] = [d for d in dirs if d not in exclude_dirs]
                
                # Relative path from root for folder structure in zip
                rel_root = root_path.relative_to(root_dir)
                
                for file in files:
                    file_path = root_path / file
                    rel_file_path = rel_root / file
                    
                    # Skip specific files
                    if file in exclude_files:
                        continue
                    if file.startswith("market_breadth_") and file.endswith(".json"):
                        continue
                    if file.endswith(".pyc") or file.endswith(".pyo"):
                        continue
                    
                    # Add to zip
                    zipf.write(file_path, rel_file_path)
                    file_size = file_path.stat().st_size
                    total_bytes += file_size
                    count_files += 1
                    
        zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
        print_status(f"Project packaged successfully!", "success")
        print_status(f"Created archive: {zip_path.name}")
        print_status(f"Total files added: {count_files}")
        print_status(f"Uncompressed size: {total_bytes / (1024 * 1024):.2f} MB")
        print_status(f"Compressed ZIP size: {zip_size_mb:.2f} MB", "success")
        
    except Exception as e:
        print_status(f"Failed to package project: {e}", "error")
        sys.exit(1)

if __name__ == "__main__":
    include_git_arg = "--include-git" in sys.argv
    package_project(include_git=include_git_arg)

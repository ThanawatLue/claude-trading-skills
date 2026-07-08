import os
import sys
import subprocess
import shutil
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

def check_python_version():
    print_status("Checking Python version...")
    if sys.version_info < (3, 9):
        print_status("Python 3.9 or higher is required.", "error")
        sys.exit(1)
    print_status(f"Python version {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} detected.", "success")

def check_and_install_uv():
    print_status("Checking for 'uv' package manager...")
    if shutil.which("uv") is None:
        print_status("uv not found. Installing uv...", "warning")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "uv"], check=True)
            print_status("uv installed successfully.", "success")
        except subprocess.CalledProcessError:
            print_status("Failed to install uv. Please install it manually.", "error")
            sys.exit(1)
    else:
        print_status("uv is already installed.", "success")

def setup_virtual_environment():
    print_status("Setting up virtual environment and dependencies using uv...")
    try:
        subprocess.run(["uv", "sync", "--extra", "dev"], check=True)
        print_status("Dependencies installed successfully.", "success")
    except subprocess.CalledProcessError:
        print_status("Failed to run 'uv sync'. Please check your pyproject.toml.", "error")
        sys.exit(1)

def create_directories():
    print_status("Creating necessary data directories...")
    directories = ["reports", "state", "logs", "scratch"]
    root_dir = Path(__file__).parent.resolve()
    for d in directories:
        dir_path = root_dir / d
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print_status(f"Created directory: {d}", "success")
        else:
            print_status(f"Directory already exists: {d}")

def setup_env_file():
    print_status("Setting up .env file...")
    root_dir = Path(__file__).parent.resolve()
    env_file = root_dir / ".env"
    env_template = root_dir / ".env.template"

    if not env_file.exists():
        if env_template.exists():
            shutil.copy(env_template, env_file)
            print_status("Created .env from .env.template.", "success")
            print_status("Please remember to populate your API keys in the .env file.", "warning")
        else:
            print_status("No .env.template found. Skipping .env creation.", "warning")
    else:
        print_status(".env file already exists.")
        
    # Check for basic keys
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "FMP_API_KEY=" in content and "your_key_here" in content:
                print_status("FMP_API_KEY is not set in .env.", "warning")

def main():
    print_status("Starting Setup for Claude Trading Skills Project")
    print("-" * 50)
    
    check_python_version()
    check_and_install_uv()
    setup_virtual_environment()
    create_directories()
    setup_env_file()
    
    print("-" * 50)
    print_status("Setup completed successfully!", "success")
    print_status("You can now activate the virtual environment and run the dashboard:")
    if os.name == 'nt':
        print_status("  run_dashboard.bat")
    else:
        print_status("  .venv/bin/python dashboard/app.py")

if __name__ == "__main__":
    main()

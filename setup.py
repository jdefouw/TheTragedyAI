"""
Quick setup script to verify environment and dependencies.
"""

import sys
import subprocess
import os

def check_python_version():
    """Check Python version."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("❌ Python 3.10+ required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """Check if required packages are installed."""
    required = ['pygame', 'torch', 'numpy', 'pandas', 'supabase']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} not installed")
            missing.append(package)
    
    return len(missing) == 0

def check_env_file():
    """Check if .env file exists."""
    if os.path.exists('.env'):
        print("✅ .env file exists")
        return True
    else:
        print("⚠️  .env file not found (copy from .env.example)")
        return False

def check_supabase_config():
    """Check Supabase configuration."""
    from dotenv import load_dotenv
    load_dotenv()
    
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    if url and key:
        print("✅ Supabase credentials configured")
        return True
    else:
        print("⚠️  Supabase credentials not configured")
        return False

def main():
    """Run all checks."""
    print("Tragedy of the Commons AI - Setup Check\n")
    print("=" * 50)
    
    all_ok = True
    
    print("\n1. Python Version:")
    all_ok &= check_python_version()
    
    print("\n2. Dependencies:")
    all_ok &= check_dependencies()
    
    print("\n3. Environment Configuration:")
    check_env_file()
    check_supabase_config()
    
    print("\n" + "=" * 50)
    if all_ok:
        print("\n✅ Setup looks good! You can start running simulations.")
    else:
        print("\n⚠️  Some issues found. Please install missing dependencies.")
        print("   Run: pip install -r simulation/requirements.txt")

if __name__ == "__main__":
    main()


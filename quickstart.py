#!/usr/bin/env python3
"""
Quick Start Script for Study App
Helps verify installation and provides setup instructions
"""

import sys
import subprocess
from pathlib import Path

def check_python():
    """Check Python version"""
    print(f"✓ Python {sys.version.split()[0]}")
    return sys.version_info >= (3, 8)

def check_imports():
    """Check if required packages are installed"""
    required = [
        'streamlit',
        'langchain',
        'langchain_core',
        'langchain_community',
        'langchain_huggingface',
        'youtube_transcript_api',
        'pypdf',
        'faiss',
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - MISSING")
            missing.append(package)
    
    return missing

def check_env():
    """Check if .env file exists"""
    env_path = Path(".env")
    if env_path.exists():
        print("✓ .env file found")
        return True
    else:
        print("✗ .env file not found")
        print("  Create .env with: HUGGINGFACEHUB_API_TOKEN=your_token")
        return False

def check_db():
    """Check if database exists"""
    db_path = Path("study.db")
    if db_path.exists():
        print(f"✓ Database found ({db_path.stat().st_size} bytes)")
        return True
    else:
        print("ℹ Database will be created on first run")
        return True

def main():
    """Run all checks"""
    print("=" * 50)
    print("📚 Study App - Quick Start Verification")
    print("=" * 50)
    
    print("\n🔍 Checking Python...")
    if not check_python():
        print("❌ Python 3.8+ required")
        return False
    
    print("\n📦 Checking Dependencies...")
    missing = check_imports()
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("\nInstall with:")
        print("  pip install -r requirements.txt")
        return False
    
    print("\n🔑 Checking Environment...")
    has_env = check_env()
    
    print("\n💾 Checking Database...")
    check_db()
    
    print("\n" + "=" * 50)
    if missing or not has_env:
        print("⚠️  Setup incomplete - fix issues above")
        return False
    else:
        print("✅ All checks passed!")
        print("\n🚀 Ready to start:")
        print("  streamlit run study.py")
        return True
    
if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

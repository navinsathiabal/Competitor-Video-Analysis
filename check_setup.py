#!/usr/bin/env python3
"""
Quick validation script to check if all dependencies are available
and API keys are properly loaded before running the server.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("PROJECT HEALTH CHECK")
print("=" * 60)

# Check 1: .env file exists
print("\n[1] Checking .env file...")
env_path = project_root / ".env"
if env_path.exists():
    print(f"   ✅ .env found at {env_path}")
    with open(env_path) as f:
        content = f.read()
        if "your_" in content:
            print("   ⚠️  WARNING: API keys still contain placeholder values!")
            print("   Please update .env with real API keys:")
            print(f"      - YOUTUBE_API_KEY")
            print(f"      - GEMINI_API_KEY")
else:
    print(f"   ❌ .env NOT found - creating template...")
    with open(env_path, "w") as f:
        f.write("YOUTUBE_API_KEY=your_youtube_api_key_here\n")
        f.write("GEMINI_API_KEY=your_gemini_api_key_here\n")
    print(f"   Created: {env_path}")

# Check 2: requirements.txt exists
print("\n[2] Checking requirements.txt...")
req_path = project_root / "requirements.txt"
if req_path.exists():
    print(f"   ✅ requirements.txt found")
    with open(req_path) as f:
        reqs = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    print(f"   Dependencies listed: {len(reqs)}")
else:
    print(f"   ❌ requirements.txt NOT found")

# Check 3: Python dependencies
print("\n[3] Checking Python dependencies...")
required_modules = {
    "fastapi": "FastAPI web framework",
    "uvicorn": "ASGI server",
    "google": "Google API client (google-api-python-client)",
    "pptx": "PowerPoint generation (python-pptx)",
    "pandas": "Data manipulation",
    "pydantic": "Data validation",
    "dotenv": "Environment variables (python-dotenv)"
}

missing = []
for module, description in required_modules.items():
    try:
        __import__(module)
        print(f"   ✅ {module:20} - {description}")
    except ImportError:
        print(f"   ❌ {module:20} - MISSING! ({description})")
        missing.append(module)

if missing:
    print(f"\n   Install missing dependencies with:")
    print(f"   pip install -r requirements.txt")

# Check 4: Load environment variables
print("\n[4] Loading environment variables...")
from dotenv import load_dotenv
load_dotenv()

youtube_key = os.getenv("YOUTUBE_API_KEY")
gemini_key = os.getenv("GEMINI_API_KEY")

if youtube_key and not youtube_key.startswith("your_"):
    print(f"   ✅ YOUTUBE_API_KEY loaded (length: {len(youtube_key)})")
else:
    print(f"   ❌ YOUTUBE_API_KEY missing or placeholder")

if gemini_key and not gemini_key.startswith("your_"):
    print(f"   ✅ GEMINI_API_KEY loaded (length: {len(gemini_key)})")
else:
    print(f"   ❌ GEMINI_API_KEY missing or placeholder")

# Check 5: main.py can be imported
print("\n[5] Checking main.py imports...")
try:
    import main
    print(f"   ✅ main.py imported successfully")
    print(f"   ✅ FastAPI app initialized: {type(main.app).__name__}")
except ImportError as e:
    print(f"   ❌ Import error: {e}")
except Exception as e:
    print(f"   ❌ Runtime error during import: {e}")

print("\n" + "=" * 60)
print("STATUS: Ready to run 'python main.py' if all checks passed ✅")
print("=" * 60)

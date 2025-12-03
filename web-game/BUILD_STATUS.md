# Build Status

## Current Issue

Python is not properly installed or accessible in the current environment. The build cannot proceed without Python 3.9+.

## What You Need to Do

### Option 1: Install Python (Recommended)

1. **Download Python:**
   - Go to https://www.python.org/downloads/
   - Download Python 3.9 or higher
   - **Important:** Check "Add Python to PATH" during installation

2. **Verify Installation:**
   ```powershell
   python --version
   ```

3. **Build the Game:**
   ```powershell
   cd web-game
   .\build.bat
   ```

### Option 2: Use Existing Python Installation

If Python is installed but not in PATH:

1. Find your Python installation (common locations):
   - `C:\Python39\python.exe`
   - `C:\Users\YourName\AppData\Local\Programs\Python\Python39\python.exe`
   - Or check where you installed it

2. Use full path to build:
   ```powershell
   cd web-game
   C:\path\to\python.exe -m pip install pygbag
   C:\path\to\python.exe -m pygbag --build main.py
   ```

### Option 3: Use WSL (Windows Subsystem for Linux)

If you have WSL installed:

```bash
cd /mnt/c/Users/matt/Documents/Programming/TheCommonsAI/web-game
python3 -m pip install pygbag
python3 -m pygbag --build main.py
```

## After Building

Once the build succeeds:

1. **Verify build:**
   ```powershell
   dir build\web\index.html
   ```

2. **Commit the build:**
   ```powershell
   git add build/web
   git commit -m "Build web-game for deployment"
   git push
   ```

## Alternative: Manual Build Instructions

If you prefer to build manually:

```powershell
# Install pygbag
python -m pip install pygbag

# Build the game
cd web-game
python -m pygbag --build main.py

# Verify
dir build\web

# Commit
git add build/web
git commit -m "Build web-game"
git push
```


# ⚠️ Build Required Before Deployment

## Current Status

Your Vercel deployment is showing a 404 because the `build/web` directory is **empty**. 

The game needs to be built locally first before it can be deployed.

## Quick Fix

### Step 1: Build the Game

Open a terminal in the `web-game` directory and run:

```bash
cd web-game

# Option 1: Using npm (recommended)
npm run build

# Option 2: Using Python directly
pip install pygbag
pygbag --build main.py

# Option 3: Using build script
# Windows:
build.bat
# Linux/Mac:
./build.sh
```

### Step 2: Verify Build

Check that files were created:

```bash
# Should show index.html and other files
dir build\web        # Windows
ls build/web         # Linux/Mac
```

You should see:
- `index.html`
- `main.py` (compiled)
- Various `.data` and `.js` files
- Other assets

### Step 3: Commit and Push

```bash
git add build/web
git commit -m "Build web-game for deployment"
git push
```

### Step 4: Vercel Will Auto-Deploy

After pushing, Vercel will automatically detect the new files and redeploy. The 404 should be resolved!

## Why This Happens

Vercel serves static files from the `build/web` directory. If this directory is empty or doesn't exist, there's nothing to serve, resulting in a 404 error.

The build process compiles your Python/Pygame code into WebAssembly that runs in the browser. This must happen **before** deployment.

## Troubleshooting

### Build fails with "Module not found"

The game imports from the parent `simulation` directory. Make sure you're running the build from the repository root or that the simulation directory is accessible.

### Build succeeds but files aren't in build/web

Check the pygbag output directory. It should create `build/web/` by default. If it's creating files elsewhere, you may need to adjust the configuration.

### Still seeing 404 after building and pushing

1. Verify `build/web/index.html` exists in your repository
2. Check Vercel project settings:
   - Root Directory: `web-game`
   - Output Directory: `build/web`
3. Check Vercel deployment logs for any errors


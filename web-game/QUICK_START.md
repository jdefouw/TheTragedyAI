# Quick Start - Web Game Deployment

## The 404 Error

If you're seeing a 404 error on Vercel, it means the `build/web` directory is empty or doesn't exist. You need to build the game first!

## Step 1: Build the Game

Run one of these commands in the `web-game` directory:

```bash
# Option 1: Using npm (if you have Node.js)
npm run build

# Option 2: Using Python directly
pip install pygbag
pygbag --build main.py

# Option 3: Using build script
# Linux/Mac:
./build.sh
# Windows:
build.bat
```

This will create the `build/web` directory with all the static files.

## Step 2: Verify Build

Check that `build/web/index.html` exists:

```bash
ls build/web/index.html  # Linux/Mac
dir build\web\index.html  # Windows
```

## Step 3: Commit and Push

```bash
git add build/web
git commit -m "Add web-game build"
git push
```

## Step 4: Vercel Configuration

In your Vercel project settings:

- **Root Directory**: `web-game`
- **Output Directory**: `build/web`
- **Build Command**: (leave empty)
- **Framework**: Other

## Troubleshooting

### Still seeing 404?

1. **Check build exists:**
   ```bash
   cd web-game
   ls -la build/web/  # Should show index.html and other files
   ```

2. **Verify Vercel settings:**
   - Root Directory must be `web-game`
   - Output Directory must be `build/web`
   - Build Command should be empty

3. **Check deployment logs:**
   - Go to Vercel dashboard → Deployments → Your deployment → Build Logs
   - Look for any errors

### Build fails?

- Make sure Python 3.9+ is installed
- Ensure `simulation` directory is accessible (it's imported by main.py)
- Check that all dependencies can be installed

### Need help?

See `BUILD_INSTRUCTIONS.md` for detailed build steps.


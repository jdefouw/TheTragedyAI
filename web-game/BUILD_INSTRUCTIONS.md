# Building and Deploying the Web Game

## Quick Start

1. **Build the game:**
   ```bash
   cd web-game
   npm run build
   # OR
   ./build.sh  # Linux/Mac
   # OR
   build.bat   # Windows
   ```

2. **Commit the build:**
   ```bash
   git add build/web
   git commit -m "Build web-game for deployment"
   git push
   ```

3. **Deploy on Vercel:**
   - Go to [vercel.com/new](https://vercel.com/new)
   - Import your repository
   - Create a new project (separate from dashboard)
   - Settings:
     - **Root Directory**: `web-game`
     - **Framework**: Other
     - **Build Command**: (leave empty)
     - **Output Directory**: `build/web`
   - Deploy!

## Detailed Steps

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Node.js (optional, for npm scripts)

### Building

The game uses `pygbag` to compile Python/Pygame code to WebAssembly. 

**Using npm (recommended):**
```bash
cd web-game
npm install  # This will install pygbag
npm run build
```

**Using Python directly:**
```bash
cd web-game
pip install pygbag
pygbag --build main.py
```

**Using build scripts:**
- Linux/Mac: `./build.sh`
- Windows: `build.bat`

The build process will:
1. Install pygbag if needed
2. Compile the Python game to WebAssembly
3. Generate static files in `build/web/`
4. Verify the build was successful

### What Gets Built

The `build/web` directory will contain:
- `index.html` - Main entry point
- `main.py` - Compiled Python code (transpiled to JS/WASM)
- Various `.data` and `.js` files - WebAssembly modules and assets
- Other static assets

### Deployment

Since Vercel doesn't natively support Python builds, we pre-build the game locally and commit the `build/web` directory.

**Important:** The `build/web` directory must be committed to your repository for Vercel to deploy it.

### Vercel Configuration

When setting up the Vercel project:

1. **Root Directory**: `web-game`
   - This tells Vercel to look in the web-game folder

2. **Framework Preset**: Other
   - We're not using a standard framework

3. **Build Command**: (leave empty)
   - Files are pre-built, no build step needed

4. **Output Directory**: `build/web`
   - This is where Vercel will serve files from

5. **Install Command**: (leave empty)
   - No dependencies to install (all static files)

### Environment Variables

Set these in Vercel project settings:

- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase anon key

These are used by the game to fetch the latest evolved AI champion.

### Updating After Changes

1. Make changes to `main.py` or other game files
2. Rebuild: `npm run build` or `./build.sh`
3. Commit: `git add build/web && git commit -m "Update game"`
4. Push: `git push`
5. Vercel will automatically redeploy

### Troubleshooting

**Build fails:**
- Ensure Python 3.9+ is installed
- Check that `simulation` directory is accessible (it's imported)
- Verify all dependencies in `requirements.txt` can be installed

**Game doesn't load:**
- Check browser console for errors
- Verify `build/web/index.html` exists
- Ensure Vercel output directory is set correctly

**AI not loading:**
- Check Supabase environment variables
- Verify network tab in browser DevTools
- Check that Supabase tables have data

## File Structure

```
web-game/
├── main.py              # Game source code
├── pygbag_config.json   # Pygbag settings
├── requirements.txt     # Python dependencies
├── package.json         # Build scripts
├── vercel.json          # Vercel config
├── build.sh / build.bat # Build scripts
├── README.md            # Documentation
├── BUILD_INSTRUCTIONS.md # This file
├── build/               # Build output (git-ignored except web/)
│   └── web/             # Static files (committed to git)
└── assets/              # Game assets
```

## Notes

- The game imports from the parent `simulation` directory, so make sure that's available when building
- Pygbag compiles Python to JavaScript/WebAssembly, so the game runs entirely in the browser
- The build output is large (several MB) due to Python runtime and dependencies
- Consider using Vercel's CDN for optimal performance


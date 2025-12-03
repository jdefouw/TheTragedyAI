# Tragedy of the Commons - Web Game

A Python/Pygame game compiled to WebAssembly using `pygbag`. Players compete against evolved AI agents in a resource competition simulation.

## Prerequisites

- Python 3.9+
- pip
- Node.js (for build scripts, optional)

## Building the Game

### Option 1: Using npm (Recommended)

```bash
cd web-game
npm install  # Installs pygbag if needed
npm run build
```

### Option 2: Manual Build

```bash
cd web-game
pip install pygbag
pygbag --build main.py
```

This will create a `build/web` directory containing all the static files needed for deployment.

## Local Testing

After building, you can test locally:

```bash
# Using Python's http.server
cd build/web
python -m http.server 8000

# Or using pygbag's built-in server
pygbag main.py
```

Then open `http://localhost:8000` in your browser.

## Deployment to Vercel

### Step 1: Build the Game

Build the game locally using one of the methods above. This creates the `build/web` directory.

### Step 2: Commit the Build

The `build/web` directory needs to be committed to your repository for Vercel to deploy it:

```bash
# Remove build/web from .gitignore temporarily
git add web-game/build/web
git commit -m "Add web-game build"
```

**Note:** The root `.gitignore` excludes `web-game/build/`, so you'll need to either:
- Remove that line from `.gitignore` before committing, or
- Force add with `git add -f web-game/build/web`

### Step 3: Configure Vercel

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your repository
3. Create a **new project** (separate from the dashboard)
4. Configure:
   - **Root Directory**: `web-game`
   - **Framework Preset**: Other
   - **Build Command**: (leave empty - files are pre-built)
   - **Output Directory**: `build/web`
   - **Install Command**: (leave empty)

### Step 4: Deploy

Click Deploy. Vercel will serve the static files from `build/web`.

## Environment Variables

The game connects to Supabase to fetch the latest evolved AI champion. Set these in your Vercel project settings:

- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon key

These should match the same values used in the dashboard.

## Updating the Game

After making changes to `main.py`:

1. Rebuild: `npm run build` or `pygbag --build main.py`
2. Commit the updated `build/web` directory
3. Push to trigger Vercel redeployment

## Troubleshooting

### Build fails

- Ensure Python 3.9+ is installed
- Check that all dependencies in `requirements.txt` are available
- Verify that the `simulation` directory is accessible (it's imported by `main.py`)

### Game doesn't load in browser

- Check browser console for errors
- Ensure all files in `build/web` are present
- Verify Vercel is serving from the correct directory

### AI champion not loading

- Check Supabase environment variables are set
- Verify network requests in browser DevTools
- Check that the Supabase tables exist and have data

## File Structure

```
web-game/
├── main.py              # Main game code
├── pygbag_config.json  # Pygbag configuration
├── requirements.txt     # Python dependencies
├── package.json        # Build scripts
├── vercel.json         # Vercel deployment config
├── build/              # Build output (git-ignored, but build/web should be committed)
│   └── web/            # Static files for deployment
└── assets/             # Game assets (icons, etc.)
```

## Dependencies

The game imports from the parent `simulation` directory:
- `simulation.config` - Game configuration constants
- `simulation.agent` - Agent class
- `simulation.logger` - Logging and Supabase integration
- `simulation.ai.model` - DQN model for AI agents

Make sure these are available when building.


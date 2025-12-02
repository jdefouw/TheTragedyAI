# Vercel Deployment Guide for The Tragedy of the Commons AI

This project consists of two web-facing components: the **Dashboard** (Next.js) and the **Web Game** (WASM/PyScript). This guide explains how to deploy both to Vercel.

## Part 1: Deploying the Dashboard (Next.js)

The dashboard is a standard Next.js application.

1.  **Push to GitHub**
    *   Ensure your code is pushed to a GitHub repository.

2.  **Create Project in Vercel**
    *   Go to [vercel.com/new](https://vercel.com/new).
    *   Import your repository.
    *   Set the **Root Directory** to `dashboard`. (Click "Edit" next to Root Directory).

3.  **Configure Environment Variables**
    *   In the "Environment Variables" section, add the following from your `.env`:
        *   `NEXT_PUBLIC_SUPABASE_URL`: Your Supabase Project URL.
        *   `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Your Supabase Anon API Key.

4.  **Deploy**
    *   Click **Deploy**.
    *   Once finished, you will get a URL like `https://tragedy-commons-dashboard.vercel.app`.

## Part 2: Deploying the Web Game (Python/WASM)

The web game is a Python application compiled to WebAssembly using `pygbag`. Vercel serves it as static files.

### Step A: Build the Game locally

You need to generate the `build/web` folder before deploying.

```bash
cd web-game
# Install pygbag if needed
pip install pygbag

# Build the game (this creates the build/web folder)
pygbag --build main.py
```

*Note: `pygbag` might start a local server. You can press `Ctrl+C` once it says "Ready". Check that the `build/web` folder exists and contains `index.html`.*

### Step B: Configure Vercel for the Game

Since Vercel expects a single project per repo by default, we need to tell it how to deploy this specific subfolder as a separate site.

**Option 1: Monorepo Setup (Recommended)**

1.  Go to [vercel.com/new](https://vercel.com/new) again.
2.  Import the **same repository** a second time.
3.  Name this project something different (e.g., `tragedy-commons-game`).
4.  **Root Directory**: Set this to `web-game/build/web`.
    *   *Issue:* If you don't commit the `build` folder to GitHub (which is good practice), Vercel won't see it.
    *   *Better Approach:* Set Root Directory to `web-game` and define a Build Command.

**Option 2: Build on Vercel (Best Practice)**

1.  **Root Directory**: Set to `web-game`.
2.  **Framework Preset**: Select "Other".
3.  **Build Command**: `pip install pygbag && pygbag --build main.py`
4.  **Output Directory**: `build/web`
5.  **Environment Variables**: None needed for the static game itself, unless you added server-side secrets (which WASM shouldn't have).

**Note on Python Version in Vercel Build:**
Vercel's default build image might not have the specific Python setup `pygbag` needs perfectly.
*Simplest Solution:* Commit the `web-game/build/web` folder to GitHub.
1.  Remove `web-game/build/` from your `.gitignore` file.
2.  Run `pygbag --build main.py` locally.
3.  Commit the `build/web` folder.
4.  In Vercel:
    *   Root Directory: `web-game/build/web`
    *   Build Command: (Leave empty)
    *   Output Directory: (Leave empty or `.`)

## Part 3: Connecting them

1.  **Update Dashboard Link**:
    In your `web-game/main.py`, update the `DASHBOARD_URL` constant to point to your new Vercel Dashboard URL.
    Re-build and re-deploy the game.

2.  **Update Game Link**:
    In your Dashboard or README, add a link to the deployed Game URL.

## Summary

| Component | Vercel Root Dir | Build Command | Output Dir | Env Vars |
| :--- | :--- | :--- | :--- | :--- |
| **Dashboard** | `dashboard` | `npm run build` | `.next` | `NEXT_PUBLIC_SUPABASE_...` |
| **Game** | `web-game/build/web`* | (None) | (None) | (None) |

*\*Assuming you build locally and commit the static files.*


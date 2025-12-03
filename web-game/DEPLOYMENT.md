# Vercel Deployment Guide for Web Game

## Overview

The web-game is a Python/Pygame application compiled to WebAssembly using `pygbag`. It's deployed as static files on Vercel.

## Deployment Steps

### 1. Build the Game Locally

```bash
cd web-game
npm run build
```

This creates the `build/web` directory with all static files.

### 2. Commit the Build

```bash
git add build/web
git commit -m "Build web-game for deployment"
git push
```

**Note:** The `build/web` directory must be committed. The `.gitignore` has been configured to allow this while ignoring other build artifacts.

### 3. Create Vercel Project

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your GitHub repository
3. **Important:** Create a NEW project (separate from the dashboard)
4. Name it something like `tragedy-commons-game`

### 4. Configure Vercel Settings

In the project settings, configure:

| Setting | Value |
|---------|-------|
| **Root Directory** | `web-game` |
| **Framework Preset** | `Other` |
| **Build Command** | *(leave empty)* |
| **Output Directory** | `build/web` |
| **Install Command** | *(leave empty)* |

### 5. Set Environment Variables

Add these in Vercel project settings → Environment Variables:

- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase anon key

These should match the values used in your dashboard.

### 6. Deploy

Click "Deploy". Vercel will:
1. Clone your repository
2. Navigate to the `web-game` directory
3. Serve static files from `build/web`

## Updating the Game

After making changes:

1. **Rebuild:**
   ```bash
   cd web-game
   npm run build
   ```

2. **Commit:**
   ```bash
   git add build/web
   git commit -m "Update web-game build"
   git push
   ```

3. **Vercel auto-deploys** on push

## Troubleshooting

### Build Not Found

If Vercel says "Build not found":
- Verify `build/web/index.html` exists in your repository
- Check that Root Directory is set to `web-game`
- Ensure Output Directory is `build/web`

### Game Doesn't Load

- Check browser console for errors
- Verify all files in `build/web` are present
- Check Vercel deployment logs

### AI Champion Not Loading

- Verify Supabase environment variables are set
- Check browser Network tab for API calls
- Ensure Supabase tables have data

## Alternative: GitHub Actions

For automated builds, you could set up a GitHub Action that:
1. Builds the game on push
2. Commits the `build/web` directory
3. Triggers Vercel deployment

See `BUILD_INSTRUCTIONS.md` for more details.


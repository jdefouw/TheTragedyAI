# Tragedy of the Commons AI - Execution Guide

Your Distributed Genetic Evolution system is ready. This guide explains how to run each component.

## 1. Database Setup (One Time)

1.  Go to your Supabase Project -> SQL Editor.
2.  Open `supabase_schema_safe.sql` from this project.
3.  Copy/Paste the content and run it to create all tables and policies.

## 2. Start the Evolution Controller (The "Brain")

This script manages the generations. Run it on your laptop or a small server (CPU is fine).

```bash
# Initialize the first generation (Gen 0)
python simulation/ai/evolve.py --init

# Start the continuous evolution loop
python simulation/ai/evolve.py --loop
```

*Output:* It will create random genomes and post jobs to the queue. Then it waits for results.

## 3. Start GPU Workers (The "Muscle")

Run this on your GPU machines. You can run multiple instances on one machine if it's powerful.

```bash
# Worker 1
python simulation/main.py --worker --id "RTX3090-01"

# Worker 2 (in a separate terminal)
python simulation/main.py --worker --id "RTX3090-02"
```

*Output:* They will poll Supabase, download genomes, run the simulation (headless), and upload fitness scores.

## 4. The Web Game (The "Validation")

This allows humans to play against the best AI from the latest generation.

```bash
cd web-game
pygbag main.py
```

*Open:* `http://localhost:8000` (or your Vercel URL).
*Feature:* The game automatically queries Supabase for the latest "Champion" model and lets you play against it.

## 5. The Dashboard (The "Monitor")

View real-time progress of your experiment.

```bash
cd dashboard
npm run dev
```

*Open:* `http://localhost:3000`
*Features:*
- **Evolution Monitor**: Graphs fitness over generations.
- **Queue Status**: See how many jobs are pending.
- **Hypothesis Widget**: Tracks if "Cooperative" strategies are winning.

## Troubleshooting

*   **"Relation does not exist"**: You didn't run the SQL schema script.
*   **Workers idle**: Check if `evolve.py` is running and has created a new generation.
*   **Supabase Connection Error**: Check your `.env` file has the correct URL and Key.

## Deployment

*   **Dashboard**: Deploy the `dashboard/` folder to Vercel.
*   **Web Game**: Deploy the `web-game/build/web` folder to Vercel/GitHub Pages.
*   **Evolution/Workers**: Run these on your local hardware/cloud VMs.


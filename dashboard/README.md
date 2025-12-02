# Tragedy of the Commons AI - Dashboard

Next.js dashboard for real-time monitoring and analysis of the Tragedy of the Commons AI simulation.

## Features

- **Live Monitor**: Real-time ticker showing latest simulation runs
- **Survival Chart**: Comparison of Cooperative vs Aggressive strategies
- **Hardware Efficiency**: Simulations per hour by GPU type
- **Hypothesis Widget**: P-value calculation and hypothesis status

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Create `.env.local`:
   ```bash
   NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_key
   ```

3. Run development server:
   ```bash
   npm run dev
   ```

4. Build for production:
   ```bash
   npm run build
   npm start
   ```

## Deployment

Deploy to Vercel:

1. Push to GitHub
2. Connect Vercel to repository
3. Add environment variables
4. Deploy


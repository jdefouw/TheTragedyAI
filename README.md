# The Tragedy of the Commons AI

A Canadian National Science Fair (CWSF) - Grade 8 project using Deep Reinforcement Learning to simulate the "Tragedy of the Commons." Uses a distributed computing cluster (RTX 3090/4090) to train AI agents and a WebAssembly frontend for human-vs-AI validation.

## Scientific Hypothesis

**"I hypothesize that the evolutionary survival advantage of 'Cooperative Altruism' over 'Predatory Aggression' is not linear, but dependent on a critical threshold of Resource Density ($R_d$). Specifically, simulated populations will only converge on Cooperative Strategies as a stable Nash Equilibrium when resource availability falls within a specific 'Scarcity Window' (predicted between 15% and 35%). Above this window, aggression will dominate; below it, population collapse occurs regardless of strategy."**

## Architecture

The system consists of three main components:

1. **Simulation Cluster** (`simulation/`) - Python-based simulation engine with GPU-accelerated batch processing
2. **Web Game** (`web-game/`) - WASM-compiled game for human validation
3. **Science Dashboard** (`dashboard/`) - Next.js dashboard for real-time monitoring and analysis

All components connect to a central Supabase database for data collection and analysis.

## Project Structure

```
TheCommonsAI/
├── simulation/              # Phase 1: Python simulation core
│   ├── ai/                 # Phase 2: Neural network models
│   ├── config.py           # Configuration (Resource Density steps, Mixed ratios)
│   ├── agent.py            # Agent class with AI integration
│   ├── main.py             # Simulation manager with Mixed Populations & Gini Metric
│   ├── logger.py           # Supabase batch logging (Time-Series & Summary)
│   └── requirements.txt    # Python dependencies
├── web-game/               # Phase 3: WASM web game
│   ├── assets/             # Game assets
│   ├── main.py             # WASM-compatible game
│   └── requirements.txt    # Web game dependencies
├── dashboard/              # Phase 4: Next.js dashboard
│   ├── src/
│   │   ├── app/           # Next.js app directory
│   │   ├── components/    # React components (PopulationDynamics, HypothesisWidget)
│   │   └── lib/           # Utilities (Supabase client)
│   └── package.json       # Node.js dependencies
├── .env.example           # Environment variable template
└── README.md              # This file
```

## Scientific Data Collection

The system collects rich datasets to prove the hypothesis:

1.  **Time-Series Data**: Snapshots of population health every N ticks.
    *   Population counts (Cooperative vs. Aggressive)
    *   Gini Coefficient (Wealth Inequality)
    *   Average Energy
2.  **Mixed Population Simulations**: Experiments starting with 50% Cooperative / 50% Aggressive agents to observe evolutionary stability and convergence.
3.  **Granular Scarcity Analysis**: Resource density tested at fine intervals (5%, 10%, 15%, 20%, 25%, 30%, 35%, 40%, 50%) to pinpoint the "Scarcity Window."

## Setup Instructions

### Prerequisites

- Python 3.10+
- Node.js 18+ (for dashboard)
- CUDA-capable GPU (optional, for training)
- Supabase account and project

### 1. Database Setup

First, create the required tables in your Supabase SQL Editor:

```sql
-- Table 1: Stores batch simulation runs (Summary Stats)
create table simulation_batch_runs (
  id uuid default gen_random_uuid() primary key,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  machine_id text,
  agent_strategy text,
  resource_density float,
  total_ticks_survived int,
  avg_agent_energy float,
  simulation_version text
);

-- Table 2: Stores Time-Series Data (Granular Analysis)
create table simulation_time_series (
  id uuid default gen_random_uuid() primary key,
  simulation_id uuid references simulation_batch_runs(id),
  tick int,
  coop_count int,
  aggressive_count int,
  gini_coefficient float,
  avg_energy float,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Table 3: Stores human vs AI match results
create table human_matches (
  id uuid default gen_random_uuid() primary key,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  player_name text,
  human_survival_time int,
  ai_average_survival_time int,
  winner text,
  difficulty_level text
);
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and fill in your Supabase credentials:

```bash
# Supabase Configuration
SUPABASE_URL=https://lfktihxrcaqxzbcoiruj.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here

# Simulation Configuration
MACHINE_ID=local-dev
SIMULATION_VERSION=v1.0
```

For the dashboard, create `dashboard/.env.local`:

```bash
NEXT_PUBLIC_SUPABASE_URL=https://lfktihxrcaqxzbcoiruj.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here
```

### 3. Simulation Setup

```bash
cd simulation
pip install -r requirements.txt
```

Run a mixed-strategy simulation to test convergence:

```bash
# Edit main.py to set agent_strategy='Mixed'
python main.py
```

Run batch simulations for scientific data collection:

```python
from main import run_batch_simulation

# Run 100 simulations at 20% resource density (inside Scarcity Window)
run_batch_simulation(
    resource_density=0.20,
    agent_strategy='Mixed',
    machine_id='RTX-4090',
    num_runs=100,
    mixed_ratio=0.5
)
```

### 4. Web Game Setup

```bash
cd web-game
pip install -r requirements.txt
pygbag main.py
```

**Controls**:
- **Move**: WASD or Arrow Keys
- **Interact**: Spacebar

**Visuals**:
- 🧑 You (Player)
- 🤖 Cooperative AI
- 👹 Aggressive AI
- 🍎 Food

### 5. Dashboard Setup

```bash
cd dashboard
npm install
npm run dev
```

## Deployment

### Deploy Web Game to Vercel

1. Build the web game: `pygbag main.py`
2. Push `build/web` folder to a GitHub repository
3. Connect Vercel to the repository and set output directory to `build/web`
4. Assign domain: `simulateAI.defouw.ca`

### Deploy Dashboard to Vercel

1. Push `dashboard/` folder to GitHub
2. Connect Vercel to the repository
3. Add environment variables (`NEXT_PUBLIC_SUPABASE_URL`, etc.)
4. Assign domain: `simulate-dashboard.defouw.ca`

## Key Scientific Metrics

- **Gini Coefficient**: Measures wealth inequality. Hypothesis: Aggressive dominance leads to high Gini (inequality).
- **Population Convergence**: Tracks whether the ratio of Cooperative vs. Aggressive agents stabilizes over time.
- **Resource Efficiency**: Total energy maintained in the population relative to food spawned.

## License

MIT License - See LICENSE file for details

## GitHub Repository

https://github.com/jdefouw/TheTragedyAI

## Contact

Email: joeldefouw@gmail.com

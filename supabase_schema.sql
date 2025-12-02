-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- Table 1: Simulation Batch Runs (Summary Statistics)
create table if not exists simulation_batch_runs (
  id uuid default gen_random_uuid() primary key,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  machine_id text,
  agent_strategy text,
  resource_density float,
  total_ticks_survived int,
  avg_agent_energy float,
  simulation_version text
);

-- Table 2: Simulation Time Series (Granular Data)
create table if not exists simulation_time_series (
  id uuid default gen_random_uuid() primary key,
  simulation_id uuid references simulation_batch_runs(id) on delete cascade,
  tick int,
  coop_count int,
  aggressive_count int,
  gini_coefficient float,
  avg_energy float,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Table 3: Human Matches
create table if not exists human_matches (
  id uuid default gen_random_uuid() primary key,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  player_name text,
  human_survival_time int,
  ai_average_survival_time int,
  winner text,
  difficulty_level text
);

-- Table 4: Generations (Genetic Evolution)
create table if not exists simulation_generations (
  id serial primary key,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  status text default 'active', -- 'active', 'completed'
  avg_fitness float,
  best_fitness float
);

-- Table 5: Genomes (The AI Brains)
create table if not exists simulation_genomes (
  id uuid default gen_random_uuid() primary key,
  generation_id int references simulation_generations(id),
  weights jsonb, -- Serialized Neural Network Weights
  fitness_score float, -- Survival Time / Success Rate
  is_elite boolean default false,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- INDEX: Optimize fetching best genomes
create index if not exists idx_genomes_gen_id_fitness 
on simulation_genomes (generation_id, fitness_score desc);

-- Table 6: Simulation Job Queue (Distributed Work)
create table if not exists simulation_queue (
  id uuid default gen_random_uuid() primary key,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  status text default 'pending', -- 'pending', 'processing', 'completed', 'failed'
  assigned_to text, -- Machine ID
  started_at timestamp with time zone,
  completed_at timestamp with time zone,
  genome_id uuid references simulation_genomes(id), -- Genome to test
  params jsonb -- Simulation parameters { "resource_density": 0.2, "max_ticks": 2000 }
);

-- Set up Row Level Security (RLS)
alter table simulation_batch_runs enable row level security;
create policy "Public read access" on simulation_batch_runs for select using (true);
create policy "Public insert access" on simulation_batch_runs for insert with check (true);

alter table simulation_time_series enable row level security;
create policy "Public read access" on simulation_time_series for select using (true);
create policy "Public insert access" on simulation_time_series for insert with check (true);

alter table human_matches enable row level security;
create policy "Public read access" on human_matches for select using (true);
create policy "Public insert access" on human_matches for insert with check (true);

alter table simulation_generations enable row level security;
create policy "Public read access" on simulation_generations for select using (true);
create policy "Public insert access" on simulation_generations for insert with check (true);

alter table simulation_genomes enable row level security;
create policy "Public read access" on simulation_genomes for select using (true);
create policy "Public insert access" on simulation_genomes for insert with check (true);

alter table simulation_queue enable row level security;
create policy "Public read access" on simulation_queue for select using (true);
create policy "Public insert access" on simulation_queue for insert with check (true);
create policy "Public update access" on simulation_queue for update using (true);

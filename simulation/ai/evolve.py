"""
Genetic Evolution Engine for The Tragedy of the Commons AI.
Handles Selection, Crossover, and Mutation of Neural Network weights.
Orchestrates the distributed evolution process via Supabase.
"""

import os
import random
import time
import numpy as np
import torch
from typing import List, Dict, Any
from dotenv import load_dotenv
from supabase import create_client, Client

# Import model definition
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.model import DQN
from config import RESOURCE_DENSITY_OPTIONS

load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://lfktihxrcaqxzbcoiruj.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Evolution Parameters
POPULATION_SIZE = 50  # Genomes per generation
ELITE_PERCENTAGE = 0.20  # Top 20% survive automatically
MUTATION_RATE = 0.05  # Probability of mutation
MUTATION_SIGMA = 0.1  # Strength of mutation
TICKS_PER_EVAL = 2000  # Simulation duration for fitness check


class EvolutionEngine:
    """Manages the evolutionary process."""
    
    def __init__(self):
        self.current_generation_id = None
        self.population = []
    
    def init_generation_zero(self):
        """Create the first generation with random weights."""
        print("Initializing Generation 0...")
        
        # Create generation record
        gen_data = {"status": "active", "avg_fitness": 0.0, "best_fitness": 0.0}
        res = supabase.table("simulation_generations").insert(gen_data).execute()
        self.current_generation_id = res.data[0]['id']
        
        # Create random genomes
        print(f"Creating {POPULATION_SIZE} random genomes...")
        genomes = []
        model = DQN()  # Initialize random model
        
        for i in range(POPULATION_SIZE):
            # Randomize weights
            model = DQN()
            weights = model.get_weights_as_dict()
            
            genomes.append({
                "generation_id": self.current_generation_id,
                "weights": weights,
                "fitness_score": 0.0,
                "is_elite": False
            })
            
        # Upload in batches
        batch_size = 10
        for i in range(0, len(genomes), batch_size):
            batch = genomes[i:i+batch_size]
            supabase.table("simulation_genomes").insert(batch).execute()
            print(f"Uploaded batch {i//batch_size + 1}")
            
        print("Generation 0 initialized. Queuing jobs...")
        self.queue_jobs_for_generation(self.current_generation_id)

    def queue_jobs_for_generation(self, generation_id: int):
        """Create simulation jobs for all genomes in a generation."""
        # Fetch all genomes
        res = supabase.table("simulation_genomes") \
            .select("id") \
            .eq("generation_id", generation_id) \
            .execute()
            
        genomes = res.data
        jobs = []
        
        # For each genome, create a job
        # We test at a challenging density (e.g., 20% - The Scarcity Window)
        params = {
            "resource_density": 0.20,
            "agent_strategy": "Genetic",
            "max_ticks": TICKS_PER_EVAL
        }
        
        for genome in genomes:
            jobs.append({
                "status": "pending",
                "genome_id": genome['id'],
                "params": params
            })
            
        # Upload jobs
        batch_size = 50
        for i in range(0, len(jobs), batch_size):
            batch = jobs[i:i+batch_size]
            supabase.table("simulation_queue").insert(batch).execute()
            
        print(f"Queued {len(jobs)} jobs for Generation {generation_id}")

    def check_generation_complete(self) -> bool:
        """Check if all jobs for the current generation are complete."""
        # Fetch most recent active generation
        if not self.current_generation_id:
            res = supabase.table("simulation_generations") \
                .select("id") \
                .eq("status", "active") \
                .order("created_at", desc=True) \
                .limit(1) \
                .execute()
            if res.data:
                self.current_generation_id = res.data[0]['id']
            else:
                print("No active generation found.")
                return False

        # Check for pending or processing jobs linked to this generation
        # (This requires a join, or we check if all genomes have fitness > 0)
        # Simpler: Check simulation_queue for pending/processing jobs associated with genomes of this gen
        
        # Step 1: Get genome IDs for this gen
        g_res = supabase.table("simulation_genomes") \
            .select("id") \
            .eq("generation_id", self.current_generation_id) \
            .execute()
        genome_ids = [g['id'] for g in g_res.data]
        
        if not genome_ids:
            return False
            
        # Step 2: Check queue
        # Note: Supabase free tier limit on query size might be an issue for huge gens, but 50 is fine
        q_res = supabase.table("simulation_queue") \
            .select("status") \
            .in_("genome_id", genome_ids) \
            .execute()
            
        statuses = [j['status'] for j in q_res.data]
        
        pending = statuses.count('pending')
        processing = statuses.count('processing')
        
        print(f"Gen {self.current_generation_id} Status: {pending} pending, {processing} processing, {statuses.count('completed')} completed")
        
        return pending == 0 and processing == 0

    def crossover(self, parent1_weights: Dict, parent2_weights: Dict) -> Dict:
        """Combine weights of two parents."""
        child_weights = {}
        
        for key in parent1_weights.keys():
            w1 = np.array(parent1_weights[key])
            w2 = np.array(parent2_weights[key])
            
            # Random crossover mask
            mask = np.random.rand(*w1.shape) > 0.5
            child_w = np.where(mask, w1, w2)
            
            child_weights[key] = child_w.tolist()
            
        return child_weights

    def evolve_next_generation(self):
        """Breed the next generation from the best performers."""
        print(f"Evolving Generation {self.current_generation_id} -> Next Gen")
        
        # 1. Fetch all genomes with fitness
        res = supabase.table("simulation_genomes") \
            .select("*") \
            .eq("generation_id", self.current_generation_id) \
            .order("fitness_score", desc=True) \
            .execute()
            
        population = res.data
        if not population:
            print("Error: No population data found.")
            return
            
        # Stats
        avg_fitness = sum(p['fitness_score'] for p in population) / len(population)
        best_fitness = population[0]['fitness_score']
        print(f"Gen Stats - Best: {best_fitness}, Avg: {avg_fitness}")
        
        # Update generation stats
        supabase.table("simulation_generations") \
            .update({
                "status": "completed",
                "avg_fitness": avg_fitness,
                "best_fitness": best_fitness
            }) \
            .eq("id", self.current_generation_id) \
            .execute()
            
        # 2. Selection (Elitism)
        num_elites = int(POPULATION_SIZE * ELITE_PERCENTAGE)
        elites = population[:num_elites]
        
        new_genomes = []
        
        # Create Next Generation ID
        gen_res = supabase.table("simulation_generations").insert({"status": "active"}).execute()
        next_gen_id = gen_res.data[0]['id']
        
        # Add Elites (unchanged)
        print(f"Preserving {len(elites)} elites...")
        for elite in elites:
            new_genomes.append({
                "generation_id": next_gen_id,
                "weights": elite['weights'],
                "fitness_score": 0.0,
                "is_elite": True
            })
            
        # 3. Crossover & Mutation
        num_children = POPULATION_SIZE - len(elites)
        print(f"Breeding {num_children} children...")
        
        model = DQN() # Helper for mutation
        
        for _ in range(num_children):
            # Tournament Selection for parents
            parent1 = random.choice(population[:len(population)//2]) # Pick from top 50%
            parent2 = random.choice(population[:len(population)//2])
            
            # Crossover
            child_weights = self.crossover(parent1['weights'], parent2['weights'])
            
            # Mutation
            model.load_weights_from_dict(child_weights)
            model.mutate(mutation_rate=MUTATION_RATE, sigma=MUTATION_SIGMA)
            final_weights = model.get_weights_as_dict()
            
            new_genomes.append({
                "generation_id": next_gen_id,
                "weights": final_weights,
                "fitness_score": 0.0,
                "is_elite": False
            })
            
        # Upload New Genomes
        batch_size = 10
        for i in range(0, len(new_genomes), batch_size):
            batch = new_genomes[i:i+batch_size]
            supabase.table("simulation_genomes").insert(batch).execute()
            
        self.current_generation_id = next_gen_id
        print(f"Generation {next_gen_id} created.")
        
        # Queue Jobs
        self.queue_jobs_for_generation(next_gen_id)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Evolution Engine')
    parser.add_argument('--init', action='store_true', help='Initialize Generation 0')
    parser.add_argument('--loop', action='store_true', help='Run evolution loop continuously')
    args = parser.parse_args()
    
    engine = EvolutionEngine()
    
    if args.init:
        engine.init_generation_zero()
        
    elif args.loop:
        print("Starting Evolution Loop...")
        while True:
            complete = engine.check_generation_complete()
            if complete:
                engine.evolve_next_generation()
            else:
                print("Waiting for generation to complete... (Checking in 30s)")
                time.sleep(30)
    else:
        # Check once
        if engine.check_generation_complete():
            engine.evolve_next_generation()
        else:
            print("Generation not complete yet.")

if __name__ == "__main__":
    main()


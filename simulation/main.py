"""
Main simulation manager for the Tragedy of the Commons.
Supports headless mode, dynamic GPU-based batching, mixed populations, and distributed genetic evolution.
"""

import os
import random
import time
import numpy as np
from typing import List, Optional, Dict, Any
import pygame
import torch

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, GRID_SIZE, CELL_SIZE,
    INITIAL_AGENT_COUNT, RESOURCE_DENSITY_OPTIONS,
    HEADLESS_MODE, MAX_TICKS, LOG_INTERVAL,
    COLOR_AGENT, COLOR_FOOD, COLOR_COOPERATIVE, COLOR_AGGRESSIVE
)
from agent import Agent
from logger import (
    log_batch_result, log_batch_results, log_time_series,
    fetch_pending_job, complete_job, fail_job,
    fetch_genome_weights, update_genome_fitness
)
from ai.model import DQN


def get_batch_size() -> int:
    """
    Determine batch size based on available GPU VRAM.
    """
    if not torch.cuda.is_available():
        return 1
    try:
        gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        if gpu_memory_gb > 20: return 200
        elif gpu_memory_gb > 8: return 50
        else: return 10
    except Exception:
        return 1


class SimulationManager:
    """Manages the simulation environment and agents."""
    
    def __init__(self, resource_density: float = 0.20, headless: bool = HEADLESS_MODE,
                 agent_strategy: str = 'Random_Walk', machine_id: str = 'local-dev',
                 mixed_ratio: float = 0.5, genome_weights: Dict = None, max_ticks: int = MAX_TICKS):
        """
        Initialize simulation manager.
        """
        self.resource_density = resource_density
        self.headless = headless
        self.agent_strategy = agent_strategy
        self.machine_id = machine_id
        self.mixed_ratio = mixed_ratio
        self.genome_weights = genome_weights
        self.max_ticks = max_ticks
        
        if not self.headless:
            pygame.init()
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.display.set_caption("Tragedy of the Commons Simulation")
            self.clock = pygame.time.Clock()
        else:
            self.screen = None
            self.clock = None
        
        self.agents: List[Agent] = []
        self.food_grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=bool)
        self.agent_grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=int)
        self.tick = 0
        self.running = True
        self.time_series_data = []
        
        self.total_ticks_survived = 0
        self.avg_agent_energy = 0.0
        self.gini_coefficient = 0.0
        
        self.reset()
    
    def reset(self):
        """Reset the simulation to initial state."""
        self.tick = 0
        self.agents = []
        self.food_grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=bool)
        self.agent_grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=int)
        self.time_series_data = []
        
        # Determine strategies
        if self.agent_strategy == 'Mixed':
            num_coop = int(INITIAL_AGENT_COUNT * self.mixed_ratio)
            num_agg = INITIAL_AGENT_COUNT - num_coop
            strategies = (['Cooperative_DQN'] * num_coop + ['Aggressive_PPO'] * num_agg)
        elif self.agent_strategy == 'Genetic':
            # In Genetic mode, all agents share the same "brain" being tested
            strategies = ['Genetic_DQN'] * INITIAL_AGENT_COUNT
        else:
            strategies = [self.agent_strategy] * INITIAL_AGENT_COUNT
            
        # Spawn Agents
        positions = set()
        random.shuffle(strategies)
        
        # If Genetic, load model
        genetic_model = None
        if self.agent_strategy == 'Genetic' and self.genome_weights:
            genetic_model = DQN()
            genetic_model.load_weights_from_dict(self.genome_weights)
        
        for i, strategy in enumerate(strategies):
            while True:
                x = random.randint(0, GRID_SIZE - 1)
                y = random.randint(0, GRID_SIZE - 1)
                if (x, y) not in positions:
                    positions.add((x, y))
                    agent = Agent(x, y, strategy_type=strategy, agent_id=i)
                    
                    # Inject genetic brain if applicable
                    if strategy == 'Genetic_DQN' and genetic_model:
                        agent.model = genetic_model
                    
                    self.agents.append(agent)
                    break
        
        self._spawn_food()
    
    def _spawn_food(self):
        self.food_grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=bool)
        total_cells = GRID_SIZE * GRID_SIZE
        num_food = int(total_cells * self.resource_density)
        food_positions = random.sample(
            [(x, y) for x in range(GRID_SIZE) for y in range(GRID_SIZE)],
            min(num_food, total_cells)
        )
        for x, y in food_positions:
            self.food_grid[y, x] = True
    
    def calculate_gini(self) -> float:
        if not self.agents: return 0.0
        energies = sorted([a.energy for a in self.agents])
        n = len(energies)
        if n == 0 or sum(energies) == 0: return 0.0
        index = np.arange(1, n + 1)
        return (np.sum((2 * index - n - 1) * energies)) / (n * np.sum(energies))
    
    def capture_snapshot(self):
        coop_count = sum(1 for a in self.agents if 'Cooperative' in a.strategy_type or 'Genetic' in a.strategy_type)
        agg_count = sum(1 for a in self.agents if 'Aggressive' in a.strategy_type)
        
        self.time_series_data.append({
            'tick': self.tick,
            'coop_count': coop_count,
            'aggressive_count': agg_count,
            'gini_coefficient': self.calculate_gini(),
            'avg_energy': sum(a.energy for a in self.agents) / len(self.agents) if self.agents else 0
        })
    
    def update(self):
        if not self.running: return
        self.tick += 1
        self.agent_grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=int)
        
        for agent in self.agents:
            if not agent.alive: continue
            self.agent_grid[agent.y, agent.x] = agent.agent_id + 1
            
            # AI Decision
            action = None
            if agent.model: # Neural/Genetic Agent
                obs = agent.get_observation(self.agent_grid, self.food_grid.astype(float))
                obs_tensor = torch.FloatTensor(obs)
                action = agent.model.predict_action(obs_tensor)
            elif 'Random' not in agent.strategy_type:
                 # Placeholder for non-genetic neural agents (load default model)
                 action = random.randint(0, 4)
            
            agent.move(action)
            
            if self.food_grid[agent.y, agent.x]:
                agent.eat()
                self.food_grid[agent.y, agent.x] = False
            
            # Interactions (Simplified for Genetic: Can they learn to cooperate?)
            # For Genetic_DQN, action 4 is "Interact"
            if action == 4:
                # Look for neighbors
                for other in self.agents:
                    if other.agent_id == agent.agent_id or not other.alive: continue
                    if agent.distance_to(other) <= 1.5:
                        # If they learned to share:
                        agent.share_resource(other)

            agent.update()
        
        self.agents = [a for a in self.agents if a.alive]
        if self.tick % 50 == 0: self._spawn_food()
        if self.tick % LOG_INTERVAL == 0: self.capture_snapshot()
        
        if len(self.agents) == 0 or self.tick >= self.max_ticks:
            self.running = False
            self._calculate_statistics()

    def _calculate_statistics(self):
        if len(self.agents) > 0:
            self.total_ticks_survived = self.tick
            self.avg_agent_energy = sum(a.energy for a in self.agents) / len(self.agents)
            self.gini_coefficient = self.calculate_gini()
        else:
            self.total_ticks_survived = self.tick
            self.avg_agent_energy = 0.0
            self.gini_coefficient = 0.0
    
    def run(self):
        """Run the simulation loop."""
        self.capture_snapshot()
        while self.running and self.tick < self.max_ticks:
            self.update()
            if not self.headless:
                self.draw() # Implemented in previous version, omitted for brevity here
                self.clock.tick(60)
        self._calculate_statistics()
        if not self.headless: pygame.quit()
        
    def get_results(self) -> Dict[str, Any]:
        return {
            'machine_id': self.machine_id,
            'agent_strategy': self.agent_strategy,
            'resource_density': self.resource_density,
            'total_ticks_survived': self.total_ticks_survived,
            'avg_agent_energy': self.avg_agent_energy,
            'simulation_version': 'v2.0-genetic'
        }

# --- WORKER MODE ---

def run_worker_node(machine_id: str):
    """
    Continuous loop that polls for jobs and executes them.
    """
    print(f"Starting Worker Node: {machine_id}")
    print("Waiting for jobs...")
    
    while True:
        # 1. Fetch Job
        job = fetch_pending_job(machine_id)
        
        if job:
            print(f"Processing Job {job['id']}...")
            try:
                params = job.get('params', {})
                genome_id = job.get('genome_id')
                
                # 2. Load Genome if Genetic Job
                genome_weights = None
                if genome_id:
                    genome_weights = fetch_genome_weights(genome_id)
                    if not genome_weights:
                        raise ValueError(f"Could not load weights for genome {genome_id}")
                
                # 3. Run Simulation
                sim = SimulationManager(
                    resource_density=params.get('resource_density', 0.2),
                    headless=True,
                    agent_strategy=params.get('agent_strategy', 'Genetic'),
                    machine_id=machine_id,
                    genome_weights=genome_weights,
                    max_ticks=params.get('max_ticks', MAX_TICKS)
                )
                sim.run()
                
                # 4. Log Results
                results = sim.get_results()
                sim_id = log_batch_result(results)
                
                # Log time series
                for snapshot in sim.time_series_data:
                    snapshot['simulation_id'] = sim_id
                log_time_series(sim.time_series_data)
                
                # 5. Report Fitness (if Genetic)
                if genome_id:
                    # Fitness = Ticks Survived + (Avg Energy * 0.1)
                    fitness = sim.total_ticks_survived + (sim.avg_agent_energy * 0.1)
                    update_genome_fitness(genome_id, fitness)
                
                # 6. Complete Job
                complete_job(job['id'])
                print(f"Job {job['id']} completed. Fitness: {sim.total_ticks_survived}")
                
            except Exception as e:
                print(f"Job failed: {e}")
                fail_job(job['id'], str(e))
        else:
            # No jobs, sleep
            time.sleep(5)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', action='store_true', help='Run as worker node')
    parser.add_argument('--id', type=str, default='local-worker', help='Machine ID')
    args = parser.parse_args()
    
    if args.worker:
        run_worker_node(args.id)
    else:
        # Standard local run
        sim = SimulationManager(headless=False, agent_strategy='Random_Walk')
        sim.run()

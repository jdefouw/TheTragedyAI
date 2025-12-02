"""
Agent class for the Tragedy of the Commons simulation.
Supports both AI-controlled and random walk agents.
"""

import random
import numpy as np
from typing import Optional, Tuple, List
import torch

from config import (
    GRID_SIZE, INITIAL_AGENT_ENERGY, MAX_AGENT_ENERGY,
    ENERGY_DECAY_RATE, FOOD_ENERGY_VALUE, VISION_RANGE,
    SHARE_THRESHOLD, ATTACK_COST, SHARE_COST, ACTION_SPACE
)


class Agent:
    """Represents an agent in the simulation."""
    
    def __init__(self, x: int, y: int, strategy_type: str = 'Random_Walk', agent_id: int = 0):
        """
        Initialize an agent.
        
        Args:
            x: Initial x position
            y: Initial y position
            strategy_type: 'Cooperative_DQN', 'Aggressive_PPO', or 'Random_Walk'
            agent_id: Unique identifier for this agent
        """
        self.x = x
        self.y = y
        self.energy = INITIAL_AGENT_ENERGY
        self.strategy_type = strategy_type
        self.agent_id = agent_id
        self.alive = True
        self.ticks_survived = 0
        
        # For neural network agents
        self.model = None
        self.last_action = None
        
    def move(self, action: Optional[int] = None, observation: Optional[torch.Tensor] = None) -> Tuple[int, int]:
        """
        Move the agent based on strategy.
        
        Args:
            action: Action index (0=Up, 1=Down, 2=Left, 3=Right, 4=Interact)
            observation: Tensor input for neural network (if strategy_type == 'neural')
            
        Returns:
            Tuple of (new_x, new_y)
        """
        if not self.alive:
            return self.x, self.y
            
        # Neural network agents use provided action
        if self.strategy_type in ['Cooperative_DQN', 'Aggressive_PPO'] and action is not None:
            new_x, new_y = self._apply_action(action)
        else:
            # Random walk for non-neural or fallback
            new_x, new_y = self._random_move()
            
        # Ensure agent stays within bounds
        new_x = max(0, min(GRID_SIZE - 1, new_x))
        new_y = max(0, min(GRID_SIZE - 1, new_y))
        
        self.x = new_x
        self.y = new_y
        self.last_action = action
        
        return self.x, self.y
    
    def _apply_action(self, action: int) -> Tuple[int, int]:
        """Apply a specific action (0-4)."""
        if action == 0:  # Up
            return self.x, self.y - 1
        elif action == 1:  # Down
            return self.x, self.y + 1
        elif action == 2:  # Left
            return self.x - 1, self.y
        elif action == 3:  # Right
            return self.x + 1, self.y
        elif action == 4:  # Interact (stay in place)
            return self.x, self.y
        else:
            return self.x, self.y
    
    def _random_move(self) -> Tuple[int, int]:
        """Random walk movement."""
        dx = random.choice([-1, 0, 1])
        dy = random.choice([-1, 0, 1])
        return self.x + dx, self.y + dy
    
    def eat(self, food_energy: float = FOOD_ENERGY_VALUE) -> float:
        """
        Agent consumes food and gains energy.
        
        Args:
            food_energy: Energy value of the food consumed
            
        Returns:
            Energy gained
        """
        if not self.alive:
            return 0
            
        energy_gained = min(food_energy, MAX_AGENT_ENERGY - self.energy)
        self.energy += energy_gained
        return energy_gained
    
    def share_resource(self, target_agent: 'Agent') -> bool:
        """
        Share energy with another agent (cooperative behavior).
        
        Args:
            target_agent: The agent to share with
            
        Returns:
            True if sharing occurred, False otherwise
        """
        if not self.alive or not target_agent.alive:
            return False
            
        # Only share if target is low on energy and we have enough
        if target_agent.energy < SHARE_THRESHOLD and self.energy > SHARE_THRESHOLD + SHARE_COST:
            share_amount = 10
            self.energy -= SHARE_COST
            target_agent.energy = min(MAX_AGENT_ENERGY, target_agent.energy + share_amount)
            return True
        return False
    
    def attack(self, target_agent: 'Agent') -> bool:
        """
        Attack another agent to steal energy (aggressive behavior).
        
        Args:
            target_agent: The agent to attack
            
        Returns:
            True if attack occurred, False otherwise
        """
        if not self.alive or not target_agent.alive:
            return False
            
        # Attack costs energy but can steal from target
        if self.energy > ATTACK_COST:
            self.energy -= ATTACK_COST
            stolen = min(15, target_agent.energy * 0.3)  # Steal 30% of target's energy
            target_agent.energy -= stolen
            self.energy = min(MAX_AGENT_ENERGY, self.energy + stolen)
            
            # Target dies if energy too low
            if target_agent.energy <= 0:
                target_agent.alive = False
            return True
        return False
    
    def update(self):
        """Update agent state each tick."""
        if not self.alive:
            return
            
        # Energy decay
        self.energy -= ENERGY_DECAY_RATE
        
        # Agent dies if energy depleted
        if self.energy <= 0:
            self.alive = False
        else:
            self.ticks_survived += 1
    
    def get_observation(self, grid: np.ndarray, food_grid: np.ndarray) -> np.ndarray:
        """
        Get the agent's observation (vision grid + energy level).
        
        Args:
            grid: Grid of agent positions
            food_grid: Grid of food positions
            
        Returns:
            Flattened observation array: [vision_grid (5x5), energy_normalized]
        """
        vision_size = VISION_RANGE * 2 + 1
        observation = np.zeros((vision_size, vision_size, 2))
        
        # Extract vision grid
        for dy in range(-VISION_RANGE, VISION_RANGE + 1):
            for dx in range(-VISION_RANGE, VISION_RANGE + 1):
                vx = self.x + dx
                vy = self.y + dy
                
                if 0 <= vx < GRID_SIZE and 0 <= vy < GRID_SIZE:
                    observation[dy + VISION_RANGE, dx + VISION_RANGE, 0] = grid[vy, vx]
                    observation[dy + VISION_RANGE, dx + VISION_RANGE, 1] = food_grid[vy, vx]
        
        # Flatten and add normalized energy
        vision_flat = observation.flatten()
        energy_normalized = self.energy / MAX_AGENT_ENERGY
        
        return np.concatenate([vision_flat, [energy_normalized]])
    
    def distance_to(self, other: 'Agent') -> float:
        """Calculate Euclidean distance to another agent."""
        return np.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)


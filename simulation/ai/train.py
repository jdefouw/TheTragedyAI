"""
Training loop for DQN agents with cooperative and aggressive reward functions.
"""

import os
import random
import numpy as np
import torch
import torch.optim as optim
from typing import Dict, List
from collections import deque

from config import (
    BATCH_SIZE, LEARNING_RATE, GAMMA, EPSILON_START, EPSILON_END, EPSILON_DECAY,
    GRID_SIZE, INITIAL_AGENT_COUNT, MAX_TICKS
)
from main import SimulationManager
from agent import Agent
from model import DQN, ReplayBuffer, save_model, export_to_onnx


class RewardFunction:
    """Defines reward functions for different strategies."""
    
    @staticmethod
    def aggressive_reward(agent: Agent, action: int, prev_energy: float, 
                          food_eaten: bool, attack_success: bool, died: bool) -> float:
        """
        Aggressive reward function: rewards eating and stealing.
        
        Returns:
            Reward value
        """
        reward = 0.0
        
        if food_eaten:
            reward += 10.0
        if attack_success:
            reward += 5.0
        if died:
            reward -= 1.0
        
        # Small reward for energy increase
        energy_change = agent.energy - prev_energy
        reward += energy_change * 0.1
        
        return reward
    
    @staticmethod
    def cooperative_reward(agent: Agent, action: int, prev_energy: float,
                           food_eaten: bool, share_success: bool, steal_attempt: bool, died: bool) -> float:
        """
        Cooperative reward function: rewards eating and sharing, penalizes stealing.
        
        Returns:
            Reward value
        """
        reward = 0.0
        
        if food_eaten:
            reward += 10.0
        if share_success:
            reward += 5.0
        if steal_attempt:
            reward -= 10.0
        if died:
            reward -= 1.0
        
        # Small reward for energy increase
        energy_change = agent.energy - prev_energy
        reward += energy_change * 0.1
        
        return reward


class DQNTrainer:
    """Trains DQN agents in the simulation environment."""
    
    def __init__(self, strategy_type: str = 'Cooperative_DQN', resource_density: float = 0.20,
                 device: str = 'cuda' if torch.cuda.is_available() else 'cpu'):
        """
        Initialize trainer.
        
        Args:
            strategy_type: 'Cooperative_DQN' or 'Aggressive_PPO' (treated as DQN)
            resource_density: Resource density for training
            device: 'cuda' or 'cpu'
        """
        self.strategy_type = strategy_type
        self.resource_density = resource_density
        self.device = device
        
        # Determine reward function
        if 'Cooperative' in strategy_type:
            self.reward_fn = RewardFunction.cooperative_reward
        else:
            self.reward_fn = RewardFunction.aggressive_reward
        
        # Initialize model
        vision_size = 5 * 5 * 2 + 1  # 5x5 grid, 2 channels, + energy
        self.model = DQN(input_size=vision_size).to(device)
        self.target_model = DQN(input_size=vision_size).to(device)
        self.target_model.load_state_dict(self.model.state_dict())
        
        # Optimizer and replay buffer
        self.optimizer = optim.Adam(self.model.parameters(), lr=LEARNING_RATE)
        self.replay_buffer = ReplayBuffer(capacity=10000)
        
        # Training state
        self.epsilon = EPSILON_START
        self.training_step = 0
        self.episode_rewards = deque(maxlen=100)
        
        # Checkpoint directory
        os.makedirs('checkpoints', exist_ok=True)
    
    def train_episode(self, max_steps: int = MAX_TICKS) -> Dict[str, float]:
        """
        Train for one episode.
        
        Args:
            max_steps: Maximum steps per episode
            
        Returns:
            Episode statistics
        """
        # Create simulation
        sim = SimulationManager(
            resource_density=self.resource_density,
            headless=True,
            agent_strategy=self.strategy_type,
            machine_id='trainer'
        )
        
        # Track rewards for all agents
        agent_rewards = {agent.agent_id: [] for agent in sim.agents}
        agent_prev_energy = {agent.agent_id: agent.energy for agent in sim.agents}
        agent_states = {}
        
        episode_reward = 0.0
        steps = 0
        
        while sim.running and steps < max_steps:
            steps += 1
            
            # Store previous states
            for agent in sim.agents:
                if agent.alive:
                    agent_states[agent.agent_id] = agent.get_observation(
                        sim.agent_grid, sim.food_grid.astype(float)
                    )
            
            # Update simulation
            sim.update()
            
            # Calculate rewards and store experiences
            for agent in sim.agents:
                if agent.agent_id not in agent_states:
                    continue
                
                # Determine what happened
                food_eaten = agent.energy > agent_prev_energy[agent.agent_id]
                died = not agent.alive and agent_prev_energy[agent.agent_id] > 0
                
                # Simplified: check if action was interact (action 4)
                action = agent.last_action if agent.last_action is not None else 0
                
                # Calculate reward
                reward = self.reward_fn(
                    agent, action, agent_prev_energy[agent.agent_id],
                    food_eaten, False, False, died
                )
                
                agent_rewards[agent.agent_id].append(reward)
                episode_reward += reward
                
                # Store experience if agent is still alive
                if agent.alive:
                    next_state = agent.get_observation(
                        sim.agent_grid, sim.food_grid.astype(float)
                    )
                    state = agent_states[agent.agent_id]
                    
                    self.replay_buffer.push(
                        state, action, reward, next_state, False
                    )
                else:
                    # Terminal state
                    if agent.agent_id in agent_states:
                        state = agent_states[agent.agent_id]
                        next_state = np.zeros_like(state)
                        self.replay_buffer.push(
                            state, action, reward, next_state, True
                        )
                
                agent_prev_energy[agent.agent_id] = agent.energy
            
            # Train on batch if buffer is large enough
            if len(self.replay_buffer) > BATCH_SIZE:
                self._train_step()
            
            # Update epsilon
            self.epsilon = max(EPSILON_END, self.epsilon * EPSILON_DECAY)
        
        # Update target network periodically
        if self.training_step % 100 == 0:
            self.target_model.load_state_dict(self.model.state_dict())
        
        self.episode_rewards.append(episode_reward)
        
        return {
            'episode_reward': episode_reward,
            'steps': steps,
            'epsilon': self.epsilon,
            'avg_reward': np.mean(self.episode_rewards) if self.episode_rewards else 0.0
        }
    
    def _train_step(self):
        """Perform one training step."""
        if len(self.replay_buffer) < BATCH_SIZE:
            return
        
        # Sample batch
        states, actions, rewards, next_states, dones = self.replay_buffer.sample(BATCH_SIZE)
        states = states.to(self.device)
        actions = actions.to(self.device)
        rewards = rewards.to(self.device)
        next_states = next_states.to(self.device)
        dones = dones.to(self.device)
        
        # Current Q values
        q_values = self.model(states).gather(1, actions.unsqueeze(1))
        
        # Next Q values from target network
        with torch.no_grad():
            next_q_values = self.target_model(next_states).max(1)[0].detach()
            target_q_values = rewards + (GAMMA * next_q_values * ~dones)
        
        # Compute loss
        loss = torch.nn.functional.mse_loss(q_values.squeeze(), target_q_values)
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        self.training_step += 1
    
    def train(self, num_episodes: int = 1000, save_interval: int = 100):
        """
        Train the model for multiple episodes.
        
        Args:
            num_episodes: Number of episodes to train
            save_interval: Save checkpoint every N episodes
        """
        print(f"Starting training: {self.strategy_type}")
        print(f"Device: {self.device}")
        print(f"Resource density: {self.resource_density}")
        
        for episode in range(num_episodes):
            stats = self.train_episode()
            
            if (episode + 1) % 10 == 0:
                print(f"Episode {episode + 1}/{num_episodes} | "
                      f"Reward: {stats['episode_reward']:.2f} | "
                      f"Avg: {stats['avg_reward']:.2f:.2f} | "
                      f"Epsilon: {stats['epsilon']:.3f}")
            
            # Save checkpoint
            if (episode + 1) % save_interval == 0:
                checkpoint_path = f"checkpoints/{self.strategy_type}_ep{episode+1}.pth"
                save_model(self.model, checkpoint_path)
        
        # Final save
        final_path = f"checkpoints/{self.strategy_type}_final.pth"
        save_model(self.model, final_path)
        
        # Export to ONNX
        vision_size = 5 * 5 * 2 + 1
        onnx_path = f"checkpoints/{self.strategy_type}.onnx"
        export_to_onnx(self.model, onnx_path, vision_size)
        
        print(f"Training complete! Model saved to {final_path}")
        print(f"ONNX model exported to {onnx_path}")


if __name__ == "__main__":
    # Example: Train a cooperative agent
    trainer = DQNTrainer(
        strategy_type='Cooperative_DQN',
        resource_density=0.20
    )
    trainer.train(num_episodes=100, save_interval=50)


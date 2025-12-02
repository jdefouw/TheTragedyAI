"""
Deep Q-Network (DQN) model for agent decision making.
Supports Genetic Algorithm weight injection/extraction.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import json
import base64
import numpy as np
from typing import Dict, Any, List
from config import VISION_RANGE, ACTION_SPACE, MAX_AGENT_ENERGY


class DQN(nn.Module):
    """
    Deep Q-Network for agent decision making.
    Input: Vision grid (5x5x2) + energy level
    Output: Q-values for 5 actions
    """
    
    def __init__(self, input_size: int = None, hidden_size: int = 128):
        """
        Initialize DQN model.
        
        Args:
            input_size: Size of input observation (auto-calculated if None)
            hidden_size: Size of hidden layers
        """
        super(DQN, self).__init__()
        
        # Calculate input size: (vision_range*2+1)^2 * 2 channels + 1 energy
        if input_size is None:
            vision_size = (VISION_RANGE * 2 + 1) ** 2
            input_size = vision_size * 2 + 1  # 2 channels (agents, food) + energy
        
        self.input_size = input_size
        self.hidden_size = hidden_size
        
        # Neural network layers
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, ACTION_SPACE)
        
        # Dropout for regularization
        self.dropout = nn.Dropout(0.2)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass."""
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)
        return x
    
    def predict_action(self, observation: torch.Tensor, epsilon: float = 0.0) -> int:
        """Predict action using epsilon-greedy policy."""
        if torch.rand(1).item() < epsilon:
            return torch.randint(0, ACTION_SPACE, (1,)).item()
        
        self.eval()
        with torch.no_grad():
            if observation.dim() == 1:
                observation = observation.unsqueeze(0)
            q_values = self.forward(observation)
            action = q_values.argmax(dim=1).item()
        return action

    # --- GENETIC ALGORITHM METHODS ---

    def get_weights_as_dict(self) -> Dict[str, Any]:
        """
        Export weights as a dictionary suitable for JSON serialization.
        Used for storing genomes in Supabase.
        """
        state_dict = self.state_dict()
        weights = {}
        for key, value in state_dict.items():
            # Convert tensor to list
            weights[key] = value.cpu().numpy().tolist()
        return weights

    def load_weights_from_dict(self, weights: Dict[str, Any]):
        """
        Load weights from a dictionary (JSON compatible).
        Used for injecting genomes into the agent.
        """
        state_dict = {}
        for key, value in weights.items():
            state_dict[key] = torch.tensor(value)
        self.load_state_dict(state_dict)

    def mutate(self, mutation_rate: float = 0.01, sigma: float = 0.1):
        """
        Apply Gaussian mutation to weights.
        
        Args:
            mutation_rate: Probability of mutating a specific weight
            sigma: Standard deviation of the Gaussian noise
        """
        with torch.no_grad():
            for param in self.parameters():
                # Create mutation mask (1 = mutate, 0 = keep)
                mask = (torch.rand_like(param) < mutation_rate).float()
                # Create noise
                noise = torch.randn_like(param) * sigma
                # Apply mutation
                param.add_(mask * noise)


class ReplayBuffer:
    """Experience replay buffer for DQN training."""
    
    def __init__(self, capacity: int = 10000):
        """Initialize replay buffer."""
        self.capacity = capacity
        self.buffer = []
        self.position = 0
    
    def push(self, state, action, reward, next_state, done):
        """Add experience to buffer."""
        if len(self.buffer) < self.capacity:
            self.buffer.append(None)
        self.buffer[self.position] = (state, action, reward, next_state, done)
        self.position = (self.position + 1) % self.capacity
    
    def sample(self, batch_size: int):
        """Sample a batch of experiences."""
        import random
        batch = random.sample(self.buffer, min(batch_size, len(self.buffer)))
        states, actions, rewards, next_states, dones = zip(*batch)
        
        return (
            torch.FloatTensor(states),
            torch.LongTensor(actions),
            torch.FloatTensor(rewards),
            torch.FloatTensor(next_states),
            torch.BoolTensor(dones)
        )
    
    def __len__(self):
        return len(self.buffer)


def save_model(model: nn.Module, filepath: str):
    """Save model to file."""
    torch.save(model.state_dict(), filepath)
    print(f"Model saved to {filepath}")


def load_model(model: nn.Module, filepath: str, device: str = 'cpu'):
    """Load model from file."""
    model.load_state_dict(torch.load(filepath, map_location=device))
    model.eval()
    print(f"Model loaded from {filepath}")
    return model


def export_to_onnx(model: nn.Module, filepath: str, input_size: int):
    """Export PyTorch model to ONNX format."""
    model.eval()
    dummy_input = torch.randn(1, input_size)
    
    torch.onnx.export(
        model,
        dummy_input,
        filepath,
        export_params=True,
        opset_version=11,
        do_constant_folding=True,
        input_names=['observation'],
        output_names=['q_values'],
        dynamic_axes={
            'observation': {0: 'batch_size'},
            'q_values': {0: 'batch_size'}
        }
    )
    print(f"Model exported to ONNX: {filepath}")

"""
Configuration constants for the Tragedy of the Commons simulation.
"""

# Display settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_SIZE = 40  # Number of cells in grid (grid will be GRID_SIZE x GRID_SIZE)
CELL_SIZE = SCREEN_WIDTH // GRID_SIZE

# Simulation parameters
INITIAL_AGENT_COUNT = 40  # Increased for better statistical significance
INITIAL_AGENT_ENERGY = 100
MAX_AGENT_ENERGY = 200
ENERGY_DECAY_RATE = 0.5  # Energy lost per tick
FOOD_ENERGY_VALUE = 20

# Resource density options (Granular steps for Scarcity Window analysis)
# Focused around the predicted 15-35% critical threshold
RESOURCE_DENSITY_OPTIONS = [
    0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50
]

# Agent behavior
VISION_RANGE = 2  # 5x5 grid (2 cells in each direction)
SHARE_THRESHOLD = 30  # Energy below which agent will accept sharing
ATTACK_COST = 5  # Energy cost to attack another agent
SHARE_COST = 3  # Energy cost to share with another agent

# AI/Neural Network settings
NEURAL_STRATEGY_TYPES = ['Cooperative_DQN', 'Aggressive_PPO', 'Mixed', 'Random_Walk']
ACTION_SPACE = 5  # Up, Down, Left, Right, Interact

# Training parameters
BATCH_SIZE = 32
LEARNING_RATE = 0.001
GAMMA = 0.99  # Discount factor
EPSILON_START = 1.0
EPSILON_END = 0.01
EPSILON_DECAY = 0.995

# GPU/Performance settings
HEADLESS_MODE = True  # Set to False for visual debugging
MAX_TICKS = 2000  # Sufficient duration to observe convergence
LOG_INTERVAL = 50  # Log time-series snapshot every N ticks

# Colors (for visualization when not headless)
COLOR_AGENT = (100, 150, 255)
COLOR_FOOD = (50, 200, 50)
COLOR_COOPERATIVE = (50, 200, 100)
COLOR_AGGRESSIVE = (200, 50, 50)

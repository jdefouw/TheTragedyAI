"""
Web game for human vs AI validation.
Compiled to WebAssembly using pygbag.
Connects to Supabase to fetch the latest evolved AI champion.
"""

import sys
import os
import json
import asyncio

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pygame
import numpy as np
import random
from typing import Optional, List, Dict, Any

# Import simulation components
from simulation.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, GRID_SIZE, CELL_SIZE,
    INITIAL_AGENT_COUNT, RESOURCE_DENSITY_OPTIONS,
    COLOR_AGENT, COLOR_FOOD, COLOR_COOPERATIVE, COLOR_AGGRESSIVE,
    MAX_AGENT_ENERGY, VISION_RANGE
)
from simulation.agent import Agent
from simulation.logger import log_human_match
from simulation.ai.model import DQN

# Player mode flag
PLAYER_MODE = True

# Game state
class GameState:
    MENU = 0
    PLAYING = 1
    GAME_OVER = 2

# Global game state
game_state = GameState.MENU
simulation = None
player_agent = None
ai_agents = []
player_survival_time = 0
ai_survival_times = []
difficulty_level = "Medium"

# Graphics - Emojis
EMOJI_PLAYER = "🧑"
EMOJI_COOP = "🤖" 
EMOJI_AGGRESSIVE = "👹"
EMOJI_FOOD = "🍎"

# AI Champion Data
champion_genome_weights = None
champion_metadata = {
    "generation_id": "Loading...",
    "fitness": 0.0,
    "created_at": "Unknown"
}

# QR code placeholder
DASHBOARD_URL = "https://simulate-dashboard.defouw.ca"


# --- SUPABASE FETCHING (Async for WASM) ---

from simulation.logger import supabase, init_supabase

def fetch_latest_champion():
    """Fetch the best genome from the latest completed generation."""
    global champion_genome_weights, champion_metadata
    
    try:
        print("Fetching champion model...")
        init_supabase()
        
        # 1. Get latest completed generation
        gen_res = supabase.table("simulation_generations") \
            .select("*") \
            .eq("status", "completed") \
            .order("id", desc=True) \
            .limit(1) \
            .execute()
            
        if not gen_res.data:
            print("No completed generations found. Using default AI.")
            champion_metadata["generation_id"] = "Random (Gen 0)"
            return
            
        generation = gen_res.data[0]
        gen_id = generation['id']
        
        # 2. Get best genome from that generation
        genome_res = supabase.table("simulation_genomes") \
            .select("*") \
            .eq("generation_id", gen_id) \
            .order("fitness_score", desc=True) \
            .limit(1) \
            .execute()
            
        if not genome_res.data:
            print("No genomes found for generation.")
            return
            
        genome = genome_res.data[0]
        champion_genome_weights = genome['weights']
        
        # Update metadata
        created_at = generation['created_at'].split('T')[0] # Simple date
        champion_metadata = {
            "generation_id": str(gen_id),
            "fitness": float(genome['fitness_score']),
            "created_at": created_at
        }
        print(f"Loaded Champion: Gen {gen_id}, Fitness {genome['fitness_score']}")
        
    except Exception as e:
        print(f"Failed to fetch champion: {e}")
        champion_metadata["generation_id"] = "Offline (Random)"

# --- SIMULATION LOGIC ---

def create_simulation(difficulty: str = "Medium"):
    """Create a new simulation with player and AI agents."""
    global simulation, player_agent, ai_agents
    
    # Determine resource density based on difficulty
    density_map = {
        "Easy": 0.50,
        "Medium": 0.20,
        "Hard": 0.10,
        "Scientist": 0.05
    }
    resource_density = density_map.get(difficulty, 0.20)
    
    # Create a simplified simulation
    simulation = {
        'agents': [],
        'food_grid': np.zeros((GRID_SIZE, GRID_SIZE), dtype=bool),
        'agent_grid': np.zeros((GRID_SIZE, GRID_SIZE), dtype=int),
        'tick': 0,
        'resource_density': resource_density,
        'running': True
    }
    
    # Spawn player agent
    x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
    player_agent = Agent(x, y, strategy_type='Random_Walk', agent_id=0)
    player_agent.energy = INITIAL_AGENT_ENERGY
    simulation['agents'].append(player_agent)
    
    # Initialize Champion AI Model
    champion_model = None
    if champion_genome_weights:
        try:
            champion_model = DQN()
            champion_model.load_weights_from_dict(champion_genome_weights)
        except Exception as e:
            print(f"Error loading champion weights: {e}")
            champion_model = None

    # Spawn AI agents
    ai_agents = []
    positions = set([(x, y)])
    for i in range(INITIAL_AGENT_COUNT - 1):
        while True:
            x = random.randint(0, GRID_SIZE - 1)
            y = random.randint(0, GRID_SIZE - 1)
            if (x, y) not in positions:
                positions.add((x, y))
                # Strategy name for display
                strat_name = f"Gen {champion_metadata['generation_id']}" if champion_model else "Random AI"
                
                agent = Agent(x, y, strategy_type=strat_name, agent_id=i + 1)
                agent.energy = INITIAL_AGENT_ENERGY
                
                # Inject Brain
                if champion_model:
                    agent.model = champion_model
                
                simulation['agents'].append(agent)
                ai_agents.append(agent)
                break
    
    # Spawn food
    spawn_food(resource_density)
    
    return simulation


def spawn_food(density: float):
    """Spawn food on the grid."""
    simulation['food_grid'] = np.zeros((GRID_SIZE, GRID_SIZE), dtype=bool)
    total_cells = GRID_SIZE * GRID_SIZE
    num_food = int(total_cells * density)
    
    food_positions = random.sample(
        [(x, y) for x in range(GRID_SIZE) for y in range(GRID_SIZE)],
        min(num_food, total_cells)
    )
    
    for x, y in food_positions:
        simulation['food_grid'][y, x] = True


def update_simulation():
    """Update simulation state."""
    global game_state, player_survival_time, ai_survival_times
    
    if not simulation or not simulation['running']:
        return
    
    simulation['tick'] += 1
    simulation['agent_grid'] = np.zeros((GRID_SIZE, GRID_SIZE), dtype=int)
    
    # Update player agent (controlled by keyboard)
    if player_agent and player_agent.alive:
        simulation['agent_grid'][player_agent.y, player_agent.x] = 1
        player_survival_time = simulation['tick']
        
        # Check for food
        if simulation['food_grid'][player_agent.y, player_agent.x]:
            player_agent.eat()
            simulation['food_grid'][player_agent.y, player_agent.x] = False
        
        player_agent.update()
    
    # Update AI agents
    for agent in ai_agents:
        if not agent.alive:
            continue
        
        simulation['agent_grid'][agent.y, agent.x] = agent.agent_id + 1
        
        # Get AI action
        action = 0
        if agent.model:
             # Use the injected DQN model
             import torch
             obs = agent.get_observation(
                simulation['agent_grid'], simulation['food_grid'].astype(float)
             )
             obs_tensor = torch.FloatTensor(obs)
             action = agent.model.predict_action(obs_tensor)
        else:
             # Fallback to random
             action = random.randint(0, 4)
        
        agent.move(action)
        
        # Check for food
        if simulation['food_grid'][agent.y, agent.x]:
            agent.eat()
            simulation['food_grid'][agent.y, agent.x] = False
            
        # Simple Interaction Logic (if action is 'Interact')
        if action == 4:
            pass
        
        agent.update()
    
    # Respawn food periodically
    if simulation['tick'] % 50 == 0:
        spawn_food(simulation['resource_density'])
    
    # Check game over
    if player_agent and not player_agent.alive:
        simulation['running'] = False
        game_state = GameState.GAME_OVER
        # Calculate AI survival times
        ai_survival_times = [a.ticks_survived for a in ai_agents if not a.alive]
        if not ai_survival_times:
            ai_survival_times = [simulation['tick']] * len(ai_agents)


def draw_debug_lines(screen):
    """Draw lines between cooperating/fighting agents."""
    if not simulation:
        return
    
    # Draw green lines for nearby agents (cooperation visualization)
    for agent in simulation['agents']:
        if not agent.alive:
            continue
        for other in simulation['agents']:
            if other.agent_id == agent.agent_id or not other.alive:
                continue
            distance = agent.distance_to(other)
            if distance <= 2.0:
                color = COLOR_COOPERATIVE # Default to showing 'connection'
                start_pos = (agent.x * CELL_SIZE + CELL_SIZE // 2, agent.y * CELL_SIZE + CELL_SIZE // 2)
                end_pos = (other.x * CELL_SIZE + CELL_SIZE // 2, other.y * CELL_SIZE + CELL_SIZE // 2)
                pygame.draw.line(screen, color, start_pos, end_pos, 1)


def draw_game(screen, font, emoji_font):
    """Draw the game screen with emojis."""
    screen.fill((30, 30, 35)) # Darker modern bg
    
    if not simulation:
        return
    
    # Draw food
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            if simulation['food_grid'][y, x]:
                text = emoji_font.render(EMOJI_FOOD, True, (255, 255, 255))
                rect = text.get_rect(center=(x * CELL_SIZE + CELL_SIZE//2, y * CELL_SIZE + CELL_SIZE//2))
                screen.blit(text, rect)
    
    # Draw debug lines
    draw_debug_lines(screen)
    
    # Draw agents
    for agent in simulation['agents']:
        if not agent.alive:
            continue
        
        emoji = EMOJI_COOP
        if agent.agent_id == 0:  # Player
            emoji = EMOJI_PLAYER
        elif agent.strategy_type == 'Aggressive_PPO':
            emoji = EMOJI_AGGRESSIVE
        
        # Draw emoji
        text = emoji_font.render(emoji, True, (255, 255, 255))
        x_pos = agent.x * CELL_SIZE + CELL_SIZE // 2
        y_pos = agent.y * CELL_SIZE + CELL_SIZE // 2
        rect = text.get_rect(center=(x_pos, y_pos))
        screen.blit(text, rect)
        
        # Draw energy bar (Cleaner look)
        bar_width = CELL_SIZE - 4
        bar_height = 3
        energy_ratio = max(0, agent.energy / MAX_AGENT_ENERGY)
        
        bar_color = (0, 255, 100) if energy_ratio > 0.5 else (255, 100, 0)
        if energy_ratio < 0.2: bar_color = (255, 0, 0)
        
        bar_bg = (50, 50, 50)
        
        pygame.draw.rect(screen, bar_bg, (x_pos - bar_width//2, y_pos - CELL_SIZE//2 - 6, bar_width, bar_height))
        pygame.draw.rect(screen, bar_color, (x_pos - bar_width//2, y_pos - CELL_SIZE//2 - 6, int(bar_width * energy_ratio), bar_height))
    
    # Draw HUD (Modern)
    if player_agent:
        # Top bar background
        pygame.draw.rect(screen, (20, 20, 25), (0, 0, SCREEN_WIDTH, 50))
        pygame.draw.line(screen, (50, 50, 60), (0, 50), (SCREEN_WIDTH, 50))
        
        # Stats
        energy_text = font.render(f"⚡ Energy: {int(player_agent.energy)}", True, (255, 255, 255))
        time_text = font.render(f"⏱️ Time: {simulation['tick']}", True, (255, 255, 255))
        opp_text = font.render(f"🆚 {champion_metadata['generation_id']}", True, (150, 200, 255))
        
        screen.blit(energy_text, (20, 15))
        screen.blit(time_text, (200, 15))
        screen.blit(opp_text, (SCREEN_WIDTH - 250, 15))


def draw_menu(screen, font, large_font):
    """Draw the main menu."""
    # Modern gradient-like background
    screen.fill((25, 25, 30))
    
    # Title
    title = large_font.render("The Tragedy of the Commons AI", True, (255, 255, 255))
    title_shadow = large_font.render("The Tragedy of the Commons AI", True, (0, 0, 0))
    
    center_x = SCREEN_WIDTH // 2
    screen.blit(title_shadow, title_shadow.get_rect(center=(center_x + 2, 102)))
    screen.blit(title, title.get_rect(center=(center_x, 100)))
    
    subtitle = font.render("Can you survive against Evolved Intelligence?", True, (150, 150, 160))
    screen.blit(subtitle, subtitle.get_rect(center=(center_x, 150)))
    
    # AI Stats Card
    card_y = 220
    card_width = 500
    card_height = 140
    card_rect = pygame.Rect(center_x - card_width//2, card_y, card_width, card_height)
    
    pygame.draw.rect(screen, (35, 35, 40), card_rect, border_radius=15)
    pygame.draw.rect(screen, (60, 60, 70), card_rect, 2, border_radius=15)
    
    header = font.render("Current Champion", True, (100, 200, 255))
    screen.blit(header, header.get_rect(center=(center_x, card_y + 25)))
    
    gen_txt = font.render(f"Generation: {champion_metadata['generation_id']}", True, (200, 200, 200))
    fit_txt = font.render(f"Fitness Score: {champion_metadata['fitness']:.1f}", True, (200, 200, 200))
    date_txt = font.render(f"Evolved: {champion_metadata['created_at']}", True, (150, 150, 150))
    
    screen.blit(gen_txt, (card_rect.x + 40, card_y + 60))
    screen.blit(fit_txt, (card_rect.x + 40, card_y + 90))
    screen.blit(date_txt, (card_rect.right - date_txt.get_width() - 40, card_y + 90))
    
    # Controls
    ctrl_y = 400
    wasd_txt = font.render("Controls: WASD or Arrow Keys to Move", True, (120, 120, 120))
    screen.blit(wasd_txt, wasd_txt.get_rect(center=(center_x, ctrl_y)))
    
    # Start Button
    btn_rect = pygame.Rect(center_x - 100, 460, 200, 60)
    pygame.draw.rect(screen, (50, 150, 80), btn_rect, border_radius=30)
    pygame.draw.rect(screen, (80, 180, 110), btn_rect, 2, border_radius=30)
    
    start_txt = font.render("PLAY", True, (255, 255, 255))
    screen.blit(start_txt, start_txt.get_rect(center=btn_rect.center))


def draw_game_over(screen, font, large_font):
    """Draw the game over screen with statistics."""
    screen.fill((20, 20, 25))
    
    if not simulation:
        return
    
    # Stats
    ai_avg = np.mean(ai_survival_times) if ai_survival_times else 0
    winner = "Human" if player_survival_time > ai_avg else "AI"
    color = (100, 255, 100) if winner == "Human" else (255, 100, 100)
    
    title = large_font.render(f"{winner} Wins!", True, color)
    screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 150)))
    
    # Score Box
    box_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, 220, 400, 150)
    pygame.draw.rect(screen, (30, 30, 35), box_rect, border_radius=10)
    
    p_score = font.render(f"You: {player_survival_time} ticks", True, (255, 255, 255))
    ai_score = font.render(f"AI Average: {int(ai_avg)} ticks", True, (200, 200, 200))
    
    screen.blit(p_score, p_score.get_rect(center=(SCREEN_WIDTH//2, 260)))
    screen.blit(ai_score, ai_score.get_rect(center=(SCREEN_WIDTH//2, 310)))
    
    restart_txt = font.render("Press SPACE to Restart", True, (150, 150, 150))
    screen.blit(restart_txt, restart_txt.get_rect(center=(SCREEN_WIDTH//2, 450)))
    
    # Log result (non-blocking attempt)
    try:
        log_human_match({
            'player_name': 'Anonymous',
            'human_survival_time': player_survival_time,
            'ai_average_survival_time': int(ai_avg),
            'winner': winner,
            'difficulty_level': difficulty_level
        })
    except Exception:
        pass


async def main():
    """Main game loop."""
    global game_state, simulation, player_agent, difficulty_level
    
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Tragedy of the Commons - Human vs AI")
    clock = pygame.time.Clock()
    
    # Fonts - Try to use system fonts that support emojis or fallback
    try:
        # Segoe UI Emoji (Windows), Apple Color Emoji (Mac), Noto Color Emoji (Linux)
        emoji_font = pygame.font.SysFont("Segoe UI Emoji", CELL_SIZE - 2)
    except:
        emoji_font = pygame.font.Font(None, CELL_SIZE)
        
    font = pygame.font.SysFont("Arial", 24)
    large_font = pygame.font.SysFont("Arial", 48, bold=True)
    
    print("Checking for updates...")
    fetch_latest_champion()
    
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if game_state == GameState.MENU:
                    if event.key == pygame.K_SPACE:
                        game_state = GameState.PLAYING
                        create_simulation(difficulty_level)
                elif game_state == GameState.GAME_OVER:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_r:
                        game_state = GameState.MENU
        
        # Handle player input (WASD + Arrows)
        if game_state == GameState.PLAYING and player_agent and player_agent.alive:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                player_agent.move(0)
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                player_agent.move(1)
            elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_agent.move(2)
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player_agent.move(3)
            elif keys[pygame.K_SPACE]:
                player_agent.move(4)  # Interact
        
        # Update simulation
        if game_state == GameState.PLAYING:
            update_simulation()
        
        # Draw
        if game_state == GameState.MENU:
            draw_menu(screen, font, large_font)
        elif game_state == GameState.PLAYING:
            draw_game(screen, font, emoji_font)
        elif game_state == GameState.GAME_OVER:
            draw_game_over(screen, font, large_font)
        
        pygame.display.flip()
        clock.tick(60)
        
        await asyncio.sleep(0)
    
    pygame.quit()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

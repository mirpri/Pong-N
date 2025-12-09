import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import random
from collections import deque

# --- 1. DQN AGENT AND NETWORK DEFINITIONS ---

# The architecture of the Neural Network
class QNetwork(nn.Module):
    def __init__(self, state_dim, action_dim):
        super().__init__()
        # Simple two-layer network
        self.net = nn.Sequential(
            nn.Linear(state_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, action_dim)
        )

    def forward(self, x):
        return self.net(x)

class OnlineDQNAgent:
    def __init__(self, state_dim, action_dim, gamma=0.99, lr=1e-4, buffer_size=5000):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon = 1.0  # Start with high exploration
        self.epsilon_min = 0.05
        self.epsilon_decay = 0.99995  # Very slow decay for continuous online learning
        self.memory = deque(maxlen=buffer_size)
        
        self.policy_net = QNetwork(state_dim, action_dim).float()
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=lr)
        self.loss_fn = nn.MSELoss()

    def act(self, state: np.ndarray):
        """Epsilon-greedy action selection."""
        if random.random() <= self.epsilon:
            return random.randrange(self.action_dim)
        else:
            state_tensor = torch.from_numpy(state).float().unsqueeze(0)
            with torch.no_grad():
                q_values = self.policy_net(state_tensor)
            return torch.argmax(q_values).item()

    def remember(self, state, action, reward, next_state, terminated):
        """Store the transition in replay memory."""
        self.memory.append((state, action, reward, next_state, terminated))

    def replay(self, batch_size):
        """Performs a single training step."""
        if len(self.memory) < batch_size:
            return 
        
        minibatch = random.sample(self.memory, batch_size)
        
        states, actions, rewards, next_states, terminateds = zip(*minibatch)
        
        states = torch.tensor(np.array(states), dtype=torch.float32)
        actions = torch.tensor(actions, dtype=torch.long)
        rewards = torch.tensor(rewards, dtype=torch.float32)
        next_states = torch.tensor(np.array(next_states), dtype=torch.float32)
        terminateds = torch.tensor(terminateds, dtype=torch.bool)

        # Compute Q(s, a)
        current_q_values = self.policy_net(states).gather(1, actions.unsqueeze(1)).squeeze(1)

        # Compute Target Q-value (Bootstrap from self, no separate target network for simplicity)
        with torch.no_grad():
            next_q_values = self.policy_net(next_states).max(1)[0]
            target_q_values = rewards + (self.gamma * next_q_values * (~terminateds))

        # Optimize
        loss = self.loss_fn(current_q_values, target_q_values)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

    def decay_epsilon(self):
        """Decrease epsilon."""
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
        
    def save(self, filename):
        torch.save(self.policy_net.state_dict(), filename)
    
    def load(self, filename):
        self.policy_net.load_state_dict(torch.load(filename))


# --- 2. GLOBAL STATE AND INTEGRATION ---

# State Dimensions: [x, y, vx, vy, my_p] (Simplified input for a single player)
STATE_DIM = 5
# Action Mapping: 0: No move, 1: Right, 2: Left
ACTION_DIM = 3 
BATCH_SIZE = 32 # Must be large enough for replay
MODEL_FILE = "online_dqn_pong.pth"

# Global Variables to maintain state across game calls
global_agent = None
global_last_state = None
global_last_action = None
global_player_id = None
global_game_start = True
PLAYER_PAD_Y_COORD = 700 # P1's Y position (approx)

def initialize_agent():
    """Initialize the agent only once."""
    global global_agent, global_player_id
    
    # Only initialize the first time
    if global_agent is not None:
        return
        
    print("Initializing Online DQN Agent...")
    global_agent = OnlineDQNAgent(STATE_DIM, ACTION_DIM)
    
    # Try loading a previously trained model
    try:
        global_agent.load(MODEL_FILE)
        print(f"Loaded existing model from {MODEL_FILE}. Epsilon: {global_agent.epsilon:.4f}")
    except FileNotFoundError:
        print("No existing model found. Starting fresh training.")

def get_agent_input(state: list, player: int) -> np.ndarray:
    """Extract and format the state for the agent."""
    x, y, vx, vy, a, p1, p2 = state
    # Extract the player's own position
    pad_pos = p1 if player == 1 else p2
    # The agent input is [ball_x, ball_y, ball_vx, ball_vy, my_pad_pos]
    return np.array([x, y, vx, vy, pad_pos], dtype=np.float32)

def calculate_reward(current_state: np.ndarray, last_state: np.ndarray, player: int) -> float:
    """
    Calculate the reward based on the transition between the last state and the current state.
    *** CRITICAL: YOU NEED TO FINE-TUNE THIS REWARD LOGIC ***
    """
    _, last_y, _, last_vy, _ = last_state
    _, current_y, _, current_vy, pad_pos = current_state
    
    reward = -0.005 # Small penalty per step
    
    # 1. Determine if the ball hit the player's side
    if player == 1:
        # P1 is on the bottom (Y=700). Hitting happens when Y is large.
        is_my_turn = last_vy > 0 and current_vy < 0 and last_y < PLAYER_PAD_Y_COORD
        
        if is_my_turn:
            # Check for successful hit (ball changes vertical direction on my side)
            reward += 1.0 # HUGE POSITIVE REWARD for hitting the ball
        
        # Check for loss (ball flies past the target Y)
        if last_y < PLAYER_PAD_Y_COORD and current_y >= PLAYER_PAD_Y_COORD and current_vy > 0:
            reward -= 10.0 # HUGE NEGATIVE REWARD for missing the ball
             
    # 2. Simple movement reward (encourage staying near the ball's X coordinate)
    ball_x = current_state[0]
    distance_to_ball = abs(ball_x - pad_pos)
    reward -= distance_to_ball / 1000.0 # Small penalty for being far from the ball
    
    return reward

def control(state: list, player: int) -> int:
    """
    The main function called by the game loop. It handles both action selection AND training.
    """
    global global_agent, global_last_state, global_last_action, global_player_id, global_game_start
    
    initialize_agent()
    
    # 1. PREPARE CURRENT STATE
    current_agent_input = get_agent_input(state, player)
    
    # Only the first player to call this function needs to be tracked.
    if global_player_id is None:
        global_player_id = player

    # 2. TRAINING/REPLAY STEP (Skip if this is the very first step of the game)
    if global_last_state is not None:
        # Calculate reward based on the transition from last_state to current_agent_input
        reward = calculate_reward(current_agent_input, global_last_state, global_player_id)
        
        # Termination: Assume the episode terminates if the reward is extremely negative (a miss)
        terminated = reward < -5.0
        
        # Store experience
        global_agent.remember(global_last_state, global_last_action, reward, current_agent_input, terminated)
        
        # Perform one optimization step (CRUCIAL: This causes lag)
        global_agent.replay(BATCH_SIZE)
        
        # Slowly decay exploration rate
        global_agent.decay_epsilon()
        
        # Save model occasionally (e.g., every 500 steps)
        if np.random.rand() < 0.002: # Save roughly every 500 steps on average
            global_agent.save(MODEL_FILE)
    
    # 3. ACTION SELECTION
    action_id = global_agent.act(current_agent_input)

    # 4. STORE STATE AND ACTION FOR NEXT STEP
    global_last_state = current_agent_input
    global_last_action = action_id

    # 5. MAP ACTION TO GAME RETURN VALUE
    # 0 -> 0 (No move), 1 -> 1 (Move Right), 2 -> -1 (Move Left)
    if action_id == 0:
        return 0
    elif action_id == 1:
        return 1
    elif action_id == 2:
        return -1
    else:
        return 0 # Should not happen

def control_s(state: list, player: int) -> bool:
    """
    Skill control remains off for the RL agent.
    """
    return False
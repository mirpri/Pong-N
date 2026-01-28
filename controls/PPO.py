import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical

# --- 1. PPO network ---

class ActorCritic(nn.Module):
    def __init__(self, state_dim, action_dim):
        super(ActorCritic, self).__init__()
        # Actor: action probabilities
        self.actor = nn.Sequential(
            nn.Linear(state_dim, 64),
            nn.Tanh(),
            nn.Linear(64, 64),
            nn.Tanh(),
            nn.Linear(64, action_dim),
            nn.Softmax(dim=-1)
        )
        # Critic: state value
        self.critic = nn.Sequential(
            nn.Linear(state_dim, 64),
            nn.Tanh(),
            nn.Linear(64, 64),
            nn.Tanh(),
            nn.Linear(64, 1)
        )

    def forward(self, state):
        value = self.critic(state)
        probs = self.actor(state)
        return probs, value

class PPOAgent:
    def __init__(self, state_dim, action_dim, lr=3e-4, gamma=0.99, K_epochs=4, eps_clip=0.2):
        self.gamma = gamma
        self.eps_clip = eps_clip
        self.K_epochs = K_epochs
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        self.policy = ActorCritic(state_dim, action_dim).float()
        self.optimizer = optim.Adam(self.policy.parameters(), lr=lr)
        self.policy_old = ActorCritic(state_dim, action_dim).float()
        self.policy_old.load_state_dict(self.policy.state_dict())
        
        self.MseLoss = nn.MSELoss()
        
        # Trajectory buffer
        self.states = []
        self.actions = []
        self.logprobs = []
        self.rewards = []
        self.is_terminals = []

    def select_action(self, state):
        state = torch.FloatTensor(state).unsqueeze(0)
        with torch.no_grad():
            probs, _ = self.policy_old(state)
        
        dist = Categorical(probs)
        action = dist.sample()
        
        self.states.append(state)
        self.actions.append(action)
        self.logprobs.append(dist.log_prob(action))
        
        return action.item()

    def update(self):
        # Skip if nothing to update
        if len(self.states) == 0:
            return
            
        # 将存储的数据转换为 tensor
        old_states = torch.cat(self.states, dim=0).detach()
        old_actions = torch.cat(self.actions, dim=0).detach()
        old_logprobs = torch.cat(self.logprobs, dim=0).detach()
        
        # Discounted returns
        rewards = []
        discounted_reward = 0
        for reward, is_terminal in zip(reversed(self.rewards), reversed(self.is_terminals)):
            if is_terminal:
                discounted_reward = 0
            discounted_reward = reward + (self.gamma * discounted_reward)
            rewards.insert(0, discounted_reward)
            
        rewards = torch.FloatTensor(rewards)
        # Normalize rewards for stability
        rewards = (rewards - rewards.mean()) / (rewards.std() + 1e-5)
        
        # Policy updates
        for _ in range(self.K_epochs):
            # 获取当前策略的 log 概率和状态价值
            probs, state_values = self.policy(old_states)
            dist = Categorical(probs)
            logprobs = dist.log_prob(old_actions)
            dist_entropy = dist.entropy()
            
            # Probability ratio r(theta)
            ratios = torch.exp(logprobs - old_logprobs.detach())
            
            # Advantage
            advantages = rewards - state_values.detach().squeeze()
            
            # PPO clipped surrogate objective
            surr1 = ratios * advantages
            surr2 = torch.clamp(ratios, 1-self.eps_clip, 1+self.eps_clip) * advantages
            
            loss = -torch.min(surr1, surr2) + 0.5 * self.MseLoss(state_values.squeeze(), rewards) - 0.01 * dist_entropy
            
            self.optimizer.zero_grad()
            loss.mean().backward()
            self.optimizer.step()
            
        # Sync old policy
        self.policy_old.load_state_dict(self.policy.state_dict())
        
        # Clear buffer
        self.states, self.actions, self.logprobs, self.rewards, self.is_terminals = [], [], [], [], []

    def save(self, checkpoint_path):
        torch.save(self.policy.state_dict(), checkpoint_path)

    def load(self, checkpoint_path):
        try:
            self.policy.load_state_dict(torch.load(checkpoint_path))
            self.policy_old.load_state_dict(self.policy.state_dict())
            return True
        except FileNotFoundError:
            return False

# --- 2. Game logic and reward ---

BOARD_WIDTH = 800
PLAYER_PAD_Y_COORD = 700

def get_target_x(ball_x, ball_y, ball_vx, ball_vy, target_y):
    """Predict landing x with wall bounces."""
    if ball_vy == 0:
        return max(0, min(BOARD_WIDTH, ball_x))
    
    # Time to reach target y
    time_to_target = abs(target_y - ball_y) / abs(ball_vy)
    
    # Horizontal displacement
    displacement_x = ball_vx * time_to_target
    
    # Raw predicted x
    predicted_x = ball_x + displacement_x
    
    # Reflect across boundaries
    if predicted_x < 0 or predicted_x > BOARD_WIDTH:
        normalized = predicted_x / BOARD_WIDTH
        bounces = int(abs(normalized))
        remainder = abs(normalized) - bounces
        
        if bounces % 2 == 0:
            # Even bounces: same direction
            result = remainder * BOARD_WIDTH
        else:
            # Odd bounces: flipped
            result = (1.0 - remainder) * BOARD_WIDTH
        
        return max(0, min(BOARD_WIDTH, result))
    else:
        return predicted_x

def calculate_reward(current_state, last_state, player_id, last_action, prev_action=None):
    """Shaped reward: hit/miss + guidance + jitter."""
    # Unpack
    x, y, vx, vy, a, p1, p2 = current_state
    last_x, last_y, last_vx, last_vy, last_a, last_p1, last_p2 = last_state
    
    my_pad_pos = p1 if player_id == 1 else p2
    
    # Step penalty
    reward = -0.005
    
    # Hit / miss
    if player_id == 1:
        # Player 1 at bottom
        is_my_turn = last_vy > 0 and vy < 0 and last_y < PLAYER_PAD_Y_COORD
        if is_my_turn:
            reward += 25.0
            return reward
        
        # Player 1 miss
        if last_y < PLAYER_PAD_Y_COORD and y >= PLAYER_PAD_Y_COORD and vy > 0:
            distance = abs(x - my_pad_pos)
            penalty = 25.0 + (distance * 0.1)
            reward -= penalty
            return reward
    else:
        # Player 2 at top
        is_my_turn = last_vy < 0 and vy > 0 and last_y > 0
        if is_my_turn:
            reward += 25.0
            return reward
        
        # Player 2 miss
        if last_y > 0 and y <= 0 and vy < 0:
            distance = abs(x - my_pad_pos)
            penalty = 25.0 + (distance * 0.1)
            reward -= penalty
            return reward
    
    # Guidance
    try:
        # Target y by player side
        target_y = PLAYER_PAD_Y_COORD if player_id == 1 else 0
        target_x = get_target_x(x, y, vx, vy, target_y)
        distance_to_target = abs(my_pad_pos - target_x)
        
        # Distance shaping
        max_distance = BOARD_WIDTH / 2.0
        proximity_reward = 0.05 * (1.0 - min(distance_to_target / max_distance, 1.0))
        reward += proximity_reward
        
        # Directional bonus (symmetric)
        threshold = BOARD_WIDTH * 0.1
        if distance_to_target > threshold:
            if my_pad_pos < target_x - 5 and last_action == 1:
                reward += 0.03
            elif my_pad_pos > target_x + 5 and last_action == 2:
                reward += 0.03
            elif last_action == 0:
                reward -= 0.01
            else:
                reward -= 0.02
        else:
            if last_action == 0:
                reward += 0.02
            elif last_action != 0:
                reward -= 0.01
            
    except Exception:
        pass
    
    # Mild jitter penalty
    if prev_action is not None and prev_action != 0:
        if last_action != prev_action:
            reward -= 0.01
            
            if (last_action == 1 and prev_action == 2) or (last_action == 2 and prev_action == 1):
                reward -= 0.02
    
    return reward

# --- 3. Global state and control ---

STATE_DIM = 7
ACTION_DIM = 3  # 0: Stay, 1: Right, 2: Left
UPDATE_TIMESTEP = 200  # Update every 200 steps
MODEL_FILE = "ppo_pong_model.pth"

# Global state
global_agent = None
global_last_state = None
global_last_action = None
global_prev_action = None  # track previous action for jitter
global_player_id = None
step_count = 0

def initialize_agent():
    """Init agent once."""
    global global_agent, global_player_id
    
    if global_agent is not None:
        return
    
    print("Initializing PPO agent...")
    global_agent = PPOAgent(STATE_DIM, ACTION_DIM)
    
    # Try loading checkpoint
    if global_agent.load(MODEL_FILE):
        print(f"Loaded model from {MODEL_FILE}.")
    else:
        print("No checkpoint found, starting fresh training.")

def get_agent_input(state, player):
    """Convert game state to agent input: [x, y, vx, vy, a, p1, p2]."""
    x, y, vx, vy, a, p1, p2 = state
    pad_pos = p1 if player == 1 else p2
    return np.array([x, y, vx, vy, a, p1, p2], dtype=np.float32)

def control(state, player):
    """
    Main control: action selection + training.
    """
    global global_agent, global_last_state, global_last_action, global_prev_action, global_player_id, step_count
    
    initialize_agent()
    
    # Current state
    current_state = get_agent_input(state, player)
    
    # Track the first player seen
    if global_player_id is None:
        global_player_id = player
    
    # Training/update (skip first step)
    if global_last_state is not None:
        # Compute reward
        reward = calculate_reward(current_state, global_last_state, global_player_id, global_last_action, global_prev_action)
        
        # Termination: large negative means miss
        terminated = reward < -5.0
        
        # Store transition
        global_agent.rewards.append(reward)
        global_agent.is_terminals.append(terminated)
        
        step_count += 1
        
        # Periodic update
        if step_count % UPDATE_TIMESTEP == 0:
            global_agent.update()
            global_agent.save(MODEL_FILE)
            print(f"Saved model at step {step_count} to {MODEL_FILE}")
    
    # Action selection
    action_id = global_agent.select_action(current_state)
    
    # Cache for next step
    global_prev_action = global_last_action
    global_last_state = current_state
    global_last_action = action_id
    
    # Map action to game command: 0 stay, 1 right, 2 left
    if action_id == 0:
        return 0
    elif action_id == 1:
        return 1
    else:  # action_id == 2
        return -1

def control_s(state, player):
    """Skill control disabled for PPO agent."""
    return False
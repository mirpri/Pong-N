import math

BOARD_WIDTH = 800
PLAYER_PAD_Y_COORD = 700

def get_target_x(ball_x, ball_y, ball_vx, ball_vy, target_y):
    """
    predict the x coordinate where the ball will reach the target_y line.
    """
    if ball_vy == 0:
        return ball_x
    
    # 1. calculate time to reach target_y
    time_to_target = abs(target_y - ball_y) / abs(ball_vy)
    
    # 2. calculate horizontal displacement
    displacement_x = ball_vx * time_to_target
    
    # 3. calculate predicted x position
    predicted_x = ball_x + displacement_x
    
    # 4. handle boundary reflection (simplified: only consider one bounce)
    # if predicted position is out of bounds (0 to BOARD_WIDTH)
    if predicted_x < 0:
        # after bounce, distance from left boundary
        return abs(predicted_x)
    elif predicted_x > BOARD_WIDTH:
        # after bounce, distance from right boundary
        return BOARD_WIDTH - (predicted_x - BOARD_WIDTH)
    else:
        return predicted_x

def control(state: list, player: int) -> int:
    x, y, vx, vy, a, p1, p2 = state
    
    if player == 1:
        my_p = p1
        # respond only when the ball is moving downwards (vy > 0)
        if vy < 0:
            return 0
        target_y = PLAYER_PAD_Y_COORD 
    else: # player == 2
        my_p = p2
        # respond only when the ball is moving upwards (vy < 0)
        if vy > 0:
            return 0
        target_y = 100 

    # 1. predict the target x position when the ball reaches the player's pad y coordinate
    target_x = get_target_x(x, y, vx, vy, target_y)
    
    # 2. decide movement based on predicted x position
    TOLERANCE = 5 
    
    if target_x > my_p + TOLERANCE:
        return 1
    elif target_x < my_p - TOLERANCE:
        return -1
    else:
        return 0

def control_s(state: list, player: int) -> bool:
    # simply always return True to use skill whenever possible
    return True
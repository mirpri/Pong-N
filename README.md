# Pong-N
Pong Neon is a modern twist on the classic arcade game, ***Pong***. With simple controls and addictive gameplay, Pong Neon is easy to pick up and play, but challenging to master. Challenge a friend in 2-player mode for endless hours of fun. Can you beat the high score and become the neon pong champion? [Download](https://github.com/Mirpri/Pong-N/releases/) Pong Neon now and find out!
![image](https://github.com/Mirpri/Pong-N/assets/71537369/c72c3cf3-fb53-4393-ac9b-0f6390d2efa6)

## ✨Deep learning with Pong Neon!
I'm working on a feature that allows players to log their game and load models as opponent. You can log the game data to train a model in your way and load the model to see how it performs!

Stay tuned for updates on this exciting feature, and get ready to take your Pong Neon experience to the next level with AI-powered opponents. Whether you're a machine learning enthusiast or just looking for a new challenge, this feature will add a whole new dimension to the game.

### Embark
It's time to train your own Pong master!
To work with the latest version, clone the repository with:
```
git clone https://github.com/Mirpri/Pong-N.git -b deeplearning
```

Install necessary packages:
```
pip install sv-ttk keyboard
```

Needed for "ai.py" profile:
```
pip install numpy
```

### Get playing data
Turn on 'Log' feature in the latest version by clicking on the 'Log' button before match starts.

Turn it off after match is over, and you will see a `log.txt` file saved in the same directory as the executable or python file.

In the `log.txt`, you get a 2D list. Each row is a set of data representing a state in the form of:
```
[x,y,vx,vy,a,p1,p2,v1,v2]
```
- `x`: The x-coordinate of the object or player in the game.
- `y`: The y-coordinate of the object or player in the game.
- `vx`: The velocity of the object or player along the x-axis.
- `vy`: The velocity of the object or player along the y-axis.
- `a`: The acceleration of the object or player.
- `p1`: The position or state of player 1.
- `p2`: The position or state of player 2.
- `v1`: The velocity or some other variable related to player 1.
- `v2`: The velocity or some other variable related to player 2.

These values collectively represent the state of the game at a particular moment in time.

For consultation:
```
board size: 600x800
player 1: y=700
player 2: y=100
origin: left-top corner
```

### Train your model
Feed the logged data into your preferred machine learning framework and choose your favorite algorithm to train your model.

### Load your model
To load your trained model in Pong Neon, you have you write a python file defining 2 functions named `control` and `control_s`.

`control` takes a list and a number as parameter and should return a number value. The parameter is like:
```
[x,y,vx,vy,a,p1,p2], p
```
`p` is either 1 or 2, suggesting the player you are operating.

A positive return value means moving the pad left, while a negative return value means moving the game pad left, and zero value mean don't move.

`control_s` takes the same parameter as `control` and should return a bool value. `True` means apply the character's skill, while `False` means don't. This function will be called only when it is possible to apply the skill.

For example:
```python
def control(state,player):
    x, y, vx, vy, a, p1, p2 = state
    # Simple logic to move the pad based on the ball's position
    if x > (if player==1 p1 else p2):
        return 1  # Move right
    elif x < (if player==1 p1 else p2):
        return -1  # Move left
    else:
        return 0
def control_s(state,player):
    return 1
```
In `./controls`, there are two exaples.

After that, put the file in `./controls` directory and run the program. You can select it in the combobox in UI. Click 'Start' and you can compete with it! 

Happy training and playing!

import numpy as np

def noise_model(direction, current_direction):
    if direction == 'left':    
        # Adds some noise for the bar to move back and forth
        if current_direction == 'left':
            if np.random.random() < 0.03:
                current_direction = 'right'
        else:
            if np.random.random() < 0.1:
                current_direction = 'left'
    
    else:
        # Adds some noise for the bar to move back and forth
        if current_direction == 'right':
            if np.random.random() < 0.03:
                current_direction = 'left'
        else:
            if np.random.random() < 0.1:
                current_direction = 'right'
    return current_direction
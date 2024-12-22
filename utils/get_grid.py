import numpy as np


def get_grid(size_x: float, size_y: float):
    grid_x = np.linspace(0, size_x, 100)
    grid_y = np.linspace(0, size_y, 100)

    return grid_x, grid_y

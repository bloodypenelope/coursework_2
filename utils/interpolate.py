import numpy as np
from scipy.interpolate import RBFInterpolator


def rbf_interpolate(points: list[list[float]], values: list[float],
                    grid_x: list[float], grid_y: list[float]):
    grid_x, grid_y = np.meshgrid(grid_x, grid_y)

    x_axis, y_axis = grid_x.ravel(), grid_y.ravel()
    plane_points = np.vstack((x_axis, y_axis)).T

    interpolator = RBFInterpolator(
        points, values, kernel="multiquadric", epsilon=.375)
    grid_z = interpolator(plane_points).reshape(grid_x.shape)

    return grid_z

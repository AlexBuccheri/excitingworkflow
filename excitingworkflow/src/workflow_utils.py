"""
Some help functions.
"""
from typing import Union

import numpy as np


def generate_k_grid_list(lattice: Union[list[list[float]], np.ndarray], cutoff: int = 3400) -> list[list[int]]:
    """
    function to generate a list of k-grids for convergence series. EXPERIMENTAL!!
    :param lattice: Lattice vectors of the material
    :param cutoff: maximum number of k_points that are included in the k_point list
    """
    reciprocal_lattice_norms = 1 / np.linalg.norm(lattice, axis=1)
    k_list = []
    k_points = [0, 0, 0]
    num_k_points = 0
    factor = 0

    while num_k_points < cutoff:
        new_k_points = [int(x) for x in np.floor(reciprocal_lattice_norms * factor)]
        if k_points != new_k_points:
            k_points = new_k_points
            num_k_points = np.product(k_points)
            if num_k_points > 0:
                k_list.append(k_points)
        factor += 0.1
    return k_list

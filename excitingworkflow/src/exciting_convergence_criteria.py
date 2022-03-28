from typing import Tuple

import numpy as np
from scipy.interpolate import interp1d
from scipy.stats import spearmanr

from src.calculation_io import ConvergenceCriteria
try:
    import simmeasxas
except ImportError:
    pass
else:
    from simmeasxas.analysis import get_spectra_similarity


def spearman_similarity(plot1: np.array, plot2: np.array) -> float:
    """
    Calculate the inverse Spearman similarity for two plots
    :param plot1: first plot to be compared
    :param plot2: second plot to be compared
    """
    interp1 = interp1d(plot1[:, 0], plot1[:, 1], assume_sorted=True, kind='cubic', bounds_error=True)
    interp2 = interp1d(plot2[:, 0], plot2[:, 1], assume_sorted=True, kind='cubic', bounds_error=True)

    spearman1 = spearmanr(interp2(plot1[:, 0]), plot1[:, 1])
    spearman2 = spearmanr(interp1(plot2[:, 0]), plot2[:, 1])

    similarity = 1 - 0.5 * (spearman1[0] + spearman2[0])
    return np.log(similarity) / np.log(10)


class ExcitingConvergenceCriteria(ConvergenceCriteria):
    """
    Exciting Convergence Criteria
    """
    def evaluate(self, current: dict, prior: dict) -> Tuple[bool, bool]:
        """ Evaluate a convergence criterion for each target.

        :param current: Dictionary containing current result/s
        :param prior: Dictionary containing prior result/s
        :return Tuple of bools indicating (converged, early_exit).
        """
        plot_current = np.array((current['frequency'], current['imag_oscillator_strength']))
        plot_prior = np.array((prior['frequency'], prior['imag_oscillator_strength']))

        if self.criteria['type'] == 'spearman':
            similarity_log = spearman_similarity(plot_current, plot_prior)
            converged = similarity_log < self.criteria['threshold']
        elif self.criteria['type'] == 'simmeasxas':
            similarity = get_spectra_similarity(plot_current, plot_prior)
            converged = similarity > self.criteria['threshold']
        else:
            raise ValueError('Convergence Criteria is not None.')

        return converged, False

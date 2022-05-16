"""
Some functions for nicer convergence plots.
"""
from typing import Union, List, Tuple

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

from excitingtools.parser.parserChooser import parser_chooser
from mpl_toolkits.axes_grid1 import make_axes_locatable

from excitingworkflow.src.exciting_calculation import ExcitingCalculation
try:
    import simmeasxas
except ImportError:
    pass
else:
    from simmeasxas.analysis import get_spectra_similarity


def compute_simmeasxas_similarity_matrix(spectra: np.ndarray) -> np.ndarray:
    """
    Takes a spectra array with dimensions: number_of_spectra x 2 (x and y) x number_of_points (typically large)
    """
    n = np.shape(spectra)[0]  # number of spectra
    similarity_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            similarity_matrix[i, j] = get_spectra_similarity(spectra[i, :, :].transpose(), spectra[j, :, :].transpose())
    return similarity_matrix


def convergence_plot_setup() -> (str, int):
    figcolor = 'white'
    dpi = 300

    mpl.rcParams['grid.linewidth'] = 1.5
    mpl.rcParams['xtick.labelsize'] = 20
    mpl.rcParams['ytick.labelsize'] = 20
    plt.rcParams['xtick.major.pad'] = 10
    plt.rcParams['ytick.major.pad'] = 10
    mpl.rcParams['axes.titlesize'] = 30
    mpl.rcParams['axes.linewidth'] = 2.0  # set the value globally
    mpl.rcParams['axes.edgecolor'] = 'black'
    mpl.rcParams['axes.labelsize'] = 20  # fontsize of the x any y labels
    mpl.rcParams['axes.labelcolor'] = 'black'
    # whether axis gridlines and ticks are below the axes elements (lines, text, etc)
    mpl.rcParams['axes.axisbelow'] = 'True'
    mpl.rcParams['legend.fontsize'] = 20
    return figcolor, dpi


def parse_spectra(calculation_list: list[Union[str, ExcitingCalculation]], quantity: str = 'EPSILON',
                  calc_type: str = 'singlet', polarization: str = '11') -> (np.ndarray, list[str]):
    if calc_type == 'singlet':
        calc_type += '-TDA-BAR'
    file_name = quantity + '_BSE-' + calc_type + '_SCR-full_OC' + polarization + '.OUT'

    spectra = []
    label_list = []
    calculations = [calc for calc in calculation_list if isinstance(calc, ExcitingCalculation)]
    calc_dirs = [calc for calc in calculation_list if calc not in calculations]
    for calculation in calculations:
        if calculation.xs is None:
            raise ValueError('Passed ExcitingCalculation is no xs calculation.')
        result = calculation.parse_output()[file_name]
        spectra = spectra + [np.array((result['frequency'], result['imag_oscillator_strength']))]
        label_list.append(calculation.name)

    for dire in calc_dirs:
        result = parser_chooser(f"{dire}/{quantity}/{file_name}")
        spectra = spectra + [np.array((result['frequency'], result['imag_oscillator_strength']))]
        label_list.append(dire)

    return np.array(spectra), label_list


def plot_spectra(calculation_list: list[Union[str, ExcitingCalculation]], quantity: str = 'EPSILON',
                 calc_type: str = 'singlet', polarization: str = '11', x_cutoff: Tuple = None):
    """
    Generate plot of spectra for BSE calculations.
    :param calculation_list: List of directories as strings containing the calculations. Or better
    list of ExcitingCalculations
    :param quantity: which quantity to plot, choose from: 'EPSILON', 'EXCITON', 'LOSS'
    :param calc_type: choose from 'singlet', 'IP', 'RPA', automatically taken from ExcitingCalculation if
    nothing else is specified
    :param polarization: polarization direction, either '11', '22' or '33'
    :param x_cutoff: defines which range of points will be plotted from the spectra
    """
    figcolor, dpi = convergence_plot_setup()
    spectra, label_list = parse_spectra(calculation_list, quantity, calc_type, polarization)
    x_cutoff = x_cutoff or (0, np.shape(spectra)[2])

    fig = plt.figure(figsize=(20, 15), dpi=dpi, facecolor=figcolor)

    ax = fig.add_subplot()
    ax.set_title('Spectra')

    ax.set_xlabel('Omega [eV]')
    for i, label in enumerate(label_list):
        ax.plot(spectra[i, 0, x_cutoff[0]:x_cutoff[1]], spectra[i, 1, x_cutoff[0]:x_cutoff[1]], label=label)
    plt.legend()


def similarity_plot(axis_tick_labels: List, similarity_matrix: np.ndarray = None,  title: str = None,
                    axis_labels: str = 'ngridk', spectra: np.ndarray = None):
    if spectra is not None:
        similarity_matrix = compute_simmeasxas_similarity_matrix(spectra)

    figcolor, dpi = convergence_plot_setup()
    fig = plt.figure(figsize=(20, 15), dpi=dpi, facecolor=figcolor)
    ax = fig.add_subplot()

    n = np.shape(similarity_matrix)[0]
    num_digits = np.min((np.max((11 - n, 1)), 6))

    ax.set_title(title or 'Spearman similarity')
    ax.set_xlabel(axis_labels)
    ax.set_ylabel(axis_labels)

    ax.set_xticks(np.arange(np.shape(similarity_matrix)[0] + 1))
    ax.set_yticks(np.arange(np.shape(similarity_matrix)[0] + 1))

    ax.set_xticklabels(axis_tick_labels + [''])
    ax.set_yticklabels(axis_tick_labels + [''])

    im = ax.imshow(similarity_matrix)

    border = (np.max(similarity_matrix) + np.nanmin(similarity_matrix[similarity_matrix != np.NINF])) / 2

    for (j, i), value in np.ndenumerate(similarity_matrix):
        if value > border:
            textcolor = 'black'
        else:
            textcolor = 'white'
        ax.text(i, j, round(value, num_digits), ha='center', va='center', fontsize='xx-large', color=textcolor)

    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="7%", pad=0.1)

    fig.colorbar(im, cax=cax)

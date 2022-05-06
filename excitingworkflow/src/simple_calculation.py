from __future__ import annotations

from typing import Union

import numpy as np
from excitingtools.runner import SubprocessRunResults, BinaryRunner
from excitingworkflow.src.calculation_io import CalculationIO


class SimpleCalculation(CalculationIO):
    """
    Function for generating an simple calculation. You can write the necessary input files, execute the calculation
    and parse the results. Really just a very simple example to show and test the behviour of the Convergence routine.
    It returns a decaying exponential function.
    """
    def __init__(self,
                 name: str,
                 directory: CalculationIO.path_type,
                 input_value: float):
        """
        :param name: title of the calculation
        :param directory: where to run the calculation
        :param input_value: input value
        """
        super().__init__(name, directory)
        self.input_value = input_value

    def write_inputs(self):
        with open(self.directory / "input.txt", "w") as fid:
            fid.write(str(self.input_value))

    def run(self):
        """ Wrapper for simple BinaryRunner.

        :return: Subprocess results or NotImplementedError.
        """
        with open(self.directory / "input.txt", "r") as fid:
            input_value = fid.read()
            try:
                value = float(input_value)
            except ValueError:
                raise ValueError('Wrong input file!')

        output = np.exp(-1 * value) + 1.5

        with open(self.directory / "out.txt", "w") as fid:
            fid.write(str(output))

    def parse_output(self) -> Union[float, FileNotFoundError]:
        """
        TODO(Fab): Rethink this, what is needed
        """
        with open(self.directory / "out.txt", "r") as fid:
            output = fid.read()
        return float(output)

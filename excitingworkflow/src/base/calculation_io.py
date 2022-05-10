""" Abstract base classes that define a calculation.
"""
import abc
import pathlib
from typing import Union

from excitingtools.runner import SubprocessRunResults


class CalculationIO(abc.ABC):
    """Abstract base class for a calculation that is performed
    by writing input file/s and parsing the result from a file.

    An IO calculation is expected to have:
        * A name,
        * A working (run) directory,
        * A method to write all input files required to run the calculation,
        * A method to run the calculation,
        * A parser for the outputs of interest.
    """
    path_type = Union[str, pathlib.Path]

    def __init__(self, name: str, directory: path_type):
        self.name = name
        if isinstance(directory, str):
            directory = pathlib.Path(directory)
        if not directory.is_dir():
            directory.mkdir()
        self.directory = directory

    @abc.abstractmethod
    def write_inputs(self) -> None:
        """ Write all input files required for calculation.
        """
        ...

    @abc.abstractmethod
    def run(self) -> SubprocessRunResults:
        """ Run the calculation.
        :return Subprocess result instance.
        """

    @abc.abstractmethod
    def parse_output(self, *args) -> Union[dict, FileNotFoundError]:
        """ Parse one or more output files for calculation.
        :return Dictionary of results.
        """
        ...

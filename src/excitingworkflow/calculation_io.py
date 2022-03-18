import abc
from collections.abc import Iterable

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
    def __init__(self, name: str, directory: path_type):
        self.name = name
        self.directory = directory
        if not Path.is_dir(directory):
            raise NotADirectoryError(f'Not a directory: {directory}')

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


class ConvergenceCriteria(abc.ABC):
    """Abstract base class for performing a set of convergence calculations.

    Attributes correspond to input value to vary, and target value to check convergence against.
    Method should supply a convergence criterion or criteria w.r.t. the target value/s.
    """
    def __init__(self, input, criteria: dict):
        """ Initialise an instance of Convergence.

        :param input: A range of input values. Can be in any format, as long it's iterable.
        :param criteria: Dictionary of convergence criteria. {key:value} = {target: criterion}
        """
        self.input = input
        self.criteria = criteria
        if not isinstance(input, Iterable):
            raise ValueError('input must be iterable.')
        if len(input) <= 1:
            raise ValueError('input must have a length > 1')

    def check_target(func: Callable):
        """ Provide argument checking.

        :param func: evaluate method.
        :return: Modified evaluate method.
        """
        def func_with_target_check(self, current: dict, prior: dict):

            # Only expect for a failed run
            if isinstance(current, SubprocessRunResults):
                converged, early_exit = current.success, True
                return converged, early_exit

            set_current = set(current)

            # TODO(Alex) Should look at propagating the ValueErrors out
            if set_current != set(prior):
                return ValueError(f'Keys of current and prior results are inconsistent:'
                                  f'{set_current} != {set(prior)}')

            if set_current != set(self.criteria):
                raise ValueError(f'Keys of current result inconsistent with keys of convergence criteria:'
                                 f'{set(current)} != {set(self.criteria)}')

            return func(self, current, prior)

        return func_with_target_check

    @abc.abstractmethod
    def evaluate(self, current: dict, prior: dict) -> Tuple[bool, bool]:
        """ Evaluate a convergence criterion for each target.

        Decorators cannot be applied to methods decorated with abstractmethod.
        As such, sub-class implementations of `evaluate` should be defined as:

        @ConvergenceCriteria.check_target
        def evaluate(self, current: dict, prior: dict) -> Tuple[bool, bool]:
            # Implementation here

        to get use the value-checking. Alternative would be to evaluate in ConvergenceCriteria
        using the definition of the decorator (i.e. the value-checking) then inherit it in
        sub-classes that overwrite the method:

        def evaluate(self, a, b):
            super.evaluate(a, b)

        :param current: Dictionary containing current result/s
        :param prior: Dictionary containing prior result/s
        :return Tuple of bools indicating (converged, early_exit).
        """
        ...
        

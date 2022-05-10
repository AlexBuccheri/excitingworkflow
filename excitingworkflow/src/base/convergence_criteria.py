""" Abstract base class to define a converence criterion or criteria
for a convergence workflow.
"""
import abc
from collections.abc import Iterable
from typing import Tuple, Callable

from excitingtools.runner import SubprocessRunResults


class ConvergenceCriteria(abc.ABC):
    """Abstract base class used to define and check convergence in a workflow.

    Attributes correspond to input value to vary, and target value to check convergence against.
    Method should supply a convergence criterion or criteria w.r.t. the target value/s.
    """
    def __init__(self, input, criteria: dict):
        """ Initialise an instance.

        :param input: A range of input values. Can be in any format, as long it's iterable.
        :param criteria: Dictionary of convergence criteria, {target: criterion}
        """
        self.input = input
        self.criteria = criteria
        if not isinstance(input, Iterable):
            raise ValueError('input must be iterable.')
        if len(input) <= 1:
            raise ValueError('input must have a length > 1')

    def check_target(self, func: Callable):
        """ Provide argument-checking.

        To be used as a decorator. See `evaluate` documentation.

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
        As such, child implementations of `evaluate` should be defined as:

        @ConvergenceCriteria.check_target
        def evaluate(self, current: dict, prior: dict) -> Tuple[bool, bool]:
            # Implementation here

        to get use the value-checking. An alternative would be to perform value-checking in
        the `evaluate` method of the parent class (so it's not abstract) and inherit it in the
        child method of the same name:

        def evaluate(self, a, b):
            super.evaluate(a, b)
            # Specific implementation

        :param current: Dictionary containing current result/s
        :param prior: Dictionary containing prior result/s
        :return Tuple of bools indicating (converged, early_exit).
        """
        ...

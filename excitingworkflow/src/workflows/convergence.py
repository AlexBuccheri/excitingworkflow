""" Generic convergence workflows.
"""
from typing import Callable, Union, List

from excitingworkflow.src.base.calculation_io import CalculationIO, CalculationError
from excitingworkflow.src.base.convergence_criteria import ConvergenceCriteria


def convergence_step(value,
                     calculation: CalculationIO,
                     set_value_in_input: Callable) -> Union[dict, CalculationError]:
    """ Perform a single calculation as part of a convergence test.

    One notes that the specifics of `set_value_in_input` are left to the developer.

    Setting a new input value (which should be varied to converge some output quantity) could be achieved by:
     1. Copying a calculation object, changing the value in the object and writing the new data to file.
     2. Simply modifying an existing file already present.

    Note, the returned dictionary MUST ONLY contain the relevant data.
    The CalculationIO class method `parse_output` determines exactly how this is constructed.

    :param value: Input value to be varied to achieve convergence.
    :param calculation: calculation instance, with methods defined by CalculationIO
    :param set_value_in_input: Function defining how to change the input value.

    :return: Dictionary containing the input value set by this routine, and the output value
    with which convergence is measured. If the calculation run fails, a SubprocessRunResults
    is returned instead.
    """
    set_value_in_input(value, calculation)
    subprocess_result = calculation.run()

    if subprocess_result.success:
        return calculation.parse_output()
    else:
        return CalculationError(subprocess_result)


class ConvergenceResult:
    """ Class to hold results of a convergence step.
    """
    def __init__(self, input_value, result, converged: bool, early_exit: bool):
        """
        :param input_value: Input value that should converge result.
        :param result: Quantity that is being converged.
        :param: converged: Is the result converged w.r.t. input_value.
        :param early_exit: Exit before the max input value, len(input_value), is reached.
        """
        self.input_value = input_value
        self.result = result
        self.converged = converged
        self.early_exit = early_exit


# A list of convergence results
ConvergenceResults = List[ConvergenceResult]


def converge(calculation: CalculationIO,
             convergence: ConvergenceCriteria,
             set_value_in_input: Callable[[any, CalculationIO], Union[any, None]]) -> ConvergenceResults:
    """ Converge a calculation output with respect to an input parameter.

    This routine assumes a calculation is performed via IO. That is, data is written to file,
    the calculation is executed, and data is written to file, which must then be parsed.

    calculation defines the methods to:
        Write all inputs required,
        Run the calculation,
        Parse the result/s required to measure convergence.

    convergence defines:
        * The input parameter to vary (and its range of values),
        * The target output/s to check,
        * The criterion/criteria with which to evaluate convergence.

    The function `set_value_in_input`:
        Function defining how to change the input value for per calculation, to achieve convergence.
        This is not a method of Calculation because it does not manage the state of
        a calculation (indeed, it could modify an input file already written), nor
        is it a method of Convergence.

    :param calculation: Calculation instance.
    :param convergence: Convergence parameters and criteria.
    :param set_value_in_input: Function that sets a value in the input
    defined by the calculation.

    :return: List of results. Each result is a tuple(input value, output)
    """
    # Write all required files to run the calculation
    calculation.write_inputs()

    # Initialise results by running the first value
    first_value = convergence.input[0]
    output = convergence_step(first_value, calculation, set_value_in_input)
    results = [ConvergenceResult(first_value, output, converged=False, early_exit=True)]

    if isinstance(output, CalculationError):
        return results

    for value in convergence.input[1:]:
        output = convergence_step(value, calculation, set_value_in_input)
        converged, early_exit = convergence.evaluate(output, results[-1].result)
        results.append(ConvergenceResult(value, output, converged, early_exit))
        if converged or early_exit:
            return results

    return results

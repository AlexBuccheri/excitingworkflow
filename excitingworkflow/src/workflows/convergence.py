""" Generic convergence workflows.
"""
from typing import Callable, Union

from excitingtools.runner import SubprocessRunResults

from excitingworkflow.src.base.calculation_io import CalculationIO
from excitingworkflow.src.base.convergence_criteria import ConvergenceCriteria


def convergence_step(value,
                     calculation: CalculationIO,
                     set_value_in_input: Callable) -> Union[dict, SubprocessRunResults]:
    """ Perform a single calculation as part of a convergence test.

    :param value: Input value be varied to achieve convergence.
    :param calculation: calculation instance, with methods defined by CalculationIO
    :param set_value_in_input: Function defining how to change the input value.
    This could be achieved by copying calculation, changing value, then write to file OR
    it could be modifying an existing file.
    :return: Dictionary containing the output value used to evaluate when convergence w.r.t. value.
    Note, this can contain other data. The ConvergenceCriteria class determines how this is evaluated.
    If the calculation run fails, a SubprocessRunResults is returned instead.
    """
    set_value_in_input(value, calculation)
    subprocess_result = calculation.run()
    if subprocess_result.success:
        return calculation.parse_output()
    return subprocess_result


def converge(calculation: CalculationIO,
             convergence: ConvergenceCriteria,
             set_value_in_input: Callable[[any, CalculationIO], Union[any, None]]) -> List[tuple]:
    """ Converge a calculation output with respect to an input parameter.

    calculation defines the methods to:
        Write all inputs required,
        Run the calculation,
        Parse the result/s required to measure convergence.

    convergence defines:
        * The input parameter to vary (and its range of values),
        * The target output/s to check,
        * The criterion/criteria with which to evaluate convergence.

    The function `set_value_in_input`:
        Function defining how to change the input value for per convergence calculation.
        This is not a method of Calculation because it does not manage the state of
        a calculation (indeed, it could modify an input file already written), nor
        is it a method of Convergence.

    Note, this is entirely analogous to writing templated code in C++

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
    result = convergence_step(first_value, calculation, set_value_in_input)
    results = [(first_value, result, False, False)]

    if isinstance(result, SubprocessRunResults):
        return results

    for value in convergence.input[1:]:
        result = convergence_step(value, calculation, set_value_in_input)
        converged, early_exit = convergence.evaluate(result, results[-1][1])
        results.append((value, result, converged, early_exit))
        if converged or early_exit:
            return results

    return results

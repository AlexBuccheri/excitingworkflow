import py

from excitingworkflow.src.simple_calculation import SimpleCalculation


def test_simpleCalculation():  # tmpdir: py.path.local):
    simple_calc = SimpleCalculation('test1', str('/home/fabi/Arbeit/Tests/excititingworkflow_test'), 4.2)
    simple_calc.write_inputs()
    simple_calc.run()
    result = simple_calc.parse_output()
    assert result == 1.5149955768204777

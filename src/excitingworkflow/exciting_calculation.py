import copy
import pathlib
from typing import Optional, Union

from excitingworkflow.calculation_io import CalculationIO


class ExcitingCalculation(CalculationIO):
    path_type = Union[str, pathlib.Path]

    def __init__(self, name, runner, structure, ground_state, bse: Optional, directory: path_type):
        super().__init__(name, directory)
        self.bse = bse

    def write_inputs(self):
        self.write_input_xml()
        # TODO Copy (from some well-defined place) and write species files

    def write_input_xml(self):
        pass
        # xml_tree = exciting_input_xml(structure, ground_state, bse=bse, title=self.name)
        # xml_string = ET.tostring(xml_tree)
        # with open(self.directory + "/input.xml", "w") as fid:
        #    fid.write(xml_string)

    def run(self):  # -> SubprocessRunResults:
        """ Wrapper for simple BinaryRunner.

        :return: Subprocess results or NotImplementedError.
        """
        # return self.runner.run()
        return

    def parse_output(self) -> FileNotFoundError:  # Union[dict, FileNotFoundError]:
        """
        """
        # info_out: dict = groundstate_parser.parse_info_out("INFO.OUT")
        # eps_singlet = bse_parser.parse_EPSILON_NAR("file_name")
        # return {**info_out, **eps_singlet}
        return FileNotFoundError


def set_gqmax(gq_max: float, calculation: ExcitingCalculation):
    new_calculation = copy.deepcopy(calculation)
    new_calculation.bse.gq_max = gq_max
    new_calculation.write_input_xml()

import copy
import pathlib
from typing import Optional, Union

from excitingtools.input.input_xml import exciting_input_xml_str
from excitingtools.parser import groundstate_parser, bse_parser
from excitingtools.runner import SubprocessRunResults, BinaryRunner
from excitingtools.input.ground_state import ExcitingGroundStateInput
from excitingtools.input.structure import ExcitingStructure
from excitingtools.input.xs import ExcitingXSInput
from excitingworkflow.calculation_io import CalculationIO


class ExcitingCalculation(CalculationIO):
    """
    Function for generating an exciting calculation. You can write the necessary input files, execute the calculation
    and parse the results.
    """
    path_type = Union[str, pathlib.Path]

    def __init__(self,
                 name: str,
                 directory: path_type,
                 runner: BinaryRunner,
                 structure: ExcitingStructure,
                 ground_state: ExcitingGroundStateInput,
                 xs: Optional[ExcitingXSInput] = None):
        """
        :param name: title of the calculation
        :param directory: where to run the calculation
        :param runner: Runner to run exciting
        :param structure: Object containing the xml structure info
        :param ground_state: Object containing the xml groundstate info
        :param xs: Object containing the xml xs info
        """
        super().__init__(name, directory)
        self.runner = runner
        self.structure = structure
        self.ground_state = ground_state
        self.optional_xml_elements = {}
        if xs is not None:
            self.optional_xml_elements['xs'] = xs

    def write_inputs(self):
        self.write_input_xml()
        # TODO Copy (from some well-defined place) and write species files

    def write_input_xml(self):
        xml_tree_str = exciting_input_xml_str(self.structure, self.ground_state, title=self.name,
                                              **self.optional_xml_elements)

        with open(self.directory + "/input.xml", "w") as fid:
            fid.write(xml_tree_str)

    def run(self) -> SubprocessRunResults:
        """ Wrapper for simple BinaryRunner.

        :return: Subprocess results or NotImplementedError.
        """
        return self.runner.run()

    def parse_output(self) -> Union[dict, FileNotFoundError]:
        """
        """
        # TODO: Parse INFOXS.OUT; INFO.OUT not needed, not even present?
        info_out: dict = groundstate_parser.parse_info_out("INFO.OUT")
        eps_singlet = bse_parser.parse_EPSILON_NAR("EPSILON_BSE-singlet-TDA-BAR_SCR-full_OC11.OUT")
        return {**info_out, **eps_singlet}


def set_gqmax(gq_max: float, calculation: ExcitingCalculation):
    new_calculation = copy.deepcopy(calculation)
    new_calculation.optional_xml_elements['xs'].xs['gqmax'] = gq_max
    new_calculation.write_input_xml()

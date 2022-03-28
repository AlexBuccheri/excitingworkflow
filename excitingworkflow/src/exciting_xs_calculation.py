import copy
import pathlib
import shutil
from typing import Union

from excitingtools.input.input_xml import exciting_input_xml_str
from excitingtools.parser import bse_parser
from excitingtools.runner import SubprocessRunResults, BinaryRunner
from excitingtools.input.ground_state import ExcitingGroundStateInput
from excitingtools.input.structure import ExcitingStructure
from excitingtools.input.xs import ExcitingXSInput
from excitingworkflow.src.calculation_io import CalculationIO


class ExcitingXSCalculation(CalculationIO):
    """
    Function for generating an exciting calculation. You can write the necessary input files, execute the calculation
    and parse the results.
    """
    path_type = Union[str, pathlib.Path]

    def __init__(self,
                 name: str,
                 directory: path_type,
                 structure: ExcitingStructure,
                 ground_state: ExcitingGroundStateInput,
                 xs: ExcitingXSInput,
                 runner: BinaryRunner):
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
        structure.species_path = './'
        self.structure = structure
        self.ground_state = ground_state
        self.optional_xml_elements = {'xs': xs}

    def write_inputs(self):
        species = self.structure.unique_species
        path_to_species_files = '/home/fabi/code/exciting/species/'
        for speci in species:
            shutil.copy(path_to_species_files + speci + '.xml', self.directory)
        self.write_input_xml()

    def write_input_xml(self):
        xml_tree_str = exciting_input_xml_str(self.structure, self.ground_state, title=self.name,
                                              **self.optional_xml_elements)

        with open(self.directory / "input.xml", "w") as fid:
            fid.write(xml_tree_str)

    def run(self) -> SubprocessRunResults:
        """ Wrapper for simple BinaryRunner.

        :return: Subprocess results or NotImplementedError.
        """
        return self.runner.run()

    def parse_output(self) -> Union[dict, FileNotFoundError]:
        """
        """
        eps_singlet = bse_parser.parse_EPSILON_NAR("EPSILON_BSE-singlet-TDA-BAR_SCR-full_OC11.OUT")
        return {**eps_singlet}


def set_gqmax(gq_max: float, calculation: ExcitingXSCalculation):
    new_calculation = copy.deepcopy(calculation)
    new_calculation.optional_xml_elements['xs'].xs['gqmax'] = gq_max
    new_calculation.write_input_xml()

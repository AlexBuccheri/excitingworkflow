import shutil
from typing import Union, Optional

from excitingtools.input.input_xml import exciting_input_xml_str
from excitingtools.input.xs import ExcitingXSInput
from excitingtools.parser import groundstate_parser, bse_parser
from excitingtools.runner import SubprocessRunResults, BinaryRunner
from excitingtools.input.ground_state import ExcitingGroundStateInput
from excitingtools.input.structure import ExcitingStructure
from excitingworkflow.src.calculation_io import CalculationIO


class ExcitingCalculation(CalculationIO):
    """
    Function for generating an exciting calculation. You can write the necessary input files, execute the calculation
    and parse the results.
    """
    def __init__(self,
                 name: str,
                 directory: CalculationIO.path_type,
                 structure: ExcitingStructure,
                 ground_state: ExcitingGroundStateInput,
                 runner: BinaryRunner,
                 xs: Optional[ExcitingXSInput] = None):
        """
        :param name: title of the calculation
        :param directory: where to run the calculation
        :param runner: Runner to run exciting
        :param structure: Object containing the xml structure info
        :param ground_state: Object containing the xml groundstate info
        """
        super().__init__(name, directory)
        self.path_to_species_files = structure.species_path
        structure.species_path = './'
        self.runner = runner
        self.structure = structure
        self.ground_state = ground_state
        self.optional_xml_elements = {}
        if xs is not None:
            self.optional_xml_elements['xs'] = xs

    def write_inputs(self):
        species = self.structure.unique_species
        for speci in species:
            shutil.copy(self.path_to_species_files + speci + '.xml', self.directory)
        self.write_input_xml()
        self.write_slurm_script()

    def write_slurm_script(self):
        pass

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
        TODO(Fab): Rethink this, what is needed
        """
        if self.optional_xml_elements == {}:
            info_out: dict = groundstate_parser.parse_info_out(self.directory / "INFO.OUT")
            return {**info_out}
        eps_singlet = bse_parser.parse_EPSILON_NAR(self.directory / "EPSILON" /
                                                   "EPSILON_BSE-singlet-TDA-BAR_SCR-full_OC11.OUT")
        return {**eps_singlet}

import pathlib
import shutil
from typing import Union, Optional

import xml.etree.ElementTree as ET
from excitingtools.input.input_xml import exciting_input_xml_str
from excitingtools.input.xs import ExcitingXSInput
from excitingtools.parser import groundstate_parser, bse_parser
from excitingtools.runner import SubprocessRunResults, BinaryRunner
from excitingtools.input.ground_state import ExcitingGroundStateInput
from excitingtools.input.structure import ExcitingStructure
from excitingworkflow.src.calculation_io import CalculationIO


def parse_groundstate(groundstate: pathlib.Path) -> ExcitingGroundStateInput:
    tree = ET.parse(groundstate / "input.xml")
    root = tree.getroot()
    for i in range(len(root)):
        if root[i].tag == 'groundstate':
            break
    gs_tree = root[i]
    gs_attribs = {key: value for key, value in gs_tree.attrib.items()}
    gs_attribs['do'] = 'skip'
    return ExcitingGroundStateInput(**gs_attribs)


class ExcitingCalculation(CalculationIO):
    """
    Function for generating an exciting calculation. You can write the necessary input files, execute the calculation
    and parse the results.
    """
    def __init__(self,
                 name: str,
                 directory: CalculationIO.path_type,
                 structure: ExcitingStructure,
                 ground_state: Union[ExcitingGroundStateInput, CalculationIO.path_type],
                 runner: BinaryRunner,
                 xs: Optional[ExcitingXSInput] = None):
        """
        :param name: title of the calculation
        :param directory: where to run the calculation
        :param runner: Runner to run exciting
        :param structure: Object containing the xml structure info
        :param ground_state: Object containing the xml groundstate info OR path to already performed gs calculation
        from where the necessary files STATE.OUT and EFERMI.OUT are copied
        :param xs: optional xml xs info
        """
        super().__init__(name, directory)
        self.path_to_species_files = structure.species_path
        structure.species_path = './'
        self.runner = runner
        self.structure = structure
        self.ground_state = self.init_ground_state(ground_state)
        self.optional_xml_elements = {}
        if xs is not None:
            self.optional_xml_elements['xs'] = xs

    def init_ground_state(self, ground_state):
        if isinstance(ground_state, ExcitingGroundStateInput):
            return ground_state
        if isinstance(ground_state, str):
            ground_state = pathlib.Path(ground_state)
        shutil.copy(ground_state / 'STATE.OUT', self.directory)
        shutil.copy(ground_state / 'EFERMI.OUT', self.directory)
        return parse_groundstate(ground_state)

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

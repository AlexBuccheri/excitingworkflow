import pathlib
import shutil
from typing import Union, Optional

import xml.etree.ElementTree as ET

import numpy as np
from excitingtools.input.input_xml import exciting_input_xml_str
from excitingtools.input.xs import ExcitingXSInput
from excitingtools.parser import groundstate_parser, bse_parser
from excitingtools.runner import SubprocessRunResults, BinaryRunner
from excitingtools.input.ground_state import ExcitingGroundStateInput
from excitingtools.input.structure import ExcitingStructure
from excitingworkflow.src.calculation_io import CalculationIO


def get_element_from_root(directory: pathlib.Path, element_tag: str) -> ET.Element:
    tree = ET.parse(directory / "input.xml")
    root = tree.getroot()
    element = None
    for element in root:
        if element.tag == element_tag:
            break
    return element


def parse_element(path_to_gs_calculation: pathlib.Path, element_tag: str) -> ET.Element:
    element = get_element_from_root(path_to_gs_calculation, element_tag)
    if element is None:
        raise ValueError('Given element_tag doesnt exist in the input.xml.')
    if element_tag == 'groundstate':
        element.set('do', 'skip')
    return element


def find_species_files(path_to_gs_calculation: pathlib.Path) -> list:
    structure_tree = get_element_from_root(path_to_gs_calculation, 'structure')
    unique_elements = set()
    for element in structure_tree:
        if element.tag == 'species':
            unique_elements.add(element.get('speciesfile'))
    return sorted(unique_elements)


class ExcitingCalculation(CalculationIO):
    """
    Function for generating an exciting calculation. You can write the necessary input files, execute the calculation
    and parse the results.
    """
    def __init__(self,
                 name: str,
                 directory: CalculationIO.path_type,
                 structure: Union[ExcitingStructure, CalculationIO.path_type],
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
        self.path_to_species_files = None
        self.unique_species = None
        self.runner = runner
        self.structure = self.init_structure(structure)
        self.ground_state = self.init_ground_state(ground_state)
        self.optional_xml_elements = {}
        if xs is not None:
            self.optional_xml_elements['xs'] = xs

    def init_structure(self, structure: Union[ExcitingStructure, CalculationIO.path_type]) -> Union[ExcitingStructure,
                                                                                                    ET.Element]:
        if isinstance(structure, ExcitingStructure):
            self.path_to_species_files = structure.species_path
            structure.species_path = './'
            self.unique_species = [x + '.xml' for x in structure.unique_species]
            return structure
        if isinstance(structure, str):
            structure = pathlib.Path(structure)
        self.path_to_species_files = str(structure) + '/'
        self.unique_species = find_species_files(structure)
        return parse_element(structure, 'structure')

    def init_ground_state(self, ground_state: Union[ExcitingGroundStateInput,
                                                    CalculationIO.path_type]) -> Union[ExcitingGroundStateInput,
                                                                                       ET.Element]:
        if isinstance(ground_state, ExcitingGroundStateInput):
            return ground_state
        if isinstance(ground_state, str):
            ground_state = pathlib.Path(ground_state)
        shutil.copy(ground_state / 'STATE.OUT', self.directory)
        shutil.copy(ground_state / 'EFERMI.OUT', self.directory)
        return parse_element(ground_state, 'groundstate')

    def write_inputs(self):
        """
        Force the species files to be in the run directory.
        TODO: Allow different names for species files.
        """
        for speci in self.unique_species:
            shutil.copy(self.path_to_species_files + speci, self.directory)
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
            totengy = {'TOTENERGY': np.genfromtxt(self.directory / 'TOTENERGY.OUT')}
            info_out: dict = groundstate_parser.parse_info_out(self.directory / "INFO.OUT")
            return {**info_out, **totengy}
        eps_singlet = bse_parser.parse_EPSILON_NAR(self.directory / "EPSILON" /
                                                   "EPSILON_BSE-singlet-TDA-BAR_SCR-full_OC11.OUT")
        return {**eps_singlet}

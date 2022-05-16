from __future__ import annotations

import os
import pathlib
import shutil
from typing import Union, Optional

import numpy as np
from excitingtools.input.input_xml import exciting_input_xml_str
from excitingtools.input.xs import ExcitingXSInput
from excitingtools.parser.parserChooser import parser_chooser
from excitingtools.runner import SubprocessRunResults, BinaryRunner
from excitingtools.input.ground_state import ExcitingGroundStateInput
from excitingtools.input.structure import ExcitingStructure
from excitingtools.parser.input_parser import parse_groundstate_to_object, parse_structure_to_object
from excitingworkflow.src.base.calculation_io import CalculationIO


class ExcitingCalculation(CalculationIO):
    """
    Function for generating an exciting calculation. You can write the necessary input files, execute the calculation
    and parse the results.
    """
    def __init__(self,
                 name: str,
                 directory: CalculationIO.path_type,
                 structure: Union[ExcitingStructure, CalculationIO.path_type, ExcitingCalculation],
                 path_to_species_files: Union[CalculationIO.path_type, ExcitingCalculation],
                 ground_state: Union[ExcitingGroundStateInput, CalculationIO.path_type, ExcitingCalculation],
                 runner: BinaryRunner,
                 xs: Optional[ExcitingXSInput] = None):
        """
        :param name: title of the calculation
        :param directory: where to run the calculation
        :param structure: Object containing the xml structure info OR path to already performed gs calculation
        from where the structure part is taken OR old ExcitingCalculation object from which the structure part is taken
        :param path_to_species_files: where to find the species files OR old ExcitingCalculation object from
        which the path is taken
        :param ground_state: Object containing the xml groundstate info OR path to already performed gs calculation
        from where the necessary files STATE.OUT and EFERMI.OUT are copied OR old ExcitingCalculation object from
        which the ground_state part is taken
        :param runner: Runner to run exciting
        :param xs: optional xml xs info
        """
        super().__init__(name, directory)
        self.path_to_species_files = self.init_path_to_species_files(path_to_species_files)
        self.species_files = None
        self.runner = runner
        # ensure that the runner runs in the calculation directory:
        self.runner.directory = self.directory
        self.structure = self.init_structure(structure)
        self.ground_state = self.init_ground_state(ground_state)
        self.xs = xs

    @staticmethod
    def init_path_to_species_files(path_to_species_files: Union[CalculationIO.path_type,
                                                                ExcitingCalculation]) -> pathlib.Path:
        if isinstance(path_to_species_files, ExcitingCalculation):
            return path_to_species_files.path_to_species_files
        if isinstance(path_to_species_files, str):
            return pathlib.Path(path_to_species_files)
        # don't know why PyCharm is complaining, maybe because of the future import?
        return path_to_species_files

    def init_structure(self, structure: Union[ExcitingStructure, CalculationIO.path_type,
                                              ExcitingCalculation]) -> ExcitingStructure:
        if isinstance(structure, ExcitingCalculation):
            self.species_files = structure.species_files
            return structure.structure
        if isinstance(structure, CalculationIO.path_type):
            structure = parse_structure_to_object(str(structure) + '/input.xml')
        self.species_files = [x + '.xml' for x in structure.unique_species]
        return structure

    def init_ground_state(self, ground_state: Union[ExcitingGroundStateInput, CalculationIO.path_type,
                                                    ExcitingCalculation]) -> ExcitingGroundStateInput:
        if isinstance(ground_state, ExcitingCalculation):
            shutil.copy(ground_state.directory / 'STATE.OUT', self.directory)
            shutil.copy(ground_state.directory / 'EFERMI.OUT', self.directory)
            ground_state.ground_state.do = 'skip'
            return ground_state.ground_state
        if isinstance(ground_state, CalculationIO.path_type):
            ground_state = str(ground_state)
            shutil.copy(ground_state + '/STATE.OUT', self.directory)
            shutil.copy(ground_state + '/EFERMI.OUT', self.directory)
            ground_state = parse_groundstate_to_object(ground_state + '/input.xml')
            ground_state.do = 'skip'
        return ground_state

    def write_inputs(self):
        """
        Force the species files to be in the run directory.
        TODO: Allow different names for species files.
        """
        if not self.directory.is_dir():
            self.directory.mkdir()
        for species_file in self.species_files:
            shutil.copy(self.path_to_species_files / species_file, self.directory)
        self.write_input_xml()
        self.write_slurm_script()

    def write_slurm_script(self):
        pass

    def write_input_xml(self):
        xml_tree_str = exciting_input_xml_str(self.structure, self.ground_state, title=self.name, xs=self.xs)

        with open(self.directory / "input.xml", "w") as fid:
            fid.write(xml_tree_str)

    def run(self) -> SubprocessRunResults:
        """ Wrapper for simple BinaryRunner.

        :return: Subprocess results or NotImplementedError.
        """
        return self.runner.run()

    def parse_output(self, groundstate_files: list = None) -> Union[dict, FileNotFoundError]:
        """
        Parse output from an exciting calculation.
        If groundstate calculation was performed (meaning the 'do' attribute is not 'skip', parse the relevant
        groundstate output files and put them with filename as key in dictionary.
        If xs calculation was performed (meaning self.xs ist not None), look for xstype. For BSE calculations parse
        the files in LOSS, EPSILON and EXCITON folders. For other xstypes nothing yet implemented.
        """
        results = {}
        if self.ground_state.do != 'skip':
            if groundstate_files is None:
                groundstate_files = ['TOTENERGY.OUT', 'INFO.OUT', 'info.xml', 'atoms.xml', 'evalcore.xml', 'eigval.xml',
                                     'geometry.xml']
            for file in groundstate_files:
                if file == 'TOTENERGY.OUT':
                    results.update({'TOTENERGY.OUT': np.genfromtxt(self.directory / 'TOTENERGY.OUT')})
                else:
                    results.update({file: parser_chooser(str(self.directory / file))})

        if self.xs is not None:
            if self.xs.xs.xstype == 'BSE':
                subdirs = ['LOSS', 'EPSILON', 'EXCITON']
                for subdir in subdirs:
                    files = os.listdir(self.directory / subdir)
                    for file in files:
                        try:
                            results.update({file: parser_chooser(str(self.directory / subdir / file))})
                        except SystemExit:
                            print(f'WARNING: file {file} has not been parsed!')
            else:
                print('Parsing from other xs types than BSE not yet implemented!')

        return results

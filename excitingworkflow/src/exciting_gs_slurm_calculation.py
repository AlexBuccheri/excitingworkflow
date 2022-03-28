import pathlib
import shutil
import subprocess
import time
from typing import Optional, Union
from collections import OrderedDict

from excitingtools.input.input_xml import exciting_input_xml_str
from excitingtools.parser import groundstate_parser
from excitingtools.runner import SubprocessRunResults
from excitingtools.input.ground_state import ExcitingGroundStateInput
from excitingtools.input.structure import ExcitingStructure
from excitingworkflow.src.calculation_io import CalculationIO
from exgw.src.job_schedulers import slurm


class ExcitingGSSlurmCalculation(CalculationIO):
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
                 slurm_directives: Optional[OrderedDict] = None):
        """
        :param name: title of the calculation
        :param directory: where to run the calculation
        :param structure: Object containing the xml structure info
        :param ground_state: Object containing the xml groundstate info
        """
        super().__init__(name, directory)
        self.path_to_species_files = structure.species_path
        structure.species_path = './'
        self.structure = structure
        self.ground_state = ground_state
        default_directives = slurm.set_slurm_directives(job_name=self.name,
                                                        time=[0, 24, 0, 0],
                                                        partition='all',
                                                        exclusive=True,
                                                        nodes=1,
                                                        ntasks_per_node=8,
                                                        cpus_per_task=4,
                                                        hint='nomultithread')
        if slurm_directives is None:
            slurm_directives = default_directives
        self.slurm_directives = slurm_directives

    def write_inputs(self):
        species = self.structure.unique_species
        for speci in species:
            shutil.copy(self.path_to_species_files + speci + '.xml', self.directory)
        self.write_input_xml()
        self.write_slurm_script()

    def write_input_xml(self):
        xml_tree_str = exciting_input_xml_str(self.structure, self.ground_state, title=self.name)

        with open(self.directory / "input.xml", "w") as fid:
            fid.write(xml_tree_str)

    def write_slurm_script(self):
        default_env_vars = OrderedDict([('EXE',
                                         '/mnt/beegfs2018/scratch/peschelf/code/release/exciting/bin/exciting_mpismp'),
                                        ('OUT', 'terminal.out')])
        default_module_envs = ['intel-oneapi/2021.4.0']

        set_run_script = slurm.set_slurm_script
        run_script = set_run_script(self.slurm_directives, default_env_vars, default_module_envs)
        with open(self.directory / "submit_run.sh", "w") as fid:
            fid.write(run_script)

    def run(self) -> SubprocessRunResults:
        """ Puts a calculation in the slurm queue.
        """
        execution_list = ['sbatch', str(self.directory) + '/submit_run.sh']
        time_start = time.time()
        result = subprocess.run(execution_list,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        total_time = time.time() - time_start
        return SubprocessRunResults(result.stdout, result.stderr, result.returncode, total_time)

    def parse_output(self) -> Union[dict, FileNotFoundError]:
        """
        """
        info_out: dict = groundstate_parser.parse_info_out("INFO.OUT")
        return {**info_out}

import shutil
import subprocess
import time
from typing import Optional, Union
from collections import OrderedDict

import schedule
from excitingtools.input.input_xml import exciting_input_xml_str
from excitingtools.parser import groundstate_parser
from excitingtools.runner import SubprocessRunResults
from excitingtools.input.ground_state import ExcitingGroundStateInput
from excitingtools.input.structure import ExcitingStructure
from excitingworkflow.src.calculation_io import CalculationIO
from exgw.src.job_schedulers import slurm


def find_job_state(job_info: str) -> str:
    """
    Find the job state in the scontrol show job JOBID output
    :param job_info:
    :return: the job state
    """
    job_info = job_info.split()
    for info in job_info:
        if info.split('=')[0] == 'JobState':
            return info.split('=')[1]


class ExcitingGSSlurmCalculation(CalculationIO):
    """
    Function for generating an exciting calculation. You can write the necessary input files, execute the calculation
    and parse the results.
    """
    def __init__(self,
                 name: str,
                 directory: CalculationIO.path_type,
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

    @staticmethod
    def is_exited(jobnumber: int) -> bool:
        execution_list = ['scontrol', 'show', 'job', str(jobnumber)]
        result = subprocess.run(execution_list,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        return find_job_state(str(result.stdout)) == 'COMPLETED'

    def wait_calculation_finish(self, jobnumber: int):
        schedule.clear()
        job1 = schedule.every(5).seconds
        job1.do(self.is_exited, jobnumber=jobnumber)
        schedule.run_all()

        job_finished = False
        while not job_finished:
            should_run_jobs = (job for job in schedule.jobs if job.should_run)
            for job in sorted(should_run_jobs):
                job_finished = job.run()
            time.sleep(1)

    def submit_to_slurm(self) -> int:
        """ Puts a calculation in the slurm queue.
        :return: jobnumber in the queue
        """
        execution_list = ['sbatch', 'submit_run.sh']
        result = subprocess.run(execution_list,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                cwd=self.directory)
        if not result.returncode == 0:
            assert RuntimeError(f"Couldn't put the calculation into queue: {result.stderr}")
        return int(result.stdout.split()[3])

    def run(self) -> SubprocessRunResults:
        """
        Executes a calculation. Put in queue, wait for finish.
        """
        time_start = time.time()
        jobnumber = self.submit_to_slurm()
        self.wait_calculation_finish(jobnumber)
        total_time = time.time() - time_start
        # TODO(Fab): Add handling for errors and time out
        returncode = 0
        with open(self.directory / ('slurm-' + str(jobnumber) + '.out')) as fid:
            stdout = fid.readlines()
        with open(self.directory / 'terminal.out') as fid:
            stderr = fid.readlines()
        return SubprocessRunResults(stdout, stderr, returncode, total_time)

    def parse_output(self) -> Union[dict, FileNotFoundError]:
        """
        """
        info_out: dict = groundstate_parser.parse_info_out(self.directory / "INFO.OUT")
        return {**info_out}

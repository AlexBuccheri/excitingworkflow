import subprocess
import time
from typing import Optional, Union
from collections import OrderedDict

import schedule
from excitingtools.input.xs import ExcitingXSInput
from excitingtools.runner import SubprocessRunResults, BinaryRunner
from excitingtools.input.ground_state import ExcitingGroundStateInput
from excitingtools.input.structure import ExcitingStructure
from excitingworkflow.src.exciting_calculation import ExcitingCalculation
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


class ExcitingSlurmCalculation(ExcitingCalculation):
    """
    Function for generating an exciting calculation on dune with slurm. You can write the necessary input files,
    execute the calculation and parse the results.
    """
    def __init__(self,
                 name: str,
                 directory: ExcitingCalculation.path_type,
                 structure: Union[ExcitingStructure, ExcitingCalculation.path_type],
                 path_to_species_files: Union[ExcitingCalculation.path_type, ExcitingCalculation],
                 ground_state: Union[ExcitingGroundStateInput, ExcitingCalculation.path_type],
                 xs: Optional[ExcitingXSInput] = None,
                 slurm_directives: Optional[OrderedDict] = None):
        """
        :param name: title of the calculation
        :param directory: where to run the calculation
        :param structure: Object containing the xml structure info
        :param path_to_species_files: where to find the species files OR old ExcitingCalculation object from
        which the path is taken
        :param ground_state: Object containing the xml groundstate info OR path to already performed gs calculation
        from where the necessary files STATE.OUT and EFERMI.OUT are copied
        :param xs: optional xml xs info
        :param slurm_directives: slurm infos to specify how the calculation should be run
        """
        super().__init__(name, directory, structure, path_to_species_files, ground_state, BinaryRunner('', '', 1, 1),
                         xs)
        self.jobnumber = None
        self.status = None
        default_directives = slurm.set_slurm_directives(job_name=self.name,
                                                        time=[0, 24, 0, 0],
                                                        partition='all',
                                                        exclusive=True,
                                                        nodes=1,
                                                        ntasks_per_node=8,
                                                        cpus_per_task=4,
                                                        hint='nomultithread')
        self.slurm_directives = slurm_directives or default_directives

    def write_slurm_script(self):
        default_env_vars = OrderedDict([('EXE',
                                         '/mnt/beegfs2018/scratch/peschelf/code/release/exciting/bin/exciting_mpismp'),
                                        ('OUT', 'terminal.out')])
        default_module_envs = ['intel-oneapi/2021.4.0']

        run_script = slurm.set_slurm_script(self.slurm_directives, default_env_vars, default_module_envs)
        with open(self.directory / "submit_run.sh", "w") as fid:
            fid.write(run_script)

    def is_exited(self) -> bool:
        execution_list = ['scontrol', 'show', 'job', str(self.jobnumber)]
        result = subprocess.run(execution_list,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        self.status = find_job_state(str(result.stdout))
        return self.status in ['COMPLETED', 'TIMEOUT', 'FAILED']

    def wait_calculation_finish(self):
        schedule.clear()
        job1 = schedule.every(30).seconds
        job1.do(self.is_exited)
        schedule.run_all()

        job_finished = False
        while not job_finished:
            should_run_jobs = (job for job in schedule.jobs if job.should_run)
            for job in sorted(should_run_jobs):
                job_finished = job.run()
            time.sleep(1)

    def submit_to_slurm(self):
        """ Puts a calculation in the slurm queue.
        """
        execution_list = ['sbatch', 'submit_run.sh']
        result = subprocess.run(execution_list,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                cwd=self.directory)
        if not result.returncode == 0:
            assert RuntimeError(f"Couldn't put the calculation into queue: {result.stderr}")
        self.jobnumber = int(result.stdout.split()[3])

    def run(self, wait_for_finish: bool = True) -> Union[SubprocessRunResults, None]:
        """
        Executes a calculation. Put in queue, wait for finish.
        """
        time_start = time.time()
        self.submit_to_slurm()
        print(f'Put calculation into queue, JOBID={self.jobnumber}')
        if not wait_for_finish:
            return
        self.wait_calculation_finish()
        return self.get_runresults(time_start)

    def get_runresults(self, time_start: float = None) -> SubprocessRunResults:
        if not self.is_exited():
            raise RuntimeError("Calculation isn't finished yet!")
        if time_start is None:
            total_time = 0
        else:
            total_time = time.time() - time_start
        # TODO(Fab): Add handling for errors and time out
        returncode = 0
        if self.status == 'TIMEOUT':
            print("TIMEOUT reached!")
        elif self.status == 'FAILED':
            returncode = 1
        with open(self.directory / ('slurm-' + str(self.jobnumber) + '.out')) as fid:
            stderr = fid.readlines()
        with open(self.directory / 'terminal.out') as fid:
            stdout = fid.readlines()
        return SubprocessRunResults(stdout, stderr, returncode, total_time)

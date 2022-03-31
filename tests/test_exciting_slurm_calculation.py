from excitingworkflow.src.exciting_slurm_calculation import ExcitingSlurmCalculation
from excitingtools.input.ground_state import ExcitingGroundStateInput
from excitingtools.input.structure import ExcitingStructure
from excitingtools.input.xs import ExcitingXSInput
from exgw.src.job_schedulers import slurm


def initialize_gs_calculation(directory: str) -> ExcitingSlurmCalculation:
    lattice = [[0.5, 0.0, 0.0], [0.0, 0.5, 0.0], [0.0, 0.0, 0.5]]
    atoms = [{'species': 'Li', 'position': [0, 0, 0]},
             {'species': 'F', 'position': [0.5, 0.5, 0.5]}]
    structure = ExcitingStructure(atoms, lattice, '/mnt/beegfs2018/scratch/peschelf/code/exciting/species/',
                                  structure_properties={'autormt': True},
                                  crystal_properties={'scale': 7.608})
    groundstate = ExcitingGroundStateInput(ngridk=[3, 3, 3], rgkmax=5.0, gmaxvr=15, nempty=50, do='fromscratch',
                                           xctype='GGA_PBE_SOL', lmaxmat=16, lmaxvr=16, lmaxapw=16, epschg=0.01,
                                           epsengy=0.01, epspot=0.01)

    slurm_directives = slurm.set_slurm_directives(job_name='test2',
                                                  time=[0, 0, 1, 0],
                                                  partition='debug',
                                                  exclusive=True,
                                                  nodes=1,
                                                  ntasks_per_node=4,
                                                  cpus_per_task=4,
                                                  hint='nomultithread')

    return ExcitingSlurmCalculation('test2', directory, structure, groundstate, slurm_directives=slurm_directives)


def test_run_gs_calculation(tmpdir):
    """
    Test a simple ground_state calculation with slurm.
    """
    calculation1 = initialize_gs_calculation(tmpdir)
    calculation1.write_inputs()
    print('Calculation starts ...')
    run_result = calculation1.run()
    print(run_result.stdout)
    print(run_result.stderr)
    print(run_result.return_code)
    print(run_result.process_time)
    if not run_result.success:
        assert RuntimeError('Calculation error occured!')
    result = calculation1.parse_output()
    # TODO: Add asserts to see if calculation was successful


def initialize_bse_calculation(directory: str) -> ExcitingSlurmCalculation:
    lattice = [[0.5, 0.0, 0.0], [0.0, 0.5, 0.0], [0.0, 0.0, 0.5]]
    atoms = [{'species': 'Li', 'position': [0, 0, 0]},
             {'species': 'F', 'position': [0.5, 0.5, 0.5]}]
    structure = ExcitingStructure(atoms, lattice, '/mnt/beegfs2018/scratch/peschelf/code/exciting/species/',
                                  structure_properties={'autormt': True},
                                  crystal_properties={'scale': 7.608})
    groundstate = ExcitingGroundStateInput(ngridk=[3, 3, 3], rgkmax=5.0, gmaxvr=15, nempty=50, do='fromscratch',
                                           xctype='GGA_PBE_SOL')
    xs_attributes = {'broad': 0.327, 'ngridk': [2, 2, 2], 'nempty': 30, 'ngridq': [2, 2, 2], 'gqmax': 2.5,
                     'tappinfo': True, 'tevout': True, 'vkloff': [0.05, 0.03, 0.13]}
    bse_attributes = {'bsetype': 'singlet', 'xas': True, 'nstlxas': [1, 30], 'xasatom': 1, 'xasedge': 'K',
                      'xasspecies': '1'}
    energywindow_attributes = {'intv': [50, 300], 'points': 5000}
    screening_attributes = {'screentype': 'full', 'nempty': 30}
    plan_input = ['xsgeneigvec', 'writepmatxs', 'scrgeneigvec', 'scrwritepmat', 'screen', 'scrcoulint', 'exccoulint',
                  'bse']
    qpointset_input = [[0, 0, 0]]
    xs = ExcitingXSInput("BSE", xs=xs_attributes,
                         BSE=bse_attributes,
                         energywindow=energywindow_attributes,
                         screening=screening_attributes,
                         qpointset=qpointset_input,
                         plan=plan_input)

    slurm_directives = slurm.set_slurm_directives(job_name='test1',
                                                  time=[0, 1, 0, 0],
                                                  partition='debug',
                                                  exclusive=True,
                                                  nodes=1,
                                                  ntasks_per_node=4,
                                                  cpus_per_task=4,
                                                  hint='nomultithread')

    return ExcitingSlurmCalculation('test1', directory, structure, groundstate, xs, slurm_directives)


def test_run_full_bse_calculation(tmpdir):
    """
    Test for a full groundstate + bse calculation with slurm.
    """
    calculation1 = initialize_bse_calculation(tmpdir)
    calculation1.write_inputs()
    print('Calculation starts ...')
    run_result = calculation1.run()
    print(run_result.stdout)
    print(run_result.stderr)
    print(run_result.return_code)
    print(run_result.process_time)
    if not run_result.success:
        assert RuntimeError('Calculation error occured!')
    result = calculation1.parse_output()
    # TODO: Add asserts to see if calculation was successful

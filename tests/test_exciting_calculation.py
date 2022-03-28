from excitingworkflow.src.exciting_groundstate_calculation import ExcitingGroundStateCalculation
from excitingtools.runner import BinaryRunner
from excitingtools.input.ground_state import ExcitingGroundStateInput
from excitingtools.input.structure import ExcitingStructure
from excitingtools.input.xs import ExcitingXSInput


def test_ExcitingCalculation(tmpdir):
    runner1 = BinaryRunner('exciting_smp', './', 4, 600)
    cubic_lattice = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    arbitrary_atoms = [{'species': 'Li', 'position': [0, 0, 0]},
                       {'species': 'F', 'position': [1, 0, 0]}]
    structure = ExcitingStructure(arbitrary_atoms, cubic_lattice, '/home/fabi/code/exciting/species/',
                                  structure_properties={'autormt': True})
    groundstate = ExcitingGroundStateInput(ngridk=[8, 8, 8], rgkmax=9.0, gmaxvr=20, nempty=50)
    xs_attributes = {'broad': 0.327, 'ngridk': [8, 8, 8], 'nempty': 100, 'ngridq': [8, 8, 8], 'gqmax': 4.0,
                     'tappinfo': True, 'tevout': True, 'vkloff': [0.05, 0.03, 0.13]}
    bse_attributes = {'bsetype': 'singlet', 'xas': True, 'nstlxas': [1, 100], 'xasatom': 1, 'xasedge': 'K',
                      'xasspecies': '1'}
    energywindow_attributes = {'intv': [50, 300], 'points': 5000}
    screening_attributes = {'screentype': 'full', 'nempty': 100}
    plan_input = ['xsgeneigvec', 'writepmatxs', 'scrgeneigvec', 'scrwritepmat', 'screen', 'scrcoulint', 'exccoulint',
                  'bse']
    qpointset_input = [[0, 0, 0]]
    xs = ExcitingXSInput("BSE", xs=xs_attributes,
                         BSE=bse_attributes,
                         energywindow=energywindow_attributes,
                         screening=screening_attributes,
                         qpointset=qpointset_input,
                         plan=plan_input)
    calculation1 = ExcitingGroundStateCalculation('test1', str(tmpdir), runner1, structure, groundstate, xs)

    calculation1.write_inputs()

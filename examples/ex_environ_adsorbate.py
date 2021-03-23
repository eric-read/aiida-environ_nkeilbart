from aiida.orm.utils import load_node, load_code
from aiida.engine import submit
from aiida.orm import Dict, StructureData
from aiida.orm.nodes.data.upf import get_pseudos_from_structure
from aiida.plugins.factories import DataFactory, WorkflowFactory
# Once this runs right, just comment out dicts and load_node
# try loading aiida-environ, everything stored as nodes already
code = load_code(109)
workchain = WorkflowFactory('environ.pw.adsorbate')
builder = workchain.get_builder()
builder.metadata.label = "Environ test"
builder.metadata.description = "Test of environ adsorbate workchain"
builder.pw.metadata.options.resources = {'num_machines': 1}
builder.pw.metadata.options.max_wallclock_seconds = 30 * 60
builder.pw.code = code

# read in structure from ase
import ase.io
import numpy as np
a = ase.io.read("adsorbate.cif")
nat = a.get_global_number_of_atoms()
# remove the adsorbate, the cif file contains two sites that we want to take
siteA = a.pop(nat-1)
siteB = a.pop(nat-2)
structure = StructureData(ase=a)
pp = get_pseudos_from_structure(structure, 'SSSPe')
vacancies = np.zeros((2, 3,))
vacancies[0, :] = siteA.position
vacancies[1, :] = siteB.position
ArrayData = DataFactory('array')
array = ArrayData()
array.set_array('matrix', vacancies)
# set the builder
builder.structure = structure
builder.vacancies = array

kpoints = load_node(285)
parameters = {
    "CONTROL": {
        "calculation": "scf",
        "restart_mode": "from_scratch",
        "tprnfor": True
    },
    'SYSTEM': {
        'ecutrho': 300,
        'ecutwfc': 30
    }, 
    'ELECTRONS': {
        'conv_thr': 5.e-9,
        'diagonalization': 'cg',
        'mixing_beta': 0.4,
        'electron_maxstep': 200
    }
}
environ_parameters = {
    "ENVIRON": {
        "environ_restart": False,
        "env_electrostatic": True,
        "environ_thr": 0.1
    },                                                   
    "BOUNDARY": {
        "alpha": 1.12,
        "radius_mode": "muff",
        "solvent_mode": "ionic"
    },
    "ELECTROSTATIC": {
        "tol": 1e-10
    }                           
}

builder.pw.kpoints = kpoints
builder.pw.parameters = Dict(dict=parameters)
builder.pw.pseudos = pp
builder.pw.environ_parameters = Dict(dict=environ_parameters)

builder.site_index = [0, 0]
builder.possible_adsorbates = ['O', 'H']
builder.adsorbate_index = [[1, 1], [1, 1]]

print(builder)
calculation = submit(builder)
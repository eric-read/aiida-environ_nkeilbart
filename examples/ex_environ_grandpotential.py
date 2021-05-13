from aiida.orm.utils import load_node, load_code
from aiida.engine import submit
from aiida.orm import List, Dict, StructureData
from aiida.orm.nodes.data.upf import get_pseudos_from_structure
from aiida.plugins.factories import WorkflowFactory
import node_assignment

# Once this runs right, just comment out dicts and load_node
# try loading aiida-environ, everything stored as nodes already
code = load_code(node_assignment.ENVIRON_CODE_PK)
workchain = WorkflowFactory('environ.pw.grandpotential')
builder = workchain.get_builder()
builder.metadata.label = "Environ test"
builder.metadata.description = "Test of environ adsorbate workchain"
builder.base.pw.metadata.options.resources = {'num_machines': 1}
builder.base.pw.metadata.options.max_wallclock_seconds = 30 * 60
builder.base.pw.code = code

# read in structure from ase
from ase.build import fcc111
import numpy as np
a = fcc111('Al', size=(4, 4, 1), vacuum=10.0)
structure = StructureData(ase=a)
positions = a.get_positions()[::4]
positions[:, 2] += 1.5
pp = get_pseudos_from_structure(structure, 'SSSPe')
vacancies = []
vacancies.append((positions[0]))
vacancies.append((positions[1]))
vacancies.append((positions[2]))
vacancies.append((positions[3]))
# set the builder
builder.size = (())
builder.structure = structure
builder.vacancies = List(list=vacancies)

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

builder.base.kpoints = load_node(node_assignment.get("SIMPLE_KPOINTS_PK"))
builder.base.pw.parameters = load_node(node_assignment.get("SIMPLE_PARAMETERS_PK"))
builder.base.pw.pseudos = pp
builder.base.pw.environ_parameters = Dict(dict=environ_parameters)

print(builder)
calculation = submit(builder)
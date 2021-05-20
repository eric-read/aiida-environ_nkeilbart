from aiida.engine import calcfunction
from aiida_environ.utils.occupancy import Occupancy
from aiida_environ.utils.graph import Graph
from aiida.plugins import DataFactory


StructureData = DataFactory('structure')
List = DataFactory('list')


@calcfunction
def adsorbate_gen_multitype(site_index, possible_adsorbates, adsorbate_index, structure, vacancies):
    # Setup based on inputs
    points_per_site = [0] * (max(site_index) + 1)
    adsorbate_per_site = [0] * (max(site_index) + 1)
    for i in site_index:
        points_per_site[i] += 1
    for i, site in enumerate(adsorbate_index):
        adsorbate_per_site[i] = sum(site)
    assert len(points_per_site) == len(adsorbate_per_site)  
    o = Occupancy(points_per_site, adsorbate_per_site)
    g = Graph()
    # note that the current implementation clones the configuration list (deepcopy) which may get expensive but for our purposes should be fine
    occ_list = list(o)
    # again, here things get expensive if we take the difference each time but for these sizes it's okay
    for i, occ1 in enumerate(occ_list):
        g.add_vertex(occ1)
        for j, occ2 in enumerate(occ_list):
            if i <= j:
                continue
            if occ1 - occ2 == 1:
                g.add_edge(i, j)

    n_max = 0
    for v in g.vertices:
        n_max = max(v.connections, n_max)

    def vertices_to_labels(vertex_list):
        labels = []
        for v in vertex_list:
            labels.append(v.configuration)
        ads_max_list = []
        for x in labels:
            list1 = []
            for y in x:
                list2 = []
                for z in y:
                    if (z == 0):
                        list2.append(0)
                    else:
                        list2.append(possible_adsorbates[z - 1])
                list1.append(list2)
            ads_max_list.append(list1)
        return ads_max_list

    max_list = g.get_vertices_with_connections(n_max)
    max_list = vertices_to_labels(max_list) 

    struct_list = []
    for i, ads_configuration in enumerate(max_list):
        new_structure = StructureData(cell=structure.cell)
        for site in structure.sites:
            new_structure.append_atom(position=site.position, symbols=site.kind_name)
        for site_configuration, pos in zip(ads_configuration, vacancies):
            for sp in site_configuration:
                if sp != 0:
                    new_structure.append_atom(position=pos, symbols=sp)
        new_structure.store()
        struct_list.append(new_structure.pk)

    struct_list = List(list=struct_list)
                    
    return struct_list
from gladier import GladierBaseTool, generate_flow_definition
from typing import Dict, Any

def create_phil(**data: Dict[str, Any]) -> str:
    """Create a phil file for dials-stills if one doesn't already exist.
    
    The Phil file uses a template set directly on the script and can be updated according to new options on dials.
    This function reads beamline JSON data and creates a phil file with appropriate parameters.
    
    Args:
        data: Dictionary containing the following keys:
            - data_dir: Path where the raw (cbf) data is stored
            - proc_dir: Path to where dials will run and save results
            - run_num: Set the beamline json being used for this particular phil
            - unit_cell: Optional unit cell parameter to override JSON value
            - beamx: Optional beam x position (default: -214.400)
            - beamy: Optional beam y position (default: 218.200)
            - nproc: Optional number of processors (default: 32)
            - mask: Optional mask file path (default: 'mask.pickle')
            
    Returns:
        str: Path to the created phil file
        
    Note:
        If a file xy.json exists in the data_dir it will override beamx and beamy variables
    """
    import json
    import os
    from string import Template

    data_dir = data['data_dir']
    proc_dir = data['proc_dir']
    run_num  = data['run_num']

    if not os.path.exists(proc_dir):
        os.makedirs(proc_dir)
        
    phil_name = f"{proc_dir}/process_{run_num}.phil"

    if os.path.isfile(phil_name):
        return phil_name
    
    ##Getting optional variables
    unit_cell = data.get('unit_cell', None)
    beamx = data.get('beamx', -214.400)
    beamy = data.get('beamy', 218.200)
    nproc = data.get('nproc', 32)
    mask_file = data.get('mask', 'mask.pickle')

    ##opening existing files
    beamline_json = os.path.join(data_dir,f"beamline_run{run_num}.json")
    xy_json = os.path.join(data_dir,'xy.json')
    mask = os.path.join(data_dir,mask_file)

    beamline_data = None

    try:
        with open(beamline_json, 'r') as fp:
            beamline_data = json.loads(fp.read())

        if not unit_cell:
            unit_cell = beamline_data['user_input']['unit_cell']

        unit_cell = unit_cell.replace(",", " ")
        space_group = beamline_data['user_input']['space_group']
        det_distance = float(beamline_data['beamline_input']['det_distance']) * -1.0
    except:
        pass

    try:
        with open(xy_json, 'r') as fp:
            xy_data = json.loads(fp.read())
        beamx = xy_data['beamx']
        beamy = xy_data['beamy']
    except:
        pass


    template_data = {'det_distance': det_distance,
                     'unit_cell': unit_cell,
                     'nproc': nproc,
                     'space_group': space_group,
                     'beamx': beamx,
                     'beamy': beamy,
                     'mask': mask}

    template_phil = Template("""spotfinder.lookup.mask=$mask
integration.lookup.mask=$mask
spotfinder.filter.min_spot_size=2
significance_filter.enable=True
#significance_filter.isigi_cutoff=1.0
mp.nproc = $nproc
mp.method=multiprocessing
output.composite_output=False
refinement.parameterisation.detector.fix=none
geometry {
  detector {
      panel {
                fast_axis = 0.9999673162585729, -0.0034449798523932267, -0.007314268824966957
                slow_axis = -0.0034447744696749034, -0.99999406591948, 4.0677756813531234e-05
                origin    = $beamx, $beamy, $det_distance
                }
            }
         }
indexing {
  known_symmetry {
    space_group = $space_group
    unit_cell = $unit_cell
  }
  stills.indexer=stills
  stills.method_list=fft1d
  multiple_lattice_search.max_lattices=3
}""")
    phil_data = template_phil.substitute(template_data)

    with open(phil_name, 'w') as fp:
        fp.write(phil_data)
    return phil_name 

@generate_flow_definition(modifiers={
    'create_phil': {'endpoint': 'compute_endpoint',
                           'ExceptionOnActionFailure': True,
                           }
})
class CreatePhil(GladierBaseTool):
    flow_input = {}
    required_input = [
        'data_dir',
        'proc_dir',
        'run_num',
        'compute_endpoint',
    ]
    funcx_functions = [create_phil]

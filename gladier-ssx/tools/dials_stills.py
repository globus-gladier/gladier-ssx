from gladier import GladierBaseTool, generate_flow_definition
from typing import Dict, Any, Tuple

def dials_stills(**data: Dict[str, Any]) -> Tuple[str, str, str]:
    """Run dials-stills processing on CBF files.
    
    This function processes a batch of CBF files using dials.stills_process with
    the specified phil file and parameters.
    
    Args:
        data: Dictionary containing the following keys:
            - data_dir: Path where the raw (cbf) data is stored
            - proc_dir: Path to where dials will run and save results
            - run_num: Set the beamline json and phil being used
            - chip_name: Name of the chip being processed
            - cbf_num: Gives the # of the trigger for this flow
            - stills_batch_size: Gives the amount of cbf's processed on this instance
            - dials_path: Optional path to dials installation (default: '/dials')
            - timeout: Optional timeout for faster/slower failure (default: 1200)
            
    Returns:
        Tuple[str, str, str]: (command, stdout, stderr) from the dials.stills_process execution
    """
    import os
    import subprocess

    data_dir = data['data_dir']
    proc_dir = data['proc_dir']
    run_num = data['run_num']
    chip_name = data['chip_name']
    cbf_num = data['cbf_num']
    batch_size = data['stills_batch_size']

    phil_name = f"{proc_dir}/process_{run_num}.phil"

    cbf_start = cbf_num - batch_size + 1
    cbf_end = cbf_num

    input_files = f"{chip_name}_{run_num}_{{{str(cbf_start).zfill(5)}..{str(cbf_end).zfill(5)}}}.cbf"

    timeout = data.get('timeout', 1200)

    logname = 'log-' + data['filename'].replace('.cbf','')
    
    dials_path = data.get('dials_path','/dials')
    cmd = f'source {dials_path}/dials && timeout {timeout} dials.stills_process {phil_name} {data_dir}/{input_files} > {logname}.txt'

    os.chdir(proc_dir) 
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             shell=True, executable='/bin/bash')
    
    return cmd, str(res.stdout), str(res.stderr)


@generate_flow_definition(modifiers={
    'dials_stills': {'WaitTime':7200}
})
class DialsStills(GladierBaseTool):
    flow_input = {}
    required_input = [
        'data_dir',
        'proc_dir',
        'run_num',
        'chip_name',
        'cbf_num',
        'stills_batch_size',
        'funcx_endpoint_compute',
    ]
    funcx_functions = [dials_stills]

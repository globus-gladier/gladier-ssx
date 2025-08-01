from gladier import GladierBaseTool, generate_flow_definition
from typing import Dict, Any, List
import os
import subprocess
from subprocess import PIPE
import glob


def run_initial_proc(**data: Dict[str, Any]) -> tuple[str, str, str]:
    """Process first N master files as a group using a single xia2.ssx command.
    
    This tool processes the first N master.h5 files as a group using xia2.ssx.
    Output goes to initial_refinement/ directory.
    
    Args:
        data: Dictionary containing the following keys:
            - raster_dir: Path to the raster directory containing master.h5 files
            - output_dir: Path where the initial refinement results will be stored (default: 'initial_refinement')
            - n_files: Number of master files to process (default: 2)
            - phil_file: Path to the phil file to use for processing (default: 'run.phil')
            - dials_path: Path to dials installation (default: '/dials')
            
    Returns:
        tuple: (command, stdout, stderr) from the xia2.ssx execution
    """
    data_dir = data['data_dir']
    raster_dir = data.get('raster_dir', 'raster')
    output_dir = data.get('output_dir', 'initial_refinement')
    n_files = data.get('n_files', 2)
    phil_file = data.get('phil_file', 'run.phil')
    
    os.chdir(data_dir)
    # Create output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Change to output directory
    os.chdir(output_dir)
    
    # Find master.h5 files in raster directory
    master_files = glob.glob(f"../{raster_dir}/*_master.h5")
    master_files.sort()
    
    if not master_files:
        raise RuntimeError(f"No master.h5 files found in {raster_dir}/")
    
    # Take first N files
    selected_files = master_files[:n_files]
    
    # Build image arguments
    image_args = []
    for master_file in selected_files:
        image_args.append(f"image={master_file}")
    
    # Construct the full command
    cmd_parts = [
        "xia2.ssx"
    ] + image_args + [
        f"--phil ../{phil_file}"
    ]
    
    cmd = " ".join(cmd_parts)
    
    # Execute the command
    result = subprocess.run(
        cmd,
        stdout=PIPE,
        stderr=PIPE,
        shell=True,
        executable='/bin/bash',
        text=True
    )
    
    return cmd, result.stdout, result.stderr


@generate_flow_definition(modifiers={
    'run_initial_proc': {
        'WaitTime': 7200,
        'ExceptionOnActionFailure': True
    }
})
class RunInitialProc(GladierBaseTool):
    """Gladier tool for initial processing of master files using xia2.ssx."""
    flow_input = {}
    required_input = [
        'compute_endpoint',
    ]
    funcx_functions = [run_initial_proc] 
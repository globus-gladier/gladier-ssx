from gladier import GladierBaseTool, generate_flow_definition
from typing import Dict, Any, List
import os
import subprocess
from subprocess import PIPE
import glob


def run_refined_proc(**data: Dict[str, Any]) -> tuple[str, str, str]:
    """Re-run xia2.ssx on all master.h5 files using refined unit cell.
    
    This tool processes each master.h5 file individually using xia2.ssx with
    a refined geometry file. Results are stored in refined/ref_*/ directories.
    
    Args:
        data: Dictionary containing the following keys:
            - raster_dir: Path to the raster directory containing master.h5 files
            - refined_dir: Path where refined processing results will be stored (default: 'refined')
            - refined_geometry: Path to the refined geometry file (default: '../../initial_refinement/geometry_refinement/refined.expt')
            - phil_file: Path to the phil file to use for processing (default: 'run.phil')
            - dials_path: Path to dials installation (default: '/dials')
            
    Returns:
        tuple: (command, stdout, stderr) from the xia2.ssx execution
    """
    raster_dir = data.get('raster_dir', 'raster')
    refined_dir = data.get('refined_dir', 'refined')
    refined_geometry = data.get('refined_geometry', '../../initial_refinement/geometry_refinement/refined.expt')
    phil_file = data.get('phil_file', 'run.phil')
    
    # Find all master.h5 files
    master_files = glob.glob(f"{raster_dir}/*_master.h5")
    master_files.sort()
    
    if not master_files:
        raise RuntimeError(f"No master.h5 files found in {raster_dir}/")
    
    # Process each file individually
    all_commands = []
    all_stdout = []
    all_stderr = []
    
    for master_file in master_files:
        # Extract run number from filename
        filename = os.path.basename(master_file)
        run_name = filename.replace('_master.h5', '')
        
        # Create output directory for this run
        outdir = f"{refined_dir}/ref_{run_name}"
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        
        # Change to output directory
        original_dir = os.getcwd()
        os.chdir(outdir)
        
        try:
            # Construct the command
            cmd_parts = [
                "xia2.ssx",
                f"image=../../{master_file}",
                f"--phil ../../{phil_file}",
                f"reference_geometry=../../{refined_geometry}"
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
            
            all_commands.append(cmd)
            all_stdout.append(result.stdout)
            all_stderr.append(result.stderr)
            
        finally:
            # Return to original directory
            os.chdir(original_dir)
    
    # Combine all outputs
    combined_cmd = "\n".join(all_commands)
    combined_stdout = "\n".join(all_stdout)
    combined_stderr = "\n".join(all_stderr)
    
    return combined_cmd, combined_stdout, combined_stderr


@generate_flow_definition(modifiers={
    'run_refined_proc': {
        'WaitTime': 7200,
        'ExceptionOnActionFailure': True
    }
})
class RunRefinedProc(GladierBaseTool):
    """Gladier tool for refined processing of master files using xia2.ssx."""
    
    flow_input = {}
    required_input = [
        'compute_endpoint',
    ]
    funcx_functions = [run_refined_proc] 
from gladier import GladierBaseTool, generate_flow_definition
from typing import Dict, Any, List
import os
import subprocess
from subprocess import PIPE
import glob


def run_prime(**data: Dict[str, Any]) -> tuple[str, str, str]:
    """Run PRIME using directories under refined/ref_*/batch_1/.
    
    This tool collects batch_1 directories from refined processing and runs PRIME
    on them. It creates a phil file with input block containing all batch directories
    and runs prime with the specified parameters.
    
    Args:
        data: Dictionary containing the following keys:
            - refined_dir: Path to the refined directory containing ref_*/batch_1 subdirectories
            - output_dir: Path where PRIME results will be stored (default: 'prime_results')
            - unit_cell: Target unit cell for PRIME (default: '78.95,78.85,38.10,90,90,90')
            - space_group: Target space group for PRIME (default: 'P43212')
            - d_min: Minimum d-spacing for merging (default: 1.5)
            - sigma_min: Minimum sigma for selection (default: 2.0)
            - isigi_cutoff: I/sigma cutoff for selection (default: 1.5)
            - frame_accept_min_cc: Minimum CC for frame acceptance (default: 0.3)
            
    Returns:
        tuple: (command, stdout, stderr) from the prime execution
    """
    refined_dir = data.get('refined_dir', 'refined')
    output_dir = data.get('output_dir', 'prime_results')
    unit_cell = data.get('unit_cell', '78.95,78.85,38.10,90,90,90')
    space_group = data.get('space_group', 'P43212')
    d_min = data.get('d_min', 1.5)
    sigma_min = data.get('sigma_min', 2.0)
    isigi_cutoff = data.get('isigi_cutoff', 1.5)
    frame_accept_min_cc = data.get('frame_accept_min_cc', 0.3)
    
    # Create output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Collect input batch directories (same logic as xia2.ssx_reduce)
    batch_dirs = []
    for ref_dir in os.listdir(refined_dir):
        ref_path = os.path.join(refined_dir, ref_dir)
        if os.path.isdir(ref_path):
            batch_path = os.path.join(ref_path, "batch_1")
            if os.path.exists(batch_path):
                batch_dirs.append(batch_path)
    
    if not batch_dirs:
        raise RuntimeError("No batch_1 directories found in refined/ref_*/")
    
    # Sort directories for consistent ordering
    batch_dirs.sort()
    
    # Write input block with all directories
    input_block = "input {\n"
    for batch_dir in batch_dirs:
        input_block += f"  directory = {batch_dir}\n"
    input_block += "}\n"
    
    # Create the full prime.phil
    prime_phil_content = f"""{input_block}

output {{
  prefix = {output_dir}/prime
  log = {output_dir}/prime.log
}}

target_unit_cell = {unit_cell}
target_space_group = {space_group}

scaling {{
  model = ml_iso
}}

merging {{
  d_min = {d_min}
  partiality_model = unity
}}

selection {{
  sigma_min = {sigma_min}
  isigi_cutoff = {isigi_cutoff}
  frame_accept_min_cc = {frame_accept_min_cc}
}}
"""
    
    # Write prime.phil file
    prime_phil_path = os.path.join(output_dir, "prime.phil")
    with open(prime_phil_path, 'w') as f:
        f.write(prime_phil_content)
    
    # Run PRIME
    cmd = f"prime {prime_phil_path}"
    
    result = subprocess.run(
        cmd,
        stdout=PIPE,
        stderr=PIPE,
        shell=True,
        text=True
    )
    
    return cmd, result.stdout, result.stderr


@generate_flow_definition(modifiers={
    'run_prime': {
        'WaitTime': 7200,
        'ExceptionOnActionFailure': True
    }
})
class RunPrime(GladierBaseTool):
    """Gladier tool for running PRIME using batch directories from refined processing."""
    
    flow_input = {}
    required_input = [
        'refined_dir',
        'output_dir',
        'unit_cell',
        'space_group',
        'funcx_endpoint_compute',
    ]
    funcx_functions = [run_prime] 
from gladier import GladierBaseTool, generate_flow_definition
from typing import Dict, Any, Optional
import os
import subprocess
from subprocess import PIPE


def merge_all(**data: Dict[str, Any]) -> tuple[str, str, str]:
    """Merge all refined SSX batches using xia2.ssx_reduce.
    
    This tool collects batch_1 directories under refined/ref_*/ and merges them
    using xia2.ssx_reduce. The result will be prime.mtz in final_merge/.
    
    Args:
        data: Dictionary containing the following keys:
            - refined_dir: Path to the refined directory containing ref_*/batch_1 subdirectories
            - output_dir: Path where the merged results will be stored (default: 'final_merge')
            - phil_file: Path to the phil file to use for merging (default: 'run.phil')
            - dials_path: Path to dials installation (default: '/dials')
            
    Returns:
        tuple: (command, stdout, stderr) from the xia2.ssx_reduce execution
    """
    refined_dir = data.get('refined_dir', 'refined')
    output_dir = data.get('output_dir', 'final_merge')
    phil_file = data.get('phil_file', 'run.phil')
    dials_path = data.get('dials_path', '/dials')
    
    # Create output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Change to output directory
    os.chdir(output_dir)
    
    # Collect batch_1 directories under refined/ref_*/
    batch_dirs = []
    for ref_dir in os.listdir(f"../{refined_dir}"):
        ref_path = os.path.join(f"../{refined_dir}", ref_dir)
        if os.path.isdir(ref_path):
            batch_path = os.path.join(ref_path, "batch_1")
            if os.path.exists(batch_path):
                batch_dirs.append(batch_path)
    
    if not batch_dirs:
        raise RuntimeError("No batch_1 directories found in refined/ref_*/")
    
    # Sort directories for consistent ordering
    batch_dirs.sort()
    
    # Build xia2.ssx_reduce command arguments
    reduce_args = []
    for batch_dir in batch_dirs:
        reduce_args.append(f"directory={batch_dir}")
    
    # Construct the full command
    cmd_parts = [
        f"source {dials_path}/dials",
        "&&",
        "xia2.ssx_reduce"
    ] + reduce_args + [
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
    'merge_all': {
        'WaitTime': 7200,
        'ExceptionOnActionFailure': True
    }
})
class MergeAll(GladierBaseTool):
    """Gladier tool for merging refined SSX batches using xia2.ssx_reduce."""
    
    flow_input = {}
    required_input = [
        'refined_dir',
        'output_dir', 
        'phil_file',
        'funcx_endpoint_compute',
    ]
    funcx_functions = [merge_all] 
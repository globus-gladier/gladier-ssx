#!/usr/bin/env python

##Basic Python import's
import argparse
from pprint import pprint
##Base Gladier imports
from gladier import GladierBaseClient, generate_flow_definition


##Import tools that will be used on the flow definition
from .tools.create_phil import CreatePhil
from .tools.run_initial_proc import RunInitialProc
from .tools.run_refined_proc import RunRefinedProc
from .tools.merge_all import MergeAll
from .tools.run_prime import RunPrime
from .tools.primalisys import Primalisys 


##Generate flow based on the collection of `gladier_tools`
@generate_flow_definition()
class SSXClient(GladierBaseClient):
    """Gladier client for SSX processing flow."""
    gladier_tools = [
        CreatePhil,
        RunInitialProc,
        RunRefinedProc,
        MergeAll,
        RunPrime,
        Primalisys,
    ]


## Main client
def run_flow(event: str) -> None:
    """Run the SSX processing flow.
    
    Args:
        event: Event string (currently unused, kept for compatibility)
    """
    ##The first step Client instance
    ssxClient = SSXClient()
    print("Flow created with ID: " + ssxClient.get_flow_id())
    print("https://app.globus.org/flows/" + ssxClient.get_flow_id())
    print("")

    ## Flow inputs necessary for each tool on the flow definition.
    flow_input = {
        "input": {
            # Transfer variables
            "transfer_source_endpoint_id": "",
            "transfer_source_path": "",
            "transfer_destination_endpoint_id": "",
            "transfer_destination_path": "",
            "transfer_recursive": True,            
            
            # SSX Processing parameters
            "data_dir": args.data_dir,
            
            # Processing parameters
            "n_files": 2,
            "nproc": 64,
            
            # PRIME parameters
            "d_min": 1.5,
            "sigma_min": 2.0,
            "isigi_cutoff": 1.5,
            "frame_accept_min_cc": 0.3,
            "prime_dmin": 2.1,
                        # FuncX endpoints
            "compute_endpoint": args.compute_endpoint,
        }
    }
    print("Created payload.")
    pprint(flow_input)
    print("")

    ##Label for the current run (This is the label that will be presented on the globus webApp)
    client_run_label = "Gladier SSX Processing Flow"

    ##Flow execution
    flow_run = ssxClient.run_flow(flow_input=flow_input, label=client_run_label)

    print("Run started with ID: " + flow_run["action_id"])
    print("https://app.globus.org/runs/" + flow_run["action_id"])


##  Arguments for the execution of this file as a stand-alone client
def arg_parse() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description="Gladier SSX Processing Client")
    parser.add_argument("--data-dir", help="Path to data directory", default="/path/to/data")
    parser.add_argument("--compute-endpoint", help="FuncX compute endpoint", default="4b116d3c-1703-4f8f-9f6f-39921e5864df")
    return parser.parse_args()


## Main execution of this "file" as a Standalone client
if __name__ == "__main__":
    args = arg_parse()
    run_flow(args.name)

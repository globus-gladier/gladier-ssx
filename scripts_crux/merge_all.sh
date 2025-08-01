#!/bin/bash
# Merge all refined SSX batches using xia2.ssx_reduce
# Result will be prime.mtz in final_merge/

set -e

MERGE_DIR="final_merge"
mkdir -p "$MERGE_DIR"
cd "$MERGE_DIR"

# Collect batch_1 directories under ../refined/ref_*/
REDUCE_ARGS=$(find ../refined/ref_*/batch_1 -type d -name batch_1 \
    | sort | xargs -I{} echo directory={})

echo "Merging using xia2.ssx_reduce with the following directories:"
echo "$REDUCE_ARGS"

# Run merge
xia2.ssx_reduce $REDUCE_ARGS \
    --phil ../run.phil

echo "Merge complete. Output written to final_merge/prime.mtz"

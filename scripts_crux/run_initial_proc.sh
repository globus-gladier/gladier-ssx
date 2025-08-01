#!/bin/bash
# Process first 10 master files as a group using a single xia2.ssx command
# Output goes to initial_refinement/

set -e
OUTPUT_DIR="initial_refinement"
N_FILES=2

mkdir -p "$OUTPUT_DIR"
cd $OUTPUT_DIR 

echo "Collecting first $N_FILES master files..."
IMAGE_ARGS=$(find ../raster/ -name "*_master.h5" | sort | head -n $N_FILES | xargs -I{} echo image={})
echo "Image arguments: $IMAGE_ARGS"

# Run xia2.ssx
echo "Running xia2.ssx on grouped dataset..."
xia2.ssx $IMAGE_ARGS \
    --phil ../run.phil

echo "Initial refinement complete. Output in $OUTPUT_DIR"

#!/bin/bash
# Re-run xia2.ssx on all master.h5 using refined unit cell, store in refined_processing/

set -e

REFINED_FILE="../../initial_refinement/geometry_refinement/refined.expt"

for f in raster/*_master.h5; do
    RUN=$(basename "$f" _master.h5)
    
    OUTDIR="refined/ref_${RUN}"
    mkdir -p $OUTDIR
    cd $OUTDIR
    echo "Reprocessing $RUN with refined unit cell ..."
    xia2.ssx image=../../$f \
    --phil ../run.phil \ 
	reference_geometry=$REFINED_FILE
    cd ../..
done

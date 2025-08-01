#!/bin/bash
# Run PRIME using directories under ../refined/ref_*/batch_1/

set -e

PRIME_PHIL="prime.phil"
OUTPUT_DIR="prime_results"
LOGFILE="$OUTPUT_DIR/prime.log"

UNIT_CELL="78.95,78.85,38.10,90,90,90"
SPACE_GROUP="P43212"

mkdir -p "$OUTPUT_DIR"

# Collect input batch directories (same logic as xia2.ssx_reduce)
BATCH_DIRS=$(find refined/ref_*/batch_1 -type d -name batch_1 | sort)

if [ -z "$BATCH_DIRS" ]; then
    echo "No batch_1 directories found. Aborting."
    exit 1
fi

# Write input block with all directories
INPUT_BLOCK="input {\n"
for d in $BATCH_DIRS; do
    INPUT_BLOCK+="  directory = $d\n"
done
INPUT_BLOCK+="}\n"

# Create the full prime.phil
cat <<EOF > "$PRIME_PHIL"
$INPUT_BLOCK

output {
  prefix = $OUTPUT_DIR/prime
  log = $LOGFILE
}

target_unit_cell = $UNIT_CELL
target_space_group = $SPACE_GROUP

scaling {
  model = ml_iso
}

merging {
  d_min = 1.5
  partiality_model = unity
}

selection {
  sigma_min = 2.0
  isigi_cutoff = 1.5
  frame_accept_min_cc = 0.3
}
EOF

echo "Running PRIME on $(echo "$BATCH_DIRS" | wc -l) batches..."
prime "$PRIME_PHIL"

echo "✅ PRIME completed. Output in $OUTPUT_DIR/"
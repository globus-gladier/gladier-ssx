#!/bin/bash
# Usage: ./create_phil.sh

set -e

JSON_FILE=$(find . -maxdepth 1 -name "beamline_run*.json" | head -n 1)
if [ -z "$JSON_FILE" ]; then
    echo "Error: No beamline_run*.json file found in the current directory."
    exit 1
fi

# Extract values using jq
SPACE_GROUP=$(jq -r '.user_input.space_group' "$JSON_FILE" | tr '[:lower:]' '[:upper:]')
UNIT_CELL=$(jq -r '.user_input.unit_cell' "$JSON_FILE")
DET_DISTANCE=$(jq -r '.beamline_input.det_distance' "$JSON_FILE")

# Check for missing fields
if [[ "$SPACE_GROUP" == "null" || "$UNIT_CELL" == "null" || "$DET_DISTANCE" == "null" ]]; then
    echo "Error: one or more required fields not found in $JSON_FILE"
    exit 1
fi

# Define default geometry (you can override this later)
FAST_AXIS="0.9999673162585729, -0.0034449798523932267, -0.007314268824966957"
SLOW_AXIS="-0.0034447744696749034, -0.99999406591948, 4.0677756813531234e-05"
ORIGIN="0.0, 0.0, $DET_DISTANCE"  # You can update beam center later
# geometry.detector.panel.fast_axis = $FAST_AXIS
# geometry.detector.panel.slow_axis = $SLOW_AXIS
# geometry.detector.panel.origin = $ORIGIN

# Write run.phil
cat <<EOF > run.phil
nproc = 64

unit_cell = $UNIT_CELL
space_group = $SPACE_GROUP


EOF

echo "✅ run.phil created:"
cat run.phil

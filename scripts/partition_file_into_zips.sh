#!/bin/bash

if [[ $# -ne 3 ]]; then
    echo "usage: $0 INPUT_FILE OUTPUT_DIR PART_BYTES"
    exit 1
fi

INPUT_FILE="$1"
OUTPUT_DIR="$2"
SPLIT_BYTES="$3"

# Handle file splitting
SIZE=$(stat -c%s "$INPUT_FILE")
BASENAME=$(basename "$INPUT_FILE")

echo "📁 Processing: $BASENAME ($(( SIZE / 1024 / 1024 ))MB)"

if [ "$SPLIT_BYTES" -gt 0 ] && [ "$SIZE" -gt "$SPLIT_BYTES" ]; then
    echo "✂️ Splitting $BASENAME into ${SPLIT_MB}MB parts..."
    zip -0 -s "${SPLIT_MB}m" "$OUTPUT_DIR/${BASENAME}.zip" -j "$INPUT_FILE"
    echo "✅ Created $(ls $OUTPUT_DIR/${BASENAME}.z* 2>/dev/null | wc -l) parts"
else
    cp "$INPUT_FILE" "$OUTPUT_DIR/$BASENAME"
    echo "✅ Copied as-is (no split needed)"
fi
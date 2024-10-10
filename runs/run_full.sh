#!/bin/bash

set -e

MODEL="mistral-large"
TEMPERATURE=0.0
REQUEST_TIMEOUT=120
TYPE="mistral"
NUM_RUNS=1
DIRECTORIES="data/full_data/test","data/full_data/valid"

python -m script \
  --model="$MODEL" \
  --temperature="$TEMPERATURE" \
  --request_timeout="$REQUEST_TIMEOUT" \
  --type="$TYPE" \
  --num_runs="$NUM_RUNS" \
  --directories="$DIRECTORIES"

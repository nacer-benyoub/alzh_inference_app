#!/bin/bash

echo "Running Step 1: Preprocessing..."
python preprocessing.py
echo "Step 1 completed successfully"
echo

echo "Running Step 2: Inference..."
jupyter nbconvert --to notebook --execute inference.ipynb --inplace
echo "Step 2 completed successfully"
echo
#!/usr/bin/env bash

# activate the base (only) environment
source $FSLDIR/bin/activate
# activate FSL
source $FSLDIR/etc/fslconf/fsl.sh
# start flask server
python ./app.py
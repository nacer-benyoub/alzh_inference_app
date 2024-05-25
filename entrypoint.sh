#!/usr/bin/env bash

# activate the base (only) environment
source /opt/conda/bin/activate base
# activate FSL
source $FSLDIR/etc/fslconf/fsl.sh
exec "$@"
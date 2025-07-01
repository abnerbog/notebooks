#!/bin/bash

# Stop if any command fails
set -e

# Create a new conda environment
conda create -y -n conus404-env python=3.11

# Activate the environment
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate conus404-env

# Install packages via conda-forge without user prompt
conda install -y -c conda-forge \
  xarray \
  intake \
  intake-xarray \
  asciitree \
  fsspec \
  requests \
  aiohttp \
  zarr \
  numcodecs \
  numpy \
  scipy \
  s3fs \
  metpy \
  cartopy \
  pyproj \
  proj \
  hvplot \
  geopandas \
  contextily \
  rioxarray \
  seaborn \
  jupyterlab \
  ipykernel

# Register this environment as a Jupyter kernel
python -m ipykernel install --user --name conus404-env --display-name "CONUS404 Analysis"

echo "Environment 'conus404-env' created and added to JupyterLab kernel list as 'CONUS404 Analysis'."

#!/bin/bash

# Stop if any command fails
set -e

# Create a folder in home directory for making the conda environment persistent between sessions
mkdir -p ~/conda_envs

# Create a new conda environment in home folder so it persists after restarts
conda create -y --prefix ~/conda_envs/conus404-env python=3.12

# Activate the environment
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate ~/conda_envs/conus404-env

# Install packages via conda-forge without user prompt; include specific versions
conda install -y -c conda-forge \
  xarray=2024.3.0 \
  intake=2.0.4 \
  intake-xarray=0.7.0 \
  asciitree=0.3.3 \
  fsspec=2024.3.1 \
  requests=2.31.0 \
  aiohttp=3.9.3 \
  numcodecs=0.12.1 \
  scipy=1.13.0 \
  s3fs=2024.3.1 \
  metpy=1.6.2 \
  cartopy=0.22.0 \
  hvplot=0.9.2 \
  geopandas=0.14.4 \
  contextily=1.6.2 \
  rioxarray=0.15.3 \
  seaborn=0.13.2 \
  jupyterlab=4.3.6 \
  ipykernel=6.29.3 \
  # these packages require some flexibility
  numpy>=2.0 \
  proj \
  pyproj \
  zarr

# Register this environment as a Jupyter kernel
python -m ipykernel install --user --name conus404-env --display-name "CONUS404 Analysis"

echo "Environment 'conus404-env' created under conda_envs folder and added to JupyterLab kernel list as 'CONUS404 Analysis'."

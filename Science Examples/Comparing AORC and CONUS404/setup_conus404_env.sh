#!/bin/bash

# Stop if any command fails
set -e

# Define the environment name and path
ENV_NAME="conus404-env"
ENV_PATH="$HOME/conda_envs/$ENV_NAME"

# Create a folder in home directory for making the conda environment persistent between sessions
mkdir -p "$HOME/conda_envs"

# Check if mamba is installed, if not, install it
if ! command -v mamba &> /dev/null
then
    echo "Mamba not found. Installing mamba..."
    conda install -y -c conda-forge mamba
fi

# Create or update the conda environment using the environment.yml file and mamba
echo "Creating/updating conda environment '$ENV_NAME' from environment.yml..."
# This command will create the environment at the specified prefix if it doesn't exist,
# or update it if it does.
mamba env create -f environment.yml --prefix "$ENV_PATH" || \
mamba env update -f environment.yml --prefix "$ENV_PATH"

# Activate the environment
echo "Activating environment '$ENV_NAME'..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$ENV_PATH"

echo "Environment '$ENV_NAME' created/updated."
echo "Jupyter will automatically discover this environment as a kernel (e.g., 'Python [conda env:$ENV_NAME]')."
echo "Please select that kernel in JupyterLab."
#!/bin/bash

# Stop if any command fails
set -e

# Define the environment name and path
ENV_NAME="conus404-env"
ENV_PATH="$HOME/conda_envs/$ENV_NAME"

# Create a folder in home directory for making the conda environment persistent between sessions
mkdir -p "$HOME/conda_envs"

# Install the libmamba solver if not already present and configure conda to use it
echo "Checking for and configuring libmamba solver..."
if ! conda list -n base | grep -q "conda-libmamba-solver"; then
    echo "conda-libmamba-solver not found in base environment. Installing..."
    conda install -n base conda-libmamba-solver -y
fi
conda config --set solver libmamba


# Create or update the conda environment using the environment.yml file
echo "Creating/updating conda environment '$ENV_NAME' from environment.yml..."
# This command will create the environment at the specified prefix if it doesn't exist,
# or update it if it does.
conda env create -f environment.yml --prefix "$ENV_PATH" || \
conda env update -f environment.yml --prefix "$ENV_PATH"

# Activate the environment
echo "Activating environment '$ENV_NAME'..."
conda activate "$ENV_PATH"

echo "Environment '$ENV_NAME' created/updated."
echo "Jupyter will automatically discover this environment as a kernel (e.g., 'Python [conda env:$ENV_NAME]')."
echo "Please select that kernel in JupyterLab."
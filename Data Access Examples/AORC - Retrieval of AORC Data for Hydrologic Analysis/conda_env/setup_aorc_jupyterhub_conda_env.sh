#!/bin/bash

# === Determine script location ===
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Define env name and paths
ENV_NAME="aorc"
ENV_PATH="$HOME/.conda/envs/$ENV_NAME"
ENV_YML="$SCRIPT_DIR/environment.yml"
KERNEL_NAME="$ENV_NAME"
KERNEL_DISPLAY="Python3 (AORC)"

echo "$ENV_NAME env path target: $ENV_PATH"


# Step 0: Check if environment.yml exists
if [ ! -f "$ENV_YML" ]; then
    echo "❌ Error: environment.yml not found at $ENV_YML"
    echo "Please ensure the file exists and try again."
    exit 1
fi

# Step 1: Clear conda cached packages - to free up disk space
echo "Clean up conda caches beroe creating a new conda environment ..."
conda clean -a -y

# Step 2: Check if env directory exists and has conda metadata
if [ -d "$ENV_PATH" ] && [ -f "$ENV_PATH/conda-meta/history" ]; then
    echo "⚠️  Conda environment '$ENV_NAME' already exists at $ENV_PATH."
    read -p "Do you want to delete and recreate it? (y/N): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo "🚫 Aborting. Environment was not modified."
        exit 0
    fi

    echo "🧨 Removing existing Conda environment..."
    conda deactivate 2>/dev/null
    conda env remove -p "$ENV_PATH" --yes

    if [ -d "$ENV_PATH" ]; then
        echo "⚠️  Conda env directory still exists, forcing removal..."
        rm -rf "$ENV_PATH"
    fi

    # Step 2: Remove Jupyter kernel spec if exists
    if jupyter kernelspec list | grep -q "/$KERNEL_NAME\$"; then
        echo "🧽 Removing existing Jupyter kernel spec '$KERNEL_NAME' ..."
        jupyter kernelspec uninstall -f "$KERNEL_NAME"
    fi
fi

# Ensure the conda-envs directory exists
mkdir -p "$(dirname "$ENV_PATH")"

# Step 3: Create the Conda environment
echo "📦 Creating Conda environment at $ENV_PATH ..."
mamba env create -p "$ENV_PATH" -f "$ENV_YML"
if [ $? -ne 0 ]; then
    echo "❌ Failed to create Conda environment."
    exit 1
fi

# Step 4: Register the conda env as a new Jupyter kernel.
echo "🧠 Registering Jupyter kernel '$KERNEL_DISPLAY' ..."
"$ENV_PATH/bin/python" -m ipykernel install --user --name "$KERNEL_NAME" --display-name "$KERNEL_DISPLAY"
if [ $? -ne 0 ]; then
    echo "❌ Failed to register Jupyter kernel."
    exit 1
fi

echo "✅ Conda environment '$ENV_NAME'  successfully created ..."
echo "To use this conda env for a notebook, switch the kernel to 'Python [cond env:.conda-aorc]' if this kernel is in the list. Otherwise, use '$KERNEL_DISPLAY'."

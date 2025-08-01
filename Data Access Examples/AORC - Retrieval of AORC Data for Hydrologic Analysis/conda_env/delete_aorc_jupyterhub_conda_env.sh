#!/bin/bash

# Set the environment path and kernel name
ENV_NAME="aorc"
ENV_PATH="$HOME/.conda/envs/$ENV_NAME"
KERNEL_NAME="aorc"

# Step 1: Remove the Conda environment
if [ -d "$ENV_PATH" ]; then
    echo "🧼 Removing Conda environment at $ENV_PATH..."
    conda deactivate 2>/dev/null
    conda env remove -p "$ENV_PATH" --yes
    
    if [ -d "$ENV_PATH" ]; then
        echo "⚠️  Conda env directory still exists, forcing removal..."
        rm -rf "$ENV_PATH"
    fi
else
    echo "⚠️  Conda environment at $ENV_PATH does not exist or was already removed."
fi

# Step 2: Remove Jupyter kernel spec if exists
if jupyter kernelspec list | grep -q "/$KERNEL_NAME\$"; then
    echo "🧽 Removing existing Jupyter kernel spec '$KERNEL_NAME'..."
    jupyter kernelspec uninstall -f "$KERNEL_NAME"
fi

echo "✅ Environment and kernel cleanup complete."
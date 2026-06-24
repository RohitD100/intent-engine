#!/usr/bin/env bash
# Activate virtual environment and install dependencies

# Determine script directory (project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"

# Activate venv
if [ -f "${VENV_DIR}/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "${VENV_DIR}/bin/activate"
else
    echo "Virtual environment not found at ${VENV_DIR}"
    exit 1
fi

# Upgrade pip and install requirements
pip install --upgrade pip
pip install -r "${SCRIPT_DIR}/requirements.txt"

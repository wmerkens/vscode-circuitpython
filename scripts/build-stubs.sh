#!/usr/bin/env bash
set -euo pipefail
[ "${DEBUG:-}" = "true" ] && set -x

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
CIRCUITPYTHON_DIR="$REPO_ROOT/circuitpython"
CIRCUITPYTHON_VERSION="9.2.1"

cd "$REPO_ROOT"

# Clone repository if it doesn't exist
if [ ! -d "$CIRCUITPYTHON_DIR" ]; then
    git clone https://github.com/adafruit/circuitpython.git "$CIRCUITPYTHON_DIR" || {
        echo "Failed to clone CircuitPython repository"
        exit 1
    }
fi
	
cd "$CIRCUITPYTHON_DIR"

# Checkout specific version and fetch submodules
git checkout 9.2.1 || {
    echo "Failed to checkout version 9.2.1"
    exit 1
}
make fetch-all-submodules || {
    echo "Failed to fetch submodules"
    exit 1
}

# Set up Python virtual environment
if [ ! -d .venv ]; then
    python3 -m venv .venv || {
        echo "Failed to create virtual environment"
        exit 1
    }
fi

source .venv/bin/activate

# Install dependencies
pip_install() {
    python3 -m pip install "$@" || {
        echo "Failed to install $*"
        exit 1
    }
}

pip_install --upgrade pip wheel
pip_install bs4
pip_install -r requirements-doc.txt

# Generate stubs
make stubs || {
    echo "Failed to generate stubs"
    exit 1
}
if [ -d "$REPO_ROOT/stubs" ]; then
    rm -rf "$REPO_ROOT/stubs"
fi
mkdir -p "$REPO_ROOT/stubs"

# Move stubs to appropriate location
if [ -d "$REPO_ROOT/stubs" ]; then
    mv circuitpython-stubs/* "$REPO_ROOT/stubs/"
    else
    mv circuitpython-stubs "$REPO_ROOT/stubs"
    fi

cd "$REPO_ROOT"
    python3 ./scripts/build_stubs.py

# Cleanup
deactivate
rm -rf "$CIRCUITPYTHON_DIR" .venv
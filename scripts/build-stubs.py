#!/usr/bin/env python3
"""
Script to generate and manage CircuitPython stubs.
Handles repository cloning, stub generation, and virtual environment management.
"""
import argparse
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Configuration
CIRCUITPYTHON_VERSION = "9.2.1"
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Setup logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def run_command(cmd: str, cwd: Optional[Path] = None) -> None:
    """
    Execute a shell command and handle errors.
    
    Args:
        cmd: Command to execute
        cwd: Working directory for command execution
    Raises:
        SystemExit: If command execution fails
    """
    logging.debug(f"Executing: {cmd} in {cwd or 'current directory'}")
    try:
        subprocess.run(cmd, cwd=cwd, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error executing {cmd}: {e}")
        sys.exit(1)

def safe_rmtree(path: Path) -> None:
    """
    Safely remove a directory tree.
    
    Args:
        path: Path to remove
    """
    try:
        shutil.rmtree(path)
    except OSError as e:
        logging.error(f"Error removing {path}: {e}")

def main(version: str) -> None:
    """
    Main function to handle stub generation and management.
    
    Args:
        version: CircuitPython version to checkout
    """
    # Setup paths
    script_dir = Path(__file__).parent.absolute()
    repo_root = script_dir.parent
    circuitpython_dir = repo_root / "circuitpython"

    # Change to repo root
    os.chdir(repo_root)

    # Clone repository if it doesn't exist
    if not circuitpython_dir.exists():
        run_command(f"git clone https://github.com/adafruit/circuitpython.git {circuitpython_dir}")

    # Change to circuitpython directory
    os.chdir(circuitpython_dir)

    # Checkout specific version and fetch submodules
    run_command(f"git checkout {version}")
    run_command("make fetch-all-submodules")

    # Setup virtual environment
    venv_dir = circuitpython_dir / ".venv"
    run_command(f"python3 -m venv {venv_dir}")

    # Activate virtual environment (Python way)
    venv_pip = venv_dir / "bin" / "pip"
    venv_python = venv_dir / "bin" / "python"

    # Install dependencies
    run_command(f"{venv_pip} install --upgrade pip wheel")
    run_command(f"{venv_pip} install bs4")
    run_command(f"{venv_pip} install isort")
    run_command(f"{venv_pip} install -r requirements-doc.txt")

    # Generate stubs
    run_command("make stubs")

    # Handle stubs directory
    stubs_dir = repo_root / "stubs"
    if stubs_dir.exists():
        safe_rmtree(stubs_dir)
    stubs_dir.mkdir(parents=True)

    # Move generated stubs
    circuitpython_stubs = circuitpython_dir / "circuitpython-stubs"
    try:
        for item in circuitpython_stubs.glob("*"):
            if item.is_file():
                shutil.copy2(item, stubs_dir)
            else:
                shutil.copytree(item, stubs_dir / item.name)
    except OSError as e:
        logging.error(f"Error copying stubs: {e}")
        sys.exit(1)

    # Change back to repo root and build stubs
    os.chdir(repo_root)
    run_command(f"{venv_python} ./scripts/build-boards.py")

    # Cleanup only the virtual environment
    safe_rmtree(venv_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate and manage CircuitPython stubs.")
    parser.add_argument("--version", default=CIRCUITPYTHON_VERSION,
                        help=f"CircuitPython version to checkout (default: {CIRCUITPYTHON_VERSION})")
    args = parser.parse_args()
    
    main(args.version)

# vim: set ts=4 sw=4 tw

#!/usr/bin/env python3
"""
Script for generating .pyi files for each CircuitPython board type.
These files need to be bundled with the extension, meaning new boards require a new extension release.
"""
import json
import pathlib
import re
from functools import lru_cache
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup

# Constants
URL = "https://circuitpython.org/downloads?sort-by=alpha-asc"
VID_PID_PATTERN = re.compile(r"0x[0-9A-Fa-f]{4}")

def fetch_sorted_manufacturers(url: str) -> List[Dict[str, str]]:
    """Fetch and return a sorted list of manufacturers and names from the webpage."""
    try:
        with requests.Session() as session:
            response = session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            elements = soup.find_all("div", class_="download")
            data_list = [
                {
                    "name": element.get("data-name"),
                    "manufacturer": element.get("data-manufacturer")
                }
                for element in elements
                if element.get("data-name") and element.get("data-manufacturer")
            ]
            return sorted(data_list, key=lambda x: x["name"].lower())
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return []

def parse_generic_stub(board_stub: pathlib.Path) -> Dict[str, str]:
    """Parse the generic board stub file."""
    generic_stubs = {}
    def_re = re.compile(r"def ([^\(]*)\(.*")
    with board_stub.open('r') as stub:
        stubs = stub.readlines()
        # Find the first line number and name of each definition
        f = []
        names = []
        for i, s in enumerate(stubs):
            match = def_re.match(s)
            if match is not None:
                f.append(i)
                names.append(match[1])
        f.append(len(stubs))
        # Iterate the line ranges
        for name, start, end in zip(names, f, f[1:]):
            generic_stubs[name] = "".join(stubs[start:end])
    return generic_stubs

def normalize_vid_pid(value: str) -> str:
    """Normalize VID/PID to format 0x04D8 (lowercase 'x', uppercase hex digits)."""
    if not value:
        return value
    if value.startswith("0x") or value.startswith("0X"):
        # Ensure '0x' prefix and uppercase hex digits
        return f"0x{value[2:].upper()}"
    # For values without '0x' prefix
    return f"0x{value.zfill(4).upper()}"

_PIN_DEF_RE = re.compile(
    r"\s*{\s*MP_ROM_QSTR\(MP_QSTR_(?P<name>[^\)]*)\)\s*,\s*MP_ROM_PTR\((?P<value>[^\)]*)\).*"
)

def parse_pins(generic_stubs: Dict[str, str], pins: pathlib.Path, board_stubs: Dict[str, str]) -> Tuple[str, str]:
    """Parse the pins file and generate imports and stub lines."""
    imports = set()
    stub_lines = []
    with pins.open('r') as p:
        for line in p:
            pin = _PIN_DEF_RE.match(line)
            if pin is None:
                continue
            pin_name = pin.group("name")
            if pin_name in generic_stubs:
                board_stubs[pin_name] = generic_stubs[pin_name]
                if "busio" in generic_stubs[pin_name]:
                    imports.add("busio")
                continue
            pin_type = None
            pin_value = pin.group("value")
            if pin_value == "&displays[0].epaper_display":
                imports.add("displayio")
                pin_type = "displayio.EPaperDisplay"
            elif pin_value == "&displays[0].display":
                imports.add("displayio")
                pin_type = "displayio.Display"
            elif pin_value.startswith("&pin_"):
                imports.add("microcontroller")
                pin_type = "microcontroller.Pin"
            if pin_type is None:
                imports.add("typing")
                pin_type = "typing.Any"
            stub_lines.append(f"{pin_name}: {pin_type} = ...\n")
    return '\n'.join(f"import {x}" for x in sorted(imports)) + '\n', ''.join(stub_lines)

def process_boards(repo_root: pathlib.Path, circuitpy_repo_root: pathlib.Path, generic_stubs: Dict[str, str]) -> List[Dict[str, str]]:
    """Process all board configurations."""
    boards = []
    processed_boards = {}  # Change to dictionary to track counts
    sorted_manufacturers = fetch_sorted_manufacturers(URL)
    board_configs = circuitpy_repo_root.glob("ports/*/boards/*/mpconfigboard.mk")

    for config in board_configs:
        b = config.parent
        site_path = b.stem
        pins = b / "pins.c"
        pins_csv = b / "pins.csv"
        
        # Skip if config file is missing
        if not config.is_file():
            print(f"Skipping {site_path}: mpconfigboard.mk not found")
            continue

        # Skip if using pins.csv instead of pins.c
        if pins_csv.exists() and not pins.exists():
            print(f"Skipping {site_path}: using pins.csv instead of pins.c")
            continue

        # Skip if neither pins.c nor pins.csv exists
        if not pins.exists() and not pins_csv.exists():
            print(f"Skipping {site_path}: no pins file found")
            continue

        board_info = {
            "usb_vid": "",
            "usb_pid": "",
            "usb_product": "",
            "usb_manufacturer": "",
            "circuitpy_creator_id": "",
            "circuitpy_creation_id": "",
        }

        with config.open() as conf:
            for line in conf:
                for key in board_info:
                    if line.startswith(key.upper()):
                        board_info[key] = line.split("=")[1].split("#")[0].strip('" \n')

        # Fallback logic
        if not board_info["usb_vid"] and board_info["circuitpy_creator_id"]:
            board_info["usb_vid"] = board_info["circuitpy_creator_id"]
        if not board_info["usb_pid"] and board_info["circuitpy_creation_id"]:
            board_info["usb_pid"] = board_info["circuitpy_creation_id"]

        prefix = site_path.split("_", 1)[0]
        matched_manufacturer = next(
            (data["manufacturer"] for data in sorted_manufacturers if prefix.lower() in data["manufacturer"].lower()),
            None
        )

        if matched_manufacturer == "Unknown" or (matched_manufacturer and prefix.lower() not in board_info["usb_manufacturer"].lower()):
            board_info["usb_product"] = site_path
            board_info["usb_manufacturer"] = prefix.capitalize()

        if not board_info["usb_product"] or not board_info["usb_manufacturer"]:
            board_info["usb_product"] = site_path
            board_info["usb_manufacturer"] = prefix.capitalize()

        board_info["usb_vid"] = normalize_vid_pid(board_info["usb_vid"])
        board_info["usb_pid"] = normalize_vid_pid(board_info["usb_pid"])

        board_id = f"{board_info['usb_vid']}:{board_info['usb_pid']}"
        if board_id in processed_boards:
            processed_boards[board_id] += 1
            print(f"Note: Found another board with the same VID:PID: {board_id}:{site_path}")
        else:
            processed_boards[board_id] = 0

        board = {
            "vid": board_info["usb_vid"],
            "pid": board_info["usb_pid"],
            "product": board_info["usb_product"],
            "manufacturer": board_info["usb_manufacturer"],
            "site_path": site_path,
            "description": f"{board_info['usb_manufacturer']} {board_info['usb_product']}",
        }
        boards.append(board)

        board_pyi_path = repo_root / "boards" / board_info["usb_vid"] / board_info["usb_pid"]
        board_pyi_path.mkdir(parents=True, exist_ok=True)
        
        # Append a number to the filename if it's a duplicate
        if processed_boards[board_id] > 0:
            board_pyi_file = board_pyi_path / f"{site_path}_board_{processed_boards[board_id]}.pyi"
        else:
            board_pyi_file = board_pyi_path / f"{site_path}_board.pyi"

        board_stubs = {}
        imports_string, stubs_string = parse_pins(generic_stubs, pins, board_stubs)

        with board_pyi_file.open("w") as outfile:
            outfile.write("from __future__ import annotations\n")
            outfile.write(imports_string)
            outfile.write(f'"""\nboard {board["description"]}\n')
            outfile.write(f'https://circuitpython.org/boards/{board["site_path"]}\n"""\n')
            outfile.write(stubs_string)
            for p in board_stubs:
                outfile.write(f"{board_stubs[p]}\n")

    return boards

def main():
    """Main function to generate board stubs and metadata."""
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    board_stub = repo_root / "stubs" / "board" / "__init__.pyi"
    generic_stubs = parse_generic_stub(board_stub)
    circuitpy_repo_root = repo_root / "circuitpython"
    
    boards = process_boards(repo_root, circuitpy_repo_root, generic_stubs)
    
    json_file = repo_root / "boards" / "metadata.json"
    with json_file.open("w") as metadata_file:
        json.dump(boards, metadata_file, indent=4)

if __name__ == "__main__":
    main()
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

@lru_cache(maxsize=1)
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
    definitions = [(i, def_re.match(s)) for i, s in enumerate(stubs)]
    valid_defs = [(i, match.group(1)) for i, match in definitions if match]
    for i, (start_idx, name) in enumerate(valid_defs):
        end_idx = valid_defs[i + 1][0] if i + 1 < len(valid_defs) else len(stubs)
        generic_stubs[name] = ''.join(stubs[start_idx:end_idx])
    return generic_stubs

def normalize_vid_pid(value: str) -> str:
    """Normalize VID/PID to uppercase hex string."""
    if not value:
        return value
    if value.startswith("0x") or value.startswith("0X"):
        return value.upper()
    return f"0x{value.zfill(4).upper()}"

def parse_pins(generic_stubs: Dict[str, str], pins: pathlib.Path, board_stubs: Dict[str, str]) -> Tuple[str, str]:
    """Parse the pins file and generate imports and stub lines."""
    imports = set()
    stub_lines = []
    pin_re = re.compile(r"\s*{\s*MP_ROM_QSTR\(MP_QSTR_(?P<name>[^\)]*)\)\s*,\s*MP_ROM_PTR\((?P<value>[^\)]*)\).*")
    type_mapping = {
        "&displays[0].epaper_display": ("displayio", "displayio.EPaperDisplay"),
        "&displays[0].display": ("displayio", "displayio.Display"),
    }

    with pins.open('r') as p:
        for line in p:
            pin = pin_re.match(line)
            if not pin:
                continue
            pin_name = pin.group("name")
            if pin_name in generic_stubs:
                board_stubs[pin_name] = generic_stubs[pin_name]
                if "busio" in generic_stubs[pin_name]:
                    imports.add("busio")
                continue
            pin_value = pin.group("value")
            if pin_value in type_mapping:
                imports.add(type_mapping[pin_value][0])
                pin_type = type_mapping[pin_value][1]
            elif pin_value.startswith("&pin_"):
                imports.add("microcontroller")
                pin_type = "microcontroller.Pin"
            else:
                imports.add("typing")
                pin_type = "typing.Any"
            stub_lines.append(f"{pin_name}: {pin_type} = ...\n")

    return '\n'.join(f"import {x}" for x in sorted(imports)) + '\n', ''.join(stub_lines)

def process_board(config: pathlib.Path, repo_root: pathlib.Path, circuitpy_repo_root: pathlib.Path, generic_stubs: Dict[str, str], sorted_manufacturers: List[Dict[str, str]]) -> Dict[str, str]:
    """Process a single board configuration."""
    b = config.parent
    site_path = b.stem
    pins = b / "pins.c"
    if not config.is_file() or not pins.is_file():
        return None

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
    matched_manufacturer = next((data["manufacturer"] for data in sorted_manufacturers if prefix.lower() in data["manufacturer"].lower()), None)
    
    if matched_manufacturer == "Unknown" or (matched_manufacturer and prefix.lower() not in board_info["usb_manufacturer"].lower()):
        board_info["usb_product"] = site_path
        board_info["usb_manufacturer"] = prefix.capitalize()

    if not board_info["usb_product"] or not board_info["usb_manufacturer"]:
        board_info["usb_product"] = site_path
        board_info["usb_manufacturer"] = prefix.capitalize()

    # Normalize VID and PID
    board_info["usb_vid"] = normalize_vid_pid(board_info["usb_vid"])
    board_info["usb_pid"] = normalize_vid_pid(board_info["usb_pid"])

    board = {
        "vid": board_info["usb_vid"],
        "pid": board_info["usb_pid"],
        "product": board_info["usb_product"],
        "manufacturer": board_info["usb_manufacturer"],
        "site_path": site_path,
        "description": f"{board_info['usb_manufacturer']} {board_info['usb_product']}",
    }

    board_pyi_path = repo_root / "boards" / board_info["usb_vid"] / board_info["usb_pid"]
    board_pyi_path.mkdir(parents=True, exist_ok=True)
    board_pyi_file = board_pyi_path / "board.pyi"

    # Skip if file already exists
    if board_pyi_file.exists():
        print(f"Skipping existing board file: {board_pyi_file}")
        return None

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

    return board

def main():
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    board_stub = repo_root / "stubs" / "board" / "__init__.pyi"
    generic_stubs = parse_generic_stub(board_stub)
    circuitpy_repo_root = repo_root / "circuitpython"
    sorted_manufacturers = fetch_sorted_manufacturers(URL)
    board_configs = list(circuitpy_repo_root.glob("ports/*/boards/*/mpconfigboard.mk"))

    with ThreadPoolExecutor() as executor:
        boards = list(filter(None, executor.map(
            lambda config: process_board(config, repo_root, circuitpy_repo_root, generic_stubs, sorted_manufacturers),
            board_configs
        )))

    json_file = repo_root / "boards" / "metadata.json"
    with json_file.open("w") as metadata_file:
        json.dump(boards, metadata_file, indent=2)

if __name__ == "__main__":
    main()
    
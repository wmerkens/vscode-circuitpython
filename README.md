# vscode-circuitpython V2 README

This extension aspires to bring your entire CircuitPython workflow into a single
place in VSCode.

Inspired by [Scott Hanselman's blog
post](https://www.hanselman.com/blog/UsingVisualStudioCodeToProgramCircuitPythonWithAnAdaFruitNeoTrellisM4.aspx)
and the [VSCode Arduino extension](https://github.com/Microsoft/vscode-arduino).

I have forked the original extension in order to apply fixes

Note: if updating and opening a existing CIRCUITPY folder please re select the board from the list. Please let me know if a board is missing, The metadata.json file contains 550 boards, 8 boards are not released or boards that have Unknown Manufacture.



## Getting Started

The extension will currently activate when any of the following occurs:

* workspace contains
  * `/code.py`
  * `/code.txt`
  * `/main.py`
  * `/main.txt`
  * `/boot_out.txt`
* command run
  * `circuitpython.openSerialMonitor`
  * `circuitpython.selectSerialPort`
  * `circuitpython.closeSerialMonitor`

Upon activation, the extension will check for the latest
[Adafruit_CircuitPython_Bundle](https://github.com/adafruit/Adafruit_CircuitPython_Bundle)
and download it if needed. It'll then load that library metadata into the
workspace's state. You can also trigger this manually with `CircuitPython: Check
for latest bundle`.

After that, you should be ready to use the following features.

## Features

### Library Management

v0.0.2 introduced a [Circup](https://github.com/adafruit/circup) inspired
library manager with an emphasis on VSCode integration. It downloads new
bundles automatically.

You can use it with the following commands:

* `CircuitPython: Show Available Libraries`
  This is every library in the Adafruit Bundle. Alphabetical but 
  installed libraries are grouped at the top. Click an out-of-date library 
  to update, click an uninstalled library to install it.
* `CircuitPython: List Project Libraries`
  Lists what's in your project's lib. If anything needs to be updated, click 
  it to update.
* `CircuitPython: Reload Project Libraries` 
  In case it's reporting incorrectly. This can happen if you modify the 
  filesystem outside of vscode.
* `CircuitPython: Update All Libraries`
  The equivalent of `circup update --all`
* `CircuitPython: Check for the latest bundle.`
  Compares the bundle on disk to the latest github release, downloads the 
  release if it's newer.

### Serial Console

`Circuit Python: Open Serial Console` will prompt you for a serial port to
connect to, and then it will display the serial output from the board attached to
that port. The port can be changed by clicking on its path in the status bar.

Hit `Ctrl-C` and any key to enter the Circuit Python REPL, and `Ctrl-D` to
reload.

Note: There are Linux permissions issues with the serial console, but if you're
on Linux, you're probably used to that.

It will also change your workspace's default `board.pyi` file for autocomplete
to the one that matches the USB Vendor ID & Product ID.

If you want to choose a different board manually, a list is available with the
command `CircuitPython: Choose CircuitPython Board,` and also by clicking on the
board name in the status bar.

**NOTE FOR WINDOWS USERS**: I have seen trouble with the serial console
displaying anything at all. If that happens, try launching VSCode as an
administrator and see if it works. I have even gotten it to work as a
non-administrator after this, so perhaps running it as an admin stole the serial
port from whatever was using it, and then whatever it was didn't grab it again.

### Auto Complete

Automatically adds stubs for your specific board, the circuitpython standard
library and all py source files in the adafruit bundle to your completion path.

### Demo

![Demo](images/circuitpy-demo.gif)

## Requirements

## Extension Settings

### Board Settings

Board-specific settings can be stored in a project's `.vscode/settings.json`
file, which will default to this board. This is great for when opening up the
CIRCUITPY drive as a vscode workspace will be automatically set whenever
you choose a board.

You can also use this for projects you're working from on disk with the intent
of running on a specific board.

You can also set these at a user level, although that's not the primary intent.
If you do this, it will get overridden at the workspace level if you ever touch
the choose board dropdown or open a serial monitor. 

I would have restricted the scope to workspace if that was an option.

`circuitpython.board.vid`: Vendor ID for the project's board
`circuitpython.board.pid`: Product ID for the project's board
`circuitpython.board.version`: Persisted in choosing the correct mpy binaries

## Known Issues

## Release Notes

See the [Changelog](CHANGELOG.md)

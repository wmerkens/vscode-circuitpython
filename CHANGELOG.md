# Change Log

All notable changes to the "vscode-circuitpython" extension will be documented
in this file. Please still refer to Joe Devivo version for possible changes.

## [0.3.3]
- Update for circuit Python 9.2.4
## [0.3.2]
- Update for Circuit Python 9.2.3

## [0.3.1]
- fix issue with intellesense and the boards not showing the pins

## [0.3.0]
- Fix issue where downloaded bundle was not unpacked properly
- Fix issue where choosing a library the list would show your already installed librarys with corrupt description
- Fix issue where the .vscode/settings.json file would not be updated properly
- Since the bundle now ships as mpy files for everything, removed the parsing of metadata from the mpy files.
  instead we use the supplied metadata.json to derive version, name, ect for the metadate. This was causing a lot of
  library issues.

## [0.2.9]
- Fix Issue #14 Incorrect link for Issues on Extention page.
- Rebuild for updated VSC and NPM

## [0.2.8]
- rebuild missing stuff

## [0.2.7]
- updated the stubs and board scripts, they are now both python and overall   improved for speed and reliability
- final fixes for generating the metadata.json file in boards directory

## [0.2.6]
- first pass at fixing the board selection list
- change node to 20.18.0 same as VSC

## [0.2.5]
- remove yarn, interferes with build
- fixed electron build, electron now at 33.2.0

## [0.2.4]
- Update boards and stubs for CP 9.2.1

## [0.2.3]
- Synced up to the Git version

## [0.2.1]
- Forked version 0.2.0 to apply some fixes
- Updated node to v20
- Updated most npm packages to be more current 
- Fixed some areas where code needed to be ES6 compliant
- Updated script build-stubs.sh to work with circuitpython build system changes.
- Generated new stubs and boards.

## [0.2.0]
- Merged [#123](https://github.com/joedevivo/vscode-circuitpython/pull/123)
- Merged [#62](https://github.com/joedevivo/vscode-circuitpython/pull/62)
- Merged [#122](https://github.com/joedevivo/vscode-circuitpython/pull/122)
- Merged [#29](https://github.com/joedevivo/vscode-circuitpython/pull/29)
- Upgraded dependencies
- Fixed version info for .py files

## [0.1.20]
- Circuit Python 8

## [0.1.19]
- Update to Electron 18
- Added `Open Board's CircuitPython.org` page for easy access to firmware downloads
- Every release includes the latest boards.

## [0.1.18]
- Drop `pylance` dependency
- Publish on `open-vsx.org`

## [0.1.17]
- Update Electron to 17.2.0
- VSCode >= 1.66.0
- Update dependabot alert on `plist`

## [0.1.16]
- Fix [#72](https://github.com/joedevivo/vscode-circuitpython/issues/72)
- Board Update
- CircuitPython Update
- Upgrade `serialport` dependency
- Move to GitHub Actions for CI

## [0.1.15]
- Electron Rebuild 13.1.7
- Board Update
- CircuitPython Update
- Fix version detection in mpy files for CP7

## [0.1.14]

- Added download for 7.x mpy bundle
- Electron Rebuild 12.0.13

### Bug Fixes
- Skips enabling serial monitor if native bindings aren't loaded
  - This prevents the extension from crashing on launch if the VSCode version of
    electron has changed or the bindings aren't available for your
    system/architecture
- Uses `""` instead of `null` in the `python.analysis.extraPaths` setting if a
  board is not chosen.
- Fixed issue that prevented the board stub at `python.analysis.extraPaths[0]`
  from changing on board selection.
- Fixed an issue preventing extension activation when workspace doesn't contain a `lib` folder
- Fixed error downloading new Adafruit Bundle if bundle storage contains a file,
  where it previously assumed directories only.
## [0.1.13]
- Put the bindings in the correct folder, 0.1.12 is pretty much broken for everyone.
## [0.1.12]
- Electron Rebuild 12.0.4

## [0.1.11]
- Fixed [#38](https://github.com/joedevivo/vscode-circuitpython/pull/37)
  issue with Apple Silicon native bindings
- Fixed [#42](https://github.com/joedevivo/vscode-circuitpython/pull/42) &
  [#44](https://github.com/joedevivo/vscode-circuitpython/pull/44)
  `boot_out.txt` was required. Still is to determine CircuitPython version, but
  we can live without that.

## [0.1.10]
- Disable pylint by default
- Opt in to pylance by default
- Added link to [GitHub Discussions](https://github.com/joedevivo/vscode-circuitpython/discussions) for Q&A.


## [0.1.9]
- Library management fix [#37](https://github.com/joedevivo/vscode-circuitpython/pull/37)
  - thanks @makermelissa!
- Fixes edge case where extension crashes if bundle was never loaded
- Updated boards for March 2021
- Update dependencies

## [0.1.8]
- all the fun of 0.1.7, but built with proper bindings

## ~~[0.1.7]~~
- Upgraded Electron to 11.2.1
- Updated VSCode version requirement to 1.53.0
- Feb 2021 board refresh

## [0.1.6]
- Jan 2021 board refresh

## [0.1.5]
- Fixed issue installing 6.x mpy stubs on computers that had previous versions

## [0.1.4]
- Improved logic for generating board stubs

## [0.1.3]
- New Azure Pipelie Build
  - Should resolve native binding issues
  - New Boards are added in the build from adafruit/circuitpython:main
    - TODO: Let the user choose their version of CircuitPython, with the boards supported by that version.

## [0.1.2]
- Added `Use Ctrl-C to enter the REPL` on Serial Monitor Connect
- New Boards
  - Radomir Dopieralski : Fluff M0
  - Alorium Technology, LLC : AloriumTech Evo M51
  - maholli : PyCubed
  - PJRC : Teensy 4.1
  - Makerdiary : Pitaya Go
  - Nordic Semiconductor : PCA10100
  - HiiBot : HiiBot BlueFi
  - Espressif : Saola 1 w/WROOM
  - Espressif : Saola 1 w/WROVER

## [0.1.1]
- Updated stubs for Circuit Python 5.3.0
- New Boards
  - NFC Copy Cat
  - ST STM32F746G Discovery - CPy
  - OpenMV-H7 R1
  - Nucleo H743ZI - CPy
  - Nucleo F767ZI - CPy
  - Nucleo F746zg - CPy
  - Simmel
- Native bindings for Raspberry Pi/ARM

## [0.1.0]

- Reworked internals to be less `static`
- more robust autocomplete path handling
- updated stubs for Circuit Python 5.1.0
- new boards

## [0.0.5]

- Removed dialog on serial monitor open
- stores board info in settings.json, which has the effect of persisting your
  board choice for a project between sessions.
- Added command to manually check for bundle update

## [0.0.4]

- Refactored the serial monitor from an output channel to a terminal, allowing
  interaction with the Circuit Python REPL

## [0.0.3]

- More board completions

## [0.0.2]

- Rebuilt for Electron@7
- Reimplemented circup features directly in the extension, see libraryManager.ts for details
  - moves older bundles to the Trash instead of deleting.
- Fixed OS dependent paths ( removed direct calls to path.posix )
- In theory, native bindings should work for windows and mac
  - no linux support yet, but it's on the way. I need to streamline the very
    manual process it took to get these bindings done.

## [0.0.1]

- Initial release

# building vscode-circuitpython V2

WARNING : this info should be considered preliminary, needs to be verified (especially on a linux system) 


## Requirements

Minumum versions:
  - python: 3.11.0
  - node: 22.18.0
  - npm: 10.9.3



### building stubs
This extension used the "circuitpython-stubs" built by "setup-py.stubs" in the circuitpython repo.  
"setup-py.stubs" requires **tomllib**, so a fairly recent version of Python is required.

## building node/typescript

According to https://www.npmjs.com/package/@electron/rebuild, node v22.12.0 or higher os required

import * as vscode from 'vscode';
import { Board } from './boards/board';
import * as path from 'path';
import * as fs from 'fs';
import { Container } from './container';

export class Project implements vscode.Disposable {

  private _context: vscode.ExtensionContext = null;
  private _circuitPythonVersion: string = null;

  private _autoCompleteBoard: string = "";
  private _autoCompleteStdLib: string = "";
  private _autoCompleteBundle: string = "";
  private _autoCompleteExtra: string[] = [];

  private _boardVID: string = null;
  private _boardPID: string = null;
  private _board: Board = null;

  public constructor(context: vscode.ExtensionContext) {
    this._context = context;

    let autoConf: vscode.WorkspaceConfiguration = vscode.workspace.getConfiguration("python.analysis");
    let paths: string[] = autoConf.get("extraPaths");

    // Load paths from last session
    if (paths.length >= 3) {
      this._autoCompleteBoard = paths.shift();
      this._autoCompleteStdLib = paths.shift();
      this._autoCompleteBundle = paths.shift();
      this._autoCompleteExtra = paths;
    }
    // Overwrite stdlib stubs, since the absolute path could have been for any
    // system and we know for sure what we've got for them.
    this._autoCompleteStdLib = path.join(this._context.extensionPath, "stubs");
    
    // Get board info from settings
    let boardConf: vscode.WorkspaceConfiguration = vscode.workspace.getConfiguration("circuitpython.board");

    // Set the CircuitPython Version, the major of which will be used for finding the right mpy files
    let version: string = boardConf.get("version");
    if (version) {
      this._circuitPythonVersion = version;
    }

    let vid: string = boardConf.get("vid");
    let pid: string = boardConf.get("pid");

    // setBoard takes care of this._autoCompleteBoard. If vid && pid are undefined, the existing value remains.
    if (vid && pid) { 
      let b: Board = Board.lookup(vid, pid);
      this.setBoard(b);
    }
  }

  public dispose() {}

  public setBoard(board: Board) {
    if (!(this._board &&
      this._board.vid === board.vid &&
      this._board.pid === board.pid
      )) {
      this._boardVID = board.vid;
      this._boardPID = board.pid;
      this._board = board;
      this._autoCompleteBoard = path.join(this._context.extensionPath, "boards", board.vid, board.pid);
      this.refreshAutoCompletePaths();
      vscode.workspace.getConfiguration().update("circuitpython.board.vid", board.vid);
      vscode.workspace.getConfiguration().update("circuitpython.board.pid", board.pid);
    }
  }

  public getBoard(): Board {
    return this._board;
  }

  public updateBundlePath(p: string) {
    this._autoCompleteBundle = p;
    this.refreshAutoCompletePaths();
  }

  public refreshAutoCompletePaths() {
    let paths: string[] = [
      this._autoCompleteBoard,
      this._autoCompleteStdLib,
      this._autoCompleteBundle
    ].concat(this._autoCompleteExtra);

    console.log("Updating python.analysis.extraPaths with:", paths);

    // Update user settings (global)
    vscode.workspace.getConfiguration().update(
      "python.analysis.extraPaths",
      paths,
      vscode.ConfigurationTarget.Global
    );

    // Check if a workspace settings file exists and update it
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (workspaceFolders && workspaceFolders.length > 0) {
      const workspaceSettingsPath = path.join(workspaceFolders[0].uri.fsPath, '.vscode', 'settings.json');

      // Check if the workspace settings file exists
      if (fs.existsSync(workspaceSettingsPath)) {
        vscode.workspace.getConfiguration().update(
          "python.analysis.extraPaths",
          paths,
          vscode.ConfigurationTarget.Workspace
        );
      }
    }
  }
}
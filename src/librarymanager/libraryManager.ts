import * as vscode from "vscode";
import * as path from "path";
import * as fs from "fs";
import * as axios from "axios";
import AdmZip from "adm-zip";
import { String } from "typescript-string-operations";
import * as _ from "lodash";
import globby from 'globby';
import * as fs_extra from "fs-extra";
import trash from "trash";
import { Container } from "../container";

// Master debug switch
const DEBUG_MODE = true;
function debugLog(message: string) {
  if (DEBUG_MODE) {
    console.log(message);
  }
}

// LibraryQP class
class LibraryQP implements vscode.QuickPickItem {
  public label: string = null;
  public description: string = null;
  public bundleLib: Library = null;
  public projectLib: Library = null;
  private op: string = null;

  public constructor(b: Library, p: Library) {
    this.bundleLib = b;
    this.projectLib = p;
    if (b === undefined) {
      this.op = "custom";
      if (p === null) {
        this.label = "Custom";
        this.description = "Cannot update";
      } else {
        this.label = p.name;
        this.description = `v${p.version} is a custom library. Not updateable`;
      }
    } else {
      this.label = b.name;
      if (p === null) {
        this.op = "install";
        this.description = `Install version ${b.version}`;
      } else if (b.version !== p.version) {
        this.op = "update";
        this.description = `Update from v${p.version} to v${b.version}`;
      } else {
        this.op = null;
        this.description = `v${p.version} is installed and up to date.`;
      }
    }
  }

  public onClick() {
    switch (this.op) {
      case "install":
        this.install();
        break;
      case "update":
        this.update();
        break;
      default:
        break;
    }
    Container.reloadProjectLibraries();
  }

  private install() {
    let src: string = LibraryManager.getMpy(
      path.basename(this.bundleLib.location)
    );
    if (this.bundleLib.isDirectory) {
      fs_extra.copySync(
        src,
        path.join(
          Container.getProjectLibDir(),
          path.basename(this.bundleLib.location)
        ),
        { overwrite: true }
      );
    } else {
      fs.copyFileSync(
        src,
        path.join(
          Container.getProjectLibDir(),
          path.basename(this.bundleLib.location, ".py") + ".mpy"
        )
      );
    }
  }

  private update() {
    this.install();
  }
}

// Library class
export class Library {
  public name: string;
  public version: string;
  public location: string;
  public isDirectory: boolean;

  constructor(name: string, version: string, location: string, isDirectory: boolean) {
    this.name = name;
    this.version = version;
    this.location = location;
    this.isDirectory = isDirectory;
  }

  public static async from(filePath: string, metadata: any): Promise<Library> {
    const name = Library.extractName(filePath);
    const isDirectory = fs.statSync(filePath).isDirectory();
    const version = metadata[name]?.version || "unknown";
    return new Library(name, version, filePath, isDirectory);
  }

  private static extractName(filePath: string): string {
    return path.basename(filePath, path.extname(filePath));
  }

  public static loadMetadata(jsonFilePath: string): any {
    try {
      const rawData = fs.readFileSync(jsonFilePath, "utf8");
      return JSON.parse(rawData);
    } catch (error) {
      console.error(`Error loading metadata from ${jsonFilePath}:`, error);
      return {};
    }
  }
}

// LibraryManager class
export class LibraryManager implements vscode.Disposable {
  public static BUNDLE_URL: string =
    "https://github.com/adafruit/Adafruit_CircuitPython_Bundle";
  public static BUNDLE_SUFFIXES: string[] = ["py", "8.x-mpy", "9.x-mpy"];
  public static BUNDLE_VERSION_REGEX: RegExp = /\d\d\d\d\d\d\d\d/;
  private storageRootDir: string = null;
  private bundleDir: string = null;
  private localBundleDir: string = null;
  public tag: string = null;
  public cpVersion = null;
  public mpySuffix: string = "py";
  public projectLibDir: string = null;
  private libraries: Map<string, Library> = new Map<string, Library>();
  private workspaceLibraries: Map<string, Library> = new Map<string, Library>();

  public dispose() {}

  public constructor(p: string) {
    this.setStorageRoot(p);
  }

  private setStorageRoot(root: string) {
    this.storageRootDir = root;
    this.bundleDir = path.join(this.storageRootDir, "bundle");
    fs.mkdirSync(this.bundleDir, { recursive: true });
  }

  public async initialize() {
    debugLog("Initializing LibraryManager.");
    try {
      let tag = this.getMostRecentBundleOnDisk();
      if (!tag || !this.verifyBundle(tag)) {
        debugLog("No valid bundle found on disk, attempting to update.");
        await this.updateBundle();
      } else {
        this.tag = tag;
        this.localBundleDir = path.join(this.bundleDir, tag);
      }
      await this.loadBundleMetadata();
      this.projectLibDir = this.getOrCreateProjectLibDir();
      debugLog("Project library directory: " + this.projectLibDir);
      this.workspaceLibraries = await this.loadLibraryMetadata(this.projectLibDir);
      this.cpVersion = this.getProjectCPVersion();
      if (this.cpVersion) {
        let v: string[] = this.cpVersion.split(".");
        if (LibraryManager.BUNDLE_SUFFIXES.includes(`${v[0]}.x-mpy`)) {
          this.mpySuffix = `${v[0]}.x-mpy`;
        }
      }
    } catch (error) {
      console.error("Error during initialization:", error);
    }
  }

  private getOrCreateProjectLibDir(): string {
    if (!this.projectLibDir) {
      this.projectLibDir = path.join(this.getProjectRoot(), "lib");
      if (!fs.existsSync(this.projectLibDir)) {
        fs.mkdirSync(this.projectLibDir);
      }
    }
    return this.projectLibDir;
  }

  private getProjectCPVersion(): string {
    let confVer: string = vscode.workspace
      .getConfiguration("circuitpython.board")
      .get("version");
    let bootOut: string = null;
    let ver: string = null;
    let b: string = path.join(this.getProjectRoot(), "boot_out.txt");
    let exists: boolean = fs.existsSync(b);
    if (!exists && confVer) {
      ver = confVer;
    } else if (exists) {
      bootOut = b;
      try {
        let _a: string = fs.readFileSync(b, "utf8").toString();
        let _b: string[] = _a.split(";");
        let _c: string = _b[0];
        let _d: string[] = _c.split(" ");
        let _e: string = _d[2];
        ver = _e;
      } catch (error) {
        ver = "unknown";
      }
    }
    vscode.workspace
      .getConfiguration("circuitpython.board")
      .update("version", ver);
    return ver;
  }

  private getProjectRoot(): string {
    let root: string = null;
    vscode.workspace.workspaceFolders.forEach((f) => {
      let r: string = path.join(f.uri.fsPath);
      if (!root && fs.existsSync(r)) {
        let b: string = path.join(r, "boot_out.txt");
        if (fs.existsSync(b)) {
          root = r;
        }
      }
    });
    if (!root) {
      root = vscode.workspace.workspaceFolders[0].uri.fsPath;
    }
    return root;
  }

  public async updateBundle() {
    debugLog("Updating bundle.");
    try {
      let tag: string = await this.getLatestBundleTag();
      if (!tag) {
        throw new Error("Failed to fetch the latest bundle tag.");
      }
      let localBundleDir: string = path.join(this.bundleDir, tag);
      debugLog(`Downloading new bundle: ${tag}`);
      await this.getBundle(tag);
      this.tag = tag;
      this.localBundleDir = localBundleDir;
      vscode.window.showInformationMessage(`Bundle updated to ${tag}`);
      if (!this.verifyBundle(tag)) {
        throw new Error("Failed to verify the downloaded bundle.");
      }
      Container.updateBundlePath();
    } catch (error) {
      console.error("Error during bundle update:", error);
    }
  }

  private async getBundle(tag: string) {
    debugLog(`Downloading bundle for tag: ${tag}`);
    let metdataUrl: string =
      LibraryManager.BUNDLE_URL +
      "/releases/download/{0}/adafruit-circuitpython-bundle-{0}.json";
    let urlRoot: string =
      LibraryManager.BUNDLE_URL +
      "/releases/download/{0}/adafruit-circuitpython-bundle-{1}-{0}.zip";
    this.tag = tag;
    let metadataUrl: string = String.Format(metdataUrl, tag);
    fs.mkdirSync(path.join(this.storageRootDir, "bundle", tag), {
      recursive: true,
    });
    try {
      for await (const suffix of LibraryManager.BUNDLE_SUFFIXES) {
        debugLog(`Processing bundle with suffix: ${suffix}`);
        let url: string = String.Format(urlRoot, tag, suffix);
        let p: string = path.join(this.storageRootDir, "bundle", tag);
        await axios.default
          .get(url, { responseType: "stream" })
          .then((response) => {
            const zipPath = path.join(p, `adafruit-circuitpython-bundle-${suffix}-${tag}.zip`);
            const writer = fs.createWriteStream(zipPath);
            response.data.pipe(writer);
            writer.on('finish', async () => {
              await this.extractBundle(zipPath, p);
            });
          })
          .catch((error) => {
            console.error(`Error downloading ${suffix} bundle: ${url}`, error);
          });
      }
      debugLog(`Bundle for tag ${tag} downloaded and processed successfully.`);
    } catch (error) {
      console.error(`Error processing bundle for tag ${tag}:`, error);
    }
    let dest: string = path.join(
      this.storageRootDir,
      "bundle",
      tag,
      `adafruit-circuitpython-bundle-${tag}.json`
    );
    await axios.default
      .get(metadataUrl, { responseType: "json" })
      .then((response) => {
        fs.writeFileSync(dest, JSON.stringify(response.data), {
          encoding: "utf8",
        });
      })
      .catch((error) => {
        console.log(`Error downloading bundle metadata: ${metadataUrl}`, error);
      });
    Container.loadBundleMetadata();
  }

  private async extractBundle(zipPath: string, extractPath: string) {
    debugLog(`Starting to extract bundle: ${zipPath}`);
    try {
      const zip = new AdmZip(zipPath);
      zip.extractAllTo(extractPath, true);
      debugLog(`Successfully extracted bundle: ${zipPath}`);
    } catch (error) {
      console.error(`Error during extraction of ${zipPath}:`, error);
    }
  }

  private verifyBundle(tag: string): boolean {
    debugLog(`Verifying bundle for tag: ${tag}`);
    let localBundleDir: string = path.join(this.bundleDir, tag);
    if (!fs.existsSync(localBundleDir)) {
      return false;
    }
    let bundles: fs.Dirent[] = fs
      .readdirSync(localBundleDir, { withFileTypes: true })
      .sort();
    let suffixRegExp: RegExp = new RegExp(
      `adafruit-circuitpython-bundle-(.*)-${tag}`
    );
    let suffixes: string[] = [];
    bundles.forEach((b) => {
      if (b.isDirectory()) {
        let p: string = path.join(localBundleDir, b.name);
        let lib: string[] = fs.readdirSync(p).filter((v, i, a) => v === "lib");
        if (lib.length !== 1) {
          return false;
        }
        suffixes.push(b.name.match(suffixRegExp)[1]);
      }
    });
    this.localBundleDir = localBundleDir;
    fs.readdir(this.bundleDir, { withFileTypes: true }, (err, bundles) => {
      bundles.forEach((b) => {
        if (b.isDirectory() && b.name !== this.tag) {
          let old: string = path.join(this.bundleDir, b.name);
          trash(old).then(() => null);
        }
      });
    });
    return true;
  }

  private async getLatestBundleTag(): Promise<string> {
    debugLog("Fetching the latest bundle tag.");
    let r: axios.AxiosResponse = await axios.default.get(
      "https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases/latest",
      { headers: { Accept: "application/json" } }
    );
    return await r.data.tag_name;
  }

  private getMostRecentBundleOnDisk(): string {
    if (!fs.existsSync(this.bundleDir)) {
      return null;
    }
    let tag: string = fs
      .readdirSync(this.bundleDir)
      .filter((dir: string) => LibraryManager.BUNDLE_VERSION_REGEX.test(dir))
      .sort()
      .reverse()
      .shift();
    return tag;
  }

  public static getMpy(name: string): string {
    if (path.extname(name) === ".py" && Container.getMpySuffix() !== "py") {
      name = path.basename(name, ".py") + ".mpy";
    }
    return path.join(Container.getBundlePath(), name);
  }

  public bundlePath(suffix: string): string {
    debugLog(`bundlePath called with suffix: ${suffix}`);
    if (!this.localBundleDir || !this.tag) {
      throw new Error("localBundleDir or tag is not set");
    }
    return path.join(
      this.localBundleDir,
      `adafruit-circuitpython-bundle-${suffix}-${this.tag}`,
      `lib`
    );
  }

  public async loadBundleMetadata(): Promise<boolean> {
    let bundlePath = this.bundlePath("py");
    this.libraries = await this.loadLibraryMetadata(bundlePath);
    return true;
  }

  private async loadLibraryMetadata(
    rootDir: string
  ): Promise<Map<string, Library>> {
    let jsonMetadataFile = path.join(
      this.localBundleDir,
      `adafruit-circuitpython-bundle-${this.tag}.json`
    );
    let rawData = fs.readFileSync(jsonMetadataFile, "utf8");
    let jsonData = JSON.parse(rawData);
    const libDirs: string[] = await globby("*", {
      absolute: true,
      cwd: rootDir,
      deep: 1,
      onlyFiles: false,
    });
    let libraries: Array<Promise<Library>> = libDirs.map((p, i, a) =>
      Library.from(p, jsonData).then((l) => {
        if (rootDir.startsWith(this.localBundleDir)) {
          l.version = jsonData[l.name].version;
        }
        return l;
      })
    );
    return new Promise<Map<string, Library>>(async (resolve, reject) => {
      let libs: Array<Library> = await Promise.all(libraries).catch((error) => {
        console.error("Error loading library metadata:", error);
        return new Array<Library>();
      });
      let libraryMetadata: Map<string, Library> = new Map<string, Library>();
      libs.forEach((l: Library) => {
        libraryMetadata.set(l.name, l);
      });
      return resolve(libraryMetadata);
    });
  }

  // Newly added methods
  public async show() {
    debugLog("Showing library choices.");
    let choices: LibraryQP[] = this.getAllChoices();
    const chosen = await vscode.window.showQuickPick(choices);
    if (chosen) {
      chosen.onClick();
    }
  }

  public async list() {
    debugLog("Listing installed libraries.");
    let choices: LibraryQP[] = this.getInstalledChoices();
    const chosen = await vscode.window.showQuickPick(choices);
    if (chosen) {
      chosen.onClick();
    }
  }

  public async update() {
    debugLog("Starting 'Update All Libraries' command.");
    try {
      let choices: LibraryQP[] = this.getInstalledChoices();
      if (choices.length === 0) {
        debugLog("No libraries installed to update.");
      } else {
        choices.forEach((c: LibraryQP) => {
          debugLog(`Updating library: ${c.label}`);
          c.onClick();
        });
        debugLog("All libraries have been updated.");
      }
    } catch (error) {
      console.error("Error during library update:", error);
    }
  }

  public async reloadProjectLibraries() {
    debugLog("Reloading project libraries.");
    this.workspaceLibraries = await this.loadLibraryMetadata(
      this.projectLibDir
    );
  }

  private getAllChoices(): LibraryQP[] {
    let installedChoices: LibraryQP[] = this.getInstalledChoices();
    let uninstalledChoices: LibraryQP[] = this.getUninstalledChoices();
    return installedChoices.concat(uninstalledChoices);
  }

  private getInstalledChoices(): LibraryQP[] {
    let choices: LibraryQP[] = new Array<LibraryQP>();
    Array.from(this.workspaceLibraries.keys())
      .sort()
      .forEach((v, i, a) => {
        let b: Library = this.libraries.get(v);
        let p: Library = this.workspaceLibraries.get(v);
        if (p) {
          let label = p.name;
          let description = `v${p.version}`;
          debugLog(`Installed Library: ${label}, Description: ${description}`);
        }
        choices.push(new LibraryQP(b, p));
      });
    return choices;
  }

  private getUninstalledChoices(): LibraryQP[] {
    let choices: LibraryQP[] = new Array<LibraryQP>();
    Array.from(this.libraries.keys())
      .sort()
      .forEach((v, i, a) => {
        let b: Library = this.libraries.get(v);
        if (!this.workspaceLibraries.has(v)) {
          choices.push(new LibraryQP(b, null));
        }
      });
    return choices;
  }
}
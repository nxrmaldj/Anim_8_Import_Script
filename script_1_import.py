# script_1_import.py
# Run via: Unreal Editor > Python Script Runner
# Or: UnrealEditor.exe MyProject.uproject -ExecutePythonScript="C:/Scripts/script_1_import.py"

# ─── CONFIG ──────────────────────────────────────────────────────────────────
# Change these values once per project. Everything below reads from this block.

# Path on disk where Maya exported all FBX/ABC files (flat folder).
# Leave blank ("") to get a folder-picker dialog every time the script runs.
SOURCE_FOLDER = ""

# Root content browser folders — these never change
PROJECT_ROOT = "/Game/Production"
ASSETS_ROOT  = "/Game/Assets"

# Set this per project
PROJECT_NAME = "FindingKiiboh"  # ← change for each project

# Known Skeletal Meshes already in the project.
# Key   = name token in the filename  (e.g. 'Kiiboh' in Shot01_Kiiboh_anim.fbx)
# Value = full content browser path to the existing SK asset
KNOWN_CHARACTERS = {
    "Kiiboh":              "/Game/Assets/Characters/Kiiboh/SK_Kiiboh",
    "Kiiboh_Damaged":      "/Game/Assets/Characters/Kiiboh/SK_Kiiboh_Damaged",
    "Kiiboh_Leg_Head_Tail":"/Game/Assets/Characters/Kiiboh/SK_Kiiboh_Leg_Head_Tail",
    "Kiiboh_Part_All":     "/Game/Assets/Characters/Kiiboh/SK_Kiiboh_Part_All",
    "Song":                "/Game/Assets/Characters/Song/SK_Song",
    # Add more characters here as needed
}

# Alembic import scale (1.0 = default; change if assets appear the wrong size)
ALEMBIC_SCALE = 1.0

# Set to True to preview what the script would do without importing anything.
# All folder creation and imports are skipped; the log shows the full plan.
DRY_RUN = False

# ─── END CONFIG ──────────────────────────────────────────────────────────────

import os
import re
import unreal

# Shot number pattern: Shot01, Shot11A, etc.
_SHOT_RE = re.compile(r'^(Shot\d+[A-Za-z]?)_', re.IGNORECASE)


# ─── FOLDER PICKER ───────────────────────────────────────────────────────────

def pick_folder(title="Select Maya Export Folder (FBX / ABC files)"):
    """
    Open a native folder-picker dialog and return the chosen path.
    Tries tkinter first (bundled with most Python builds).
    Falls back to a PowerShell dialog on Windows if tkinter is unavailable.
    Returns an empty string if the user cancels.
    """
    # ── Option A: tkinter (works in UE's Python on most platforms) ───────────
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", True)
        folder = filedialog.askdirectory(title=title, parent=root)
        root.destroy()
        return folder.replace("\\", "/") if folder else ""
    except Exception:
        pass

    # ── Option B: PowerShell WinForms dialog (Windows fallback) ─────────────
    try:
        import subprocess
        ps = (
            "Add-Type -AssemblyName System.Windows.Forms; "
            "$d = New-Object System.Windows.Forms.FolderBrowserDialog; "
            f"$d.Description = '{title}'; "
            "$d.ShowNewFolderButton = $false; "
            "if ($d.ShowDialog() -eq 'OK') { $d.SelectedPath } else { '' }"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True, text=True, timeout=120
        )
        return result.stdout.strip().replace("\\", "/")
    except Exception:
        pass

    return ""


# ─── FILENAME PARSING ────────────────────────────────────────────────────────

def parse_filename(filename):
    """
    Inspect a filename and return a dict describing what it is.

    Returns:
        {
            shot    : str | None   e.g. 'Shot01' — None means shared asset
            token   : str          e.g. 'Kiiboh_Damaged', 'Debris', 'Camera'
            kind    : str          'camera' | 'anim' | 'alembic' | 'static' | 'shared'
            sk_path : str | None   content-browser skeleton path (anim only)
        }

    Detection order (first match wins):
        1. token == 'Camera'              → camera  (skipped by this script)
        2. token in KNOWN_CHARACTERS      → anim
        3. extension is .abc              → alembic
        4. extension is .fbx (fallback)   → static
        No Shot## prefix in filename      → shared  (checked before steps 2-4)
    """
    base, ext = os.path.splitext(filename)
    ext = ext.lower()

    # Strip trailing _anim suffix (case-insensitive)
    base_no_anim = re.sub(r'_anim$', '', base, flags=re.IGNORECASE)

    # Extract shot prefix
    shot_match = _SHOT_RE.match(base_no_anim)
    shot = shot_match.group(1) if shot_match else None

    # Token = everything after "Shot##_"
    token = base_no_anim[len(shot) + 1:] if shot else base_no_anim

    # 1. Camera check
    if token.lower() == 'camera':
        return {"shot": shot, "token": token, "kind": "camera", "sk_path": None}

    # Files without a Shot## prefix go to the shared _Assets folder
    if not shot:
        return {"shot": None, "token": token, "kind": "shared", "sk_path": None}

    # 2. Known character check — sort longest key first to avoid partial matches
    for char_name in sorted(KNOWN_CHARACTERS, key=len, reverse=True):
        if token == char_name:
            return {"shot": shot, "token": char_name, "kind": "anim",
                    "sk_path": KNOWN_CHARACTERS[char_name]}

    # 3. Alembic check
    if ext == '.abc':
        return {"shot": shot, "token": token, "kind": "alembic", "sk_path": None}

    # 4. Static mesh fallback (unknown FBX)
    unreal.log_warning(
        f"  [WARN] '{filename}' — character not in KNOWN_CHARACTERS; "
        "importing as Static Mesh. Add it to the config if it should be an animation."
    )
    return {"shot": shot, "token": token, "kind": "static", "sk_path": None}


# ─── FOLDER HELPERS ──────────────────────────────────────────────────────────

def ensure_directory(content_path):
    """Create a Content Browser directory only if it does not already exist."""
    if not unreal.EditorAssetLibrary.does_directory_exist(content_path):
        unreal.EditorAssetLibrary.make_directory(content_path)
        unreal.log(f"    [DIR] Created: {content_path}")


def destination_for(kind, shot):
    """Return the target Content Browser folder path for a given kind/shot."""
    if kind in ("anim", "alembic"):
        return f"{PROJECT_ROOT}/{PROJECT_NAME}/{shot}/Animation"
    if kind == "static":
        return f"{ASSETS_ROOT}/Props"
    if kind == "shared":
        return f"{PROJECT_ROOT}/{PROJECT_NAME}/_Assets"
    return None


# ─── IMPORT FUNCTIONS ────────────────────────────────────────────────────────

def import_animation_fbx(disk_path, sk_path, destination, asset_name):
    """
    Import a character animation FBX.
    Skips the mesh re-import; only loads the animation track onto the
    existing skeleton referenced by sk_path.
    """
    sk_asset = unreal.load_asset(sk_path)
    if sk_asset is None:
        unreal.log_warning(
            f"    [WARN] Skeleton/SkeletalMesh not found at '{sk_path}'. "
            f"Skipping {os.path.basename(disk_path)}"
        )
        return False

    if isinstance(sk_asset, unreal.SkeletalMesh):
        skeleton = sk_asset.skeleton
    elif isinstance(sk_asset, unreal.Skeleton):
        skeleton = sk_asset
    else:
        unreal.log_warning(
            f"    [WARN] Asset at '{sk_path}' is not a SkeletalMesh or Skeleton. "
            f"Skipping {os.path.basename(disk_path)}"
        )
        return False

    import_ui = unreal.FbxImportUI()
    import_ui.import_mesh            = False
    import_ui.import_animations      = True
    import_ui.import_as_skeletal     = False
    import_ui.create_physics_asset   = False
    import_ui.mesh_type_to_import    = unreal.FBXImportType.FBXIT_ANIMATION
    import_ui.skeleton               = skeleton
    import_ui.anim_sequence_import_data = unreal.FbxAnimSequenceImportData()

    task = unreal.AssetImportTask()
    task.automated       = True
    task.filename        = disk_path
    task.destination_path = destination
    task.destination_name = asset_name
    task.replace_existing = False
    task.save            = True
    task.options         = import_ui

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    return True


def import_alembic(disk_path, destination, asset_name):
    """
    Import an Alembic (.abc) file as a GeometryCache with flattened tracks
    and per-vertex motion vectors.
    """
    settings = unreal.AbcImportSettings()
    settings.import_type = unreal.AlembicImportType.GEOMETRY_CACHE

    geo_settings = unreal.AbcGeometryCacheSettings()
    geo_settings.flatten_tracks = True
    settings.geometry_cache_settings = geo_settings

    conversion = unreal.AbcConversionSettings()
    conversion.scale = unreal.Vector(ALEMBIC_SCALE, ALEMBIC_SCALE, ALEMBIC_SCALE)
    settings.conversion_settings = conversion

    task = unreal.AssetImportTask()
    task.automated        = True
    task.filename         = disk_path
    task.destination_path = destination
    task.destination_name = asset_name
    task.replace_existing = False
    task.save             = True
    task.options          = settings

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    return True


def import_static_mesh(disk_path, destination, asset_name):
    """Import an FBX as a Static Mesh (unknown prop / no character match)."""
    import_ui = unreal.FbxImportUI()
    import_ui.import_mesh          = True
    import_ui.import_animations    = False
    import_ui.import_as_skeletal   = False
    import_ui.create_physics_asset = False
    import_ui.mesh_type_to_import  = unreal.FBXImportType.FBXIT_STATIC_MESH

    task = unreal.AssetImportTask()
    task.automated        = True
    task.filename         = disk_path
    task.destination_path = destination
    task.destination_name = asset_name
    task.replace_existing = False
    task.save             = True
    task.options          = import_ui

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    return True


# ─── DISPATCH ────────────────────────────────────────────────────────────────

def dispatch_import(disk_path, info, asset_name):
    """
    Route a file to the correct import function based on its detected kind.
    Returns True on success, False on skip/failure.
    When DRY_RUN is True, logs the plan and returns True without touching UE.
    """
    kind = info["kind"]
    destination = destination_for(kind, info["shot"])

    if destination is None:
        unreal.log_warning(f"    [WARN] Could not resolve destination for kind='{kind}'. Skipping.")
        return False

    if DRY_RUN:
        unreal.log(f"    [DRY RUN] Would create dir : {destination}")
        unreal.log(f"    [DRY RUN] Would import     : {os.path.basename(disk_path)}")
        unreal.log(f"    [DRY RUN] Destination      : {destination}/{asset_name}")
        if info["sk_path"]:
            unreal.log(f"    [DRY RUN] Skeleton         : {info['sk_path']}")
        return True

    ensure_directory(destination)

    if kind == "anim":
        return import_animation_fbx(disk_path, info["sk_path"], destination, asset_name)

    if kind == "alembic":
        return import_alembic(disk_path, destination, asset_name)

    if kind == "static":
        return import_static_mesh(disk_path, destination, asset_name)

    if kind == "shared":
        _, ext = os.path.splitext(disk_path)
        if ext.lower() == '.abc':
            return import_alembic(disk_path, destination, asset_name)
        return import_static_mesh(disk_path, destination, asset_name)

    return False


# ─── MAIN ────────────────────────────────────────────────────────────────────

def run():
    # ── Resolve source folder ────────────────────────────────────────────────
    source = SOURCE_FOLDER.strip()

    if not source or not os.path.isdir(source):
        if source:
            unreal.log_warning(f"SOURCE_FOLDER '{source}' not found on disk. Opening folder picker...")
        else:
            unreal.log("SOURCE_FOLDER is not set. Opening folder picker...")

        source = pick_folder()

        if not source:
            unreal.log_warning("No folder selected — aborting.")
            return

        if not os.path.isdir(source):
            unreal.log_error(f"Selected path does not exist: {source}")
            return

    unreal.log(f"Source folder: {source}")

    all_files = sorted(
        f for f in os.listdir(source)
        if os.path.splitext(f)[1].lower() in ('.fbx', '.abc')
    )

    if not all_files:
        unreal.log_warning(f"No FBX or ABC files found in: {source}")
        return

    sep = "=" * 60
    unreal.log(f"\n{sep}")
    unreal.log("Script 1 — Import & Folder Setup")
    unreal.log(f"Project : {PROJECT_NAME}")
    unreal.log(f"Source  : {source}")
    unreal.log(f"Files   : {len(all_files)}")
    unreal.log(sep)

    counts = {"imported": 0, "skipped": 0, "errors": 0}

    for filename in all_files:
        disk_path = os.path.join(source, filename).replace("\\", "/")
        info      = parse_filename(filename)
        kind      = info["kind"]
        shot      = info["shot"]
        token     = info["token"]

        unreal.log(f"\n  {filename}")
        unreal.log(f"    kind={kind}  shot={shot}  token={token}")

        if kind == "camera":
            unreal.log("    → SKIPPED — camera is handled by Script 2")
            counts["skipped"] += 1
            continue

        # Build the asset name: strip extension and trailing _anim
        base, _ = os.path.splitext(filename)
        asset_name = re.sub(r'_anim$', '', base, flags=re.IGNORECASE)

        try:
            ok = dispatch_import(disk_path, info, asset_name)
            if ok:
                dest = destination_for(kind, shot)
                unreal.log(f"    ✓ Imported → {dest}/{asset_name}")
                counts["imported"] += 1
            else:
                counts["skipped"] += 1
        except Exception as exc:
            unreal.log_error(f"    ✗ Error importing '{filename}': {exc}")
            counts["errors"] += 1

    unreal.log(f"\n{sep}")
    unreal.log(
        f"Done — Imported: {counts['imported']}  "
        f"Skipped: {counts['skipped']}  "
        f"Errors: {counts['errors']}"
    )
    unreal.log(sep + "\n")


# Guard lets this file be imported by test_parse.py without executing run().
# UE's script runner sets __name__ == '__main__' just like the CLI does.
if __name__ == '__main__':
    run()

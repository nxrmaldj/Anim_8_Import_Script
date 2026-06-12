# script_1_organize.py
#
# Staging Organizer — moves assets the TA already imported (via the native
# UE import window) from the staging folder into the correct production
# folder structure. This script never imports anything itself.
#
# Workflow:
#   1. TA imports all FBX/ABC batches into /Game/Staging through the
#      native import window (skeleton linking handled there).
#   2. Run this script (from an Editor Utility Widget, the Python console,
#      or the script runner).
#   3. Assets are routed by their REAL asset type + name into:
#        /Game/Production/{Project}/Shot##/Animation/   anims + geo caches
#        /Game/Assets/Props/                            static meshes
#        /Game/Assets/Characters/{Name}/                SK meshes/skeletons
#        /Game/Production/{Project}/_Assets/            no shot prefix
#
# From an Editor Utility Widget, call:
#   import script_1_organize
#   script_1_organize.run(project_name="MyProject", dry_run=False)

# ─── CONFIG ──────────────────────────────────────────────────────────────────

# Content Browser folder the TA imports everything into
STAGING_FOLDER = "/Game/Staging"

# Root content browser folders — these never change
PROJECT_ROOT = "/Game/Production"
ASSETS_ROOT  = "/Game/Assets"

# Default project name — pre-fills the dialog / widget field
PROJECT_NAME = "FindingKiiboh"

# Set True to log the full move plan without moving anything
DRY_RUN = False

# ─── END CONFIG ──────────────────────────────────────────────────────────────

import re
import unreal

from pipeline_common import get_open_project_name, resolve_production_project

# Shot number pattern: Shot01, Shot11A, etc.
_SHOT_RE = re.compile(r'^(Shot\d+[A-Za-z]?)_', re.IGNORECASE)

# Asset classes this script knows how to route
ANIM_CLASSES      = {"AnimSequence"}
GEOCACHE_CLASSES  = {"GeometryCache"}
STATIC_CLASSES    = {"StaticMesh"}
CHARACTER_CLASSES = {"SkeletalMesh", "Skeleton", "PhysicsAsset"}

# Everything else (Materials, Textures, etc.) is left in staging with a
# warning — those usually belong next to whichever mesh owns them and the
# TA should place them deliberately.


# ─── NAME PARSING ────────────────────────────────────────────────────────────

def parse_asset_name(name):
    """
    Extract the shot prefix from an asset name.
    Returns (shot, remainder) — shot is None when there is no Shot## prefix.
      'Shot01_Song_anim'  → ('Shot01', 'Song_anim')
      'Dumpster_Location' → (None, 'Dumpster_Location')
    """
    match = _SHOT_RE.match(name)
    if match:
        shot = match.group(1)
        return shot, name[len(shot) + 1:]
    return None, name


def clean_character_name(name):
    """
    Derive a character folder name from a skeletal asset name.
      'SK_Song'                      → 'Song'
      'Shot01_Song_anim_Skeleton'    → 'Song'
      'Song_PhysicsAsset'            → 'Song'
    """
    _, rest = parse_asset_name(name)
    # Strip UE-generated suffixes, then the _anim export suffix
    rest = re.sub(r'_(Skeleton|PhysicsAsset|PhysAsset)$', '', rest, flags=re.IGNORECASE)
    rest = re.sub(r'_anim$', '', rest, flags=re.IGNORECASE)
    # Strip common asset-type prefixes
    rest = re.sub(r'^(SK|SKEL|SKM|PA|SM)_', '', rest, flags=re.IGNORECASE)
    return rest


# ─── ROUTING ─────────────────────────────────────────────────────────────────

def route_asset(name, class_name, project):
    """
    Decide where an asset belongs based on its class and name.
    Returns (destination_folder, reason) — destination is None when the
    asset should be left in staging.
    """
    shot, _ = parse_asset_name(name)

    if class_name in ANIM_CLASSES or class_name in GEOCACHE_CLASSES:
        if shot:
            return f"{PROJECT_ROOT}/{project}/{shot}/Animation", "shot animation"
        return f"{PROJECT_ROOT}/{project}/_Assets", "animation without shot prefix"

    if class_name in CHARACTER_CLASSES:
        character = clean_character_name(name)
        if character:
            return f"{ASSETS_ROOT}/Characters/{character}", "character asset"
        return None, "could not derive character name"

    if class_name in STATIC_CLASSES:
        return f"{ASSETS_ROOT}/Props", "static mesh"

    if shot is None and class_name not in CHARACTER_CLASSES:
        # Unhandled class without a shot prefix — leave for the TA
        return None, f"unhandled class '{class_name}'"

    return None, f"unhandled class '{class_name}'"


# ─── UNREAL HELPERS ──────────────────────────────────────────────────────────

def get_asset_class_name(asset_data):
    """Return the asset's class name as a string (handles UE5.1+ and older APIs)."""
    try:
        return str(asset_data.asset_class_path.asset_name)   # UE 5.1+
    except AttributeError:
        return str(asset_data.asset_class)                   # UE 5.0 / 4.x


def ensure_directory(content_path):
    if not unreal.EditorAssetLibrary.does_directory_exist(content_path):
        unreal.EditorAssetLibrary.make_directory(content_path)
        unreal.log(f"    [DIR] Created: {content_path}")


def ask_project_name(default=""):
    """
    Text-input dialog for when run() is called without a project name.
    Tries tkinter first; falls back to a PowerShell InputBox on Windows.
    Returns empty string if the user cancels.
    """
    prompt = "Enter the project name.\nThis becomes the folder under /Game/Production/."

    # ── Option A: tkinter simpledialog ───────────────────────────────────────
    try:
        import tkinter as tk
        from tkinter import simpledialog
        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", True)
        name = simpledialog.askstring(
            title="Project Name",
            prompt=prompt,
            initialvalue=default,
            parent=root
        )
        root.destroy()
        return name.strip() if name else ""
    except Exception:
        pass

    # ── Option B: PowerShell InputBox (Windows fallback) ─────────────────────
    try:
        import subprocess
        ps = (
            "[System.Reflection.Assembly]::LoadWithPartialName('Microsoft.VisualBasic') | Out-Null; "
            f"[Microsoft.VisualBasic.Interaction]::InputBox('{prompt}', 'Project Name', '{default}')"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True, text=True, timeout=60
        )
        return result.stdout.strip()
    except Exception:
        pass

    return ""


# ─── MAIN ────────────────────────────────────────────────────────────────────

def run(staging_path=None, project_name="", dry_run=None):
    """
    Organize all assets in the staging folder into production folders.
    All parameters optional — designed to be called from an Editor Utility
    Widget, the Python console, or executed directly.

      staging_path  Content Browser path to scan   (default: STAGING_FOLDER)
      project_name  Production folder name (blank → open Unreal project name)
      dry_run       Log the plan without moving     (default: DRY_RUN)
    """
    staging = (staging_path or STAGING_FOLDER).rstrip("/")
    dry     = DRY_RUN if dry_run is None else dry_run

    # ── Validate staging folder ──────────────────────────────────────────────
    if not unreal.EditorAssetLibrary.does_directory_exist(staging):
        unreal.log_error(f"Staging folder does not exist: {staging}")
        return

    # ── Resolve project name ─────────────────────────────────────────────────
    project = resolve_production_project(project_name)
    if not project:
        default = get_open_project_name() or PROJECT_NAME
        project = ask_project_name(default=default)
    if not project:
        unreal.log_warning("No project name provided — aborting.")
        return

    # ── Scan staging ─────────────────────────────────────────────────────────
    object_paths = unreal.EditorAssetLibrary.list_assets(
        staging, recursive=True, include_folder=False
    )

    if not object_paths:
        unreal.log_warning(f"No assets found in: {staging}")
        return

    sep = "=" * 60
    unreal.log(f"\n{sep}")
    unreal.log("Staging Organizer")
    unreal.log(f"Project : {project}")
    unreal.log(f"Staging : {staging}")
    unreal.log(f"Assets  : {len(object_paths)}")
    if dry:
        unreal.log("Mode    : DRY RUN — nothing will be moved")
    unreal.log(sep)

    counts = {"moved": 0, "left": 0, "errors": 0}

    for object_path in sorted(object_paths):
        # '/Game/Staging/Shot01_Song_anim.Shot01_Song_anim' → package path + name
        package_path = str(object_path).split(".")[0]
        asset_name   = package_path.rsplit("/", 1)[-1]

        asset_data = unreal.EditorAssetLibrary.find_asset_data(object_path)
        class_name = get_asset_class_name(asset_data)

        # Skip redirectors left over from previous moves
        if class_name == "ObjectRedirector":
            continue

        destination_folder, reason = route_asset(asset_name, class_name, project)

        unreal.log(f"\n  {asset_name}  [{class_name}]")

        if destination_folder is None:
            unreal.log_warning(f"    → LEFT IN STAGING — {reason}")
            counts["left"] += 1
            continue

        destination_path = f"{destination_folder}/{asset_name}"

        if dry:
            unreal.log(f"    [DRY RUN] Would move → {destination_path}  ({reason})")
            counts["moved"] += 1
            continue

        if unreal.EditorAssetLibrary.does_asset_exist(destination_path):
            unreal.log_warning(f"    → SKIPPED — already exists at {destination_path}")
            counts["left"] += 1
            continue

        try:
            ensure_directory(destination_folder)
            ok = unreal.EditorAssetLibrary.rename_asset(package_path, destination_path)
            if ok:
                unreal.EditorAssetLibrary.save_asset(destination_path)
                unreal.log(f"    ✓ Moved → {destination_path}  ({reason})")
                counts["moved"] += 1
            else:
                unreal.log_error(f"    ✗ Move failed (rename_asset returned False)")
                counts["errors"] += 1
        except Exception as exc:
            unreal.log_error(f"    ✗ Error moving '{asset_name}': {exc}")
            counts["errors"] += 1

    unreal.log(f"\n{sep}")
    unreal.log(
        f"Done — Moved: {counts['moved']}  "
        f"Left in staging: {counts['left']}  "
        f"Errors: {counts['errors']}"
    )
    if not dry and counts["moved"] > 0:
        unreal.log(
            "NOTE: Right-click the Staging folder in the Content Browser and "
            "choose 'Fix Up Redirectors' to finish cleaning it."
        )
    unreal.log(sep + "\n")


if __name__ == '__main__':
    run()

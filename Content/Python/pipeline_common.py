# pipeline_common.py
# Shared helpers for Script 1 and Script 2.

import os
import unreal


def get_open_project_name():
    """Return the open .uproject name (no extension), or '' if unavailable."""
    try:
        path = unreal.Paths.get_project_file_path()
        if path:
            return os.path.splitext(os.path.basename(str(path)))[0]
    except Exception:
        pass
    return ""


PRODUCTION_ROOT = "/Game/Production"


def list_production_projects():
    """Return folder names directly under /Game/Production/."""
    subpaths = unreal.EditorAssetLibrary.list_assets(
        PRODUCTION_ROOT, recursive=False, include_folder=True
    )
    folders = []
    for path in subpaths:
        path = str(path).rstrip("/")
        name = normalize_project_name(path.rsplit("/", 1)[-1])
        if name and "." not in name:
            folders.append(name)
    return sorted(folders)


def get_suggested_production_project(projects=None):
    """Best default project for the widget dropdown (open UE project if listed)."""
    projects = projects if projects is not None else list_production_projects()
    if not projects:
        return ""
    resolved = resolve_production_project("", projects)
    return resolved or projects[0]


def normalize_project_name(name):
    """Strip whitespace and slashes from widget / path-derived project names."""
    return (name or "").strip().strip("/")


def match_production_folder(name, projects):
    """Map a widget value to the exact folder name under /Game/Production/."""
    name = normalize_project_name(name)
    if not name or not projects:
        return ""
    if name in projects:
        return name
    for folder in projects:
        if normalize_project_name(folder) == name:
            return folder
        if folder.lower() == name.lower():
            return folder
    return ""


def resolve_production_project(explicit="", production_folders=None):
    """
    Pick the production folder name to use.

      explicit            value from widget / run() argument
      production_folders  list of folder names under /Game/Production/
                          (Script 2 only — pass None for Script 1)

    Returns the resolved name, or '' when still ambiguous (widget must choose).
    """
    explicit = normalize_project_name(explicit)
    if explicit:
        if production_folders is not None:
            matched = match_production_folder(explicit, production_folders)
            return matched or explicit
        return explicit

    ue_name = get_open_project_name()
    if not ue_name:
        return ""

    if production_folders is None:
        unreal.log(f"Using open Unreal project: {ue_name}")
        return ue_name

    if ue_name in production_folders:
        unreal.log(f"Using open Unreal project: {ue_name}")
        return ue_name

    return ""


def pick_folder(title="Select Maya Export Folder (camera FBX files)"):
    """
    Open a native folder-picker dialog.
    tkinter first, PowerShell WinForms fallback. Returns '' on cancel.
    """
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

    try:
        import subprocess
        ps = (
            "Add-Type -AssemblyName System.Windows.Forms; "
            "$d = New-Object System.Windows.Forms.FolderBrowserDialog; "
            f"$d.Description = '{title}'; "
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


import sys
import types

_SESSION_STATE_MODULE = "anim8_pipeline_session_state"


def _session_state():
    """Persist widget session values across importlib.reload(pipeline_common)."""
    if _SESSION_STATE_MODULE not in sys.modules:
        mod = types.ModuleType(_SESSION_STATE_MODULE)
        mod.last_camera_folder = ""
        sys.modules[_SESSION_STATE_MODULE] = mod
    return sys.modules[_SESSION_STATE_MODULE]


def set_last_camera_folder(path):
    """Store the camera export folder path for the next Script 2 run."""
    _session_state().last_camera_folder = (path or "").strip().replace("\\", "/")


def get_last_camera_folder():
    """Return the last camera folder picked in this editor session."""
    return _session_state().last_camera_folder


def browse_camera_folder():
    """
    Open the folder picker and remember the result for Script 2.
    Returns the selected path, or '' if cancelled.
    """
    path = pick_folder(title="Select Camera Export Folder (Shot##_cam.fbx)")
    if path:
        set_last_camera_folder(path)
        unreal.log(f"Camera export folder set: {path}")
    return path

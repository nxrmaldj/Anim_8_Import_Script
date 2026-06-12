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


def resolve_production_project(explicit="", production_folders=None):
    """
    Pick the production folder name to use.

      explicit            value from widget / run() argument
      production_folders  list of folder names under /Game/Production/
                          (Script 2 only — pass None for Script 1)

    Returns the resolved name, or '' when a dialog/picker is still needed.
    """
    explicit = (explicit or "").strip()
    if explicit:
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

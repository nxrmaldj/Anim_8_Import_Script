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


def pick_production_project_dialog(projects, title="Select Production Project"):
    """
    Pick one folder name from /Game/Production/ when multiple exist.
    Returns the chosen name, or '' on cancel.
    """
    projects = sorted(projects)
    if not projects:
        return ""
    if len(projects) == 1:
        return projects[0]

    try:
        import tkinter as tk
        from tkinter import messagebox

        result = {"project": ""}

        root = tk.Tk()
        root.title(title)
        root.wm_attributes("-topmost", True)
        root.geometry("360x320")
        root.minsize(320, 260)

        tk.Label(
            root,
            text="Multiple projects under /Game/Production/.\nSelect which one to use:",
            justify=tk.LEFT,
        ).pack(pady=(10, 6), padx=12, anchor="w")

        listbox = tk.Listbox(root, height=min(len(projects), 12), exportselection=False)
        listbox.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 8))
        for name in projects:
            listbox.insert(tk.END, name)
        listbox.selection_set(0)
        listbox.activate(0)

        def confirm():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning(
                    title="No selection",
                    message="Select a production project.",
                    parent=root,
                )
                return
            result["project"] = projects[selection[0]]
            root.destroy()

        def cancel():
            result["project"] = ""
            root.destroy()

        btn_row = tk.Frame(root)
        btn_row.pack(pady=(0, 10))
        tk.Button(btn_row, text="Use Selected", command=confirm, width=14).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_row, text="Cancel", command=cancel, width=10).pack(side=tk.LEFT, padx=4)

        listbox.bind("<Double-Button-1>", lambda _e: confirm())
        root.protocol("WM_DELETE_WINDOW", cancel)
        root.mainloop()
        return result["project"]
    except Exception:
        pass

    return ""


def resolve_production_project_choice(explicit="", production_folders=None, interactive=False):
    """
    Resolve which /Game/Production/ project to use.

      explicit              widget value or run() argument (preferred)
      production_folders    folder names from list_production_projects()
      interactive           when True and explicit is blank with multiple projects,
                            open a picker dialog instead of guessing
    """
    folders = production_folders if production_folders is not None else list_production_projects()
    if not folders:
        return ""

    explicit = normalize_project_name(explicit)
    if explicit:
        matched = match_production_folder(explicit, folders)
        return matched or (explicit if explicit in folders else explicit)

    if len(folders) == 1:
        return folders[0]

    if interactive:
        picked = pick_production_project_dialog(folders)
        if picked:
            unreal.log(f"Selected production project: {picked}")
        return picked

    return resolve_production_project("", folders)


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

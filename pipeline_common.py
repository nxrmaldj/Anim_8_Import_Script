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

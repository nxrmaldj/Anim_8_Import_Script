#!/usr/bin/env python3
"""
Install Anim8 Pipeline into an Unreal Engine project.

Double-click install_plugin.bat (Windows) or run:
  python install_plugin.py

You will be asked to pick either:
  - Your Unreal project folder (contains a .uproject file), or
  - Your project's Plugins folder

Files are copied to:  <project>/Plugins/Anim8Pipeline/
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

PLUGIN_NAME = "Anim8Pipeline"
REPO_ROOT = Path(__file__).resolve().parent
UPLUGIN_FILE = REPO_ROOT / f"{PLUGIN_NAME}.uplugin"
PYTHON_SOURCE_DIR = REPO_ROOT / "Content" / "Python"
EDITOR_UTILITIES_DIR = REPO_ROOT / "Content" / "EditorUtilities"
RESOURCES_DIR = REPO_ROOT / "Resources"
CONFIG_DIR = REPO_ROOT / "Config"
ICON_FILE = RESOURCES_DIR / "Icon128.png"


def pick_folder(title: str) -> Path | None:
    """Native folder picker. Returns None if cancelled."""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", True)
        folder = filedialog.askdirectory(title=title, parent=root)
        root.destroy()
        if folder:
            return Path(folder)
    except Exception:
        pass

    # Fallback: type path in terminal
    print(title)
    typed = input("Paste folder path (or press Enter to cancel): ").strip().strip('"')
    if typed:
        return Path(typed)
    return None


def find_uproject(folder: Path) -> Path | None:
    matches = list(folder.glob("*.uproject"))
    return matches[0] if matches else None


def resolve_install_dest(chosen: Path) -> Path:
    """
    Turn the user's folder pick into Plugins/Anim8Pipeline.

    Accepts:
      - Project root (has .uproject)
      - Plugins folder
      - Existing Anim8Pipeline folder (reinstall)
    """
    chosen = chosen.resolve()

    if chosen.name == PLUGIN_NAME and chosen.parent.name == "Plugins":
        return chosen

    if chosen.name == "Plugins":
        return chosen / PLUGIN_NAME

    if find_uproject(chosen):
        return chosen / "Plugins" / PLUGIN_NAME

    if (chosen / "Plugins").is_dir() and find_uproject(chosen):
        return chosen / "Plugins" / PLUGIN_NAME

    if chosen.parent.name == "Plugins" and find_uproject(chosen.parent.parent):
        return chosen.parent / PLUGIN_NAME

    raise ValueError(
        f"Could not find a .uproject in:\n  {chosen}\n\n"
        "Pick your Unreal project folder (the one with the .uproject file),\n"
        "or pick the project's Plugins folder."
    )


def copy_plugin(dest: Path) -> None:
    if not UPLUGIN_FILE.is_file():
        raise FileNotFoundError(f"Missing plugin file: {UPLUGIN_FILE}")
    if not PYTHON_SOURCE_DIR.is_dir():
        raise FileNotFoundError(f"Missing Python folder: {PYTHON_SOURCE_DIR}")

    py_files = sorted(PYTHON_SOURCE_DIR.glob("*.py"))
    if not py_files:
        raise FileNotFoundError(f"No Python files in {PYTHON_SOURCE_DIR}")

    dest.mkdir(parents=True, exist_ok=True)
    python_dest = dest / "Content" / "Python"
    python_dest.mkdir(parents=True, exist_ok=True)

    shutil.copy2(UPLUGIN_FILE, dest / UPLUGIN_FILE.name)
    for src in py_files:
        shutil.copy2(src, python_dest / src.name)

    if EDITOR_UTILITIES_DIR.is_dir():
        util_dest = dest / "Content" / "EditorUtilities"
        util_dest.mkdir(parents=True, exist_ok=True)
        copied_widget = False
        for src in EDITOR_UTILITIES_DIR.iterdir():
            if src.suffix.lower() == ".uasset":
                shutil.copy2(src, util_dest / src.name)
                copied_widget = True
        if copied_widget:
            print("  + Editor Utility Widget copied")

    if ICON_FILE.is_file():
        resources_dest = dest / "Resources"
        resources_dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ICON_FILE, resources_dest / ICON_FILE.name)
        print("  + Plugin icon copied")

    if CONFIG_DIR.is_dir():
        config_dest = dest / "Config"
        config_dest.mkdir(parents=True, exist_ok=True)
        copied_config = False
        for src in CONFIG_DIR.iterdir():
            if src.is_file() and src.suffix.lower() == ".ini":
                shutil.copy2(src, config_dest / src.name)
                copied_config = True
        if copied_config:
            print("  + Plugin config copied (Social Media filmback preset)")


def main() -> int:
    print("=" * 60)
    print("Anim8 Pipeline — Plugin Installer")
    print("=" * 60)
    print()
    print(f"Source: {REPO_ROOT}")
    print()

    chosen = pick_folder(
        "Select Unreal project folder (.uproject) OR Plugins folder"
    )
    if not chosen:
        print("Cancelled — nothing was installed.")
        return 1

    try:
        dest = resolve_install_dest(chosen)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1

    print(f"Install to: {dest}")
    print()

    if dest.exists() and any(dest.iterdir()):
        answer = input("Folder already exists. Overwrite files? [y/N]: ").strip().lower()
        if answer not in ("y", "yes"):
            print("Cancelled — existing install left unchanged.")
            return 1

    try:
        copy_plugin(dest)
    except (FileNotFoundError, OSError) as exc:
        print(f"Install failed: {exc}")
        return 1

    project_root = dest.parent.parent if dest.parent.name == "Plugins" else dest.parent

    print()
    print("Done — plugin installed.")
    print()
    print("Next steps:")
    print("  1. Open the project in Unreal Editor")
    print("  2. Edit → Plugins → enable Python Editor Script Plugin + Anim8 Pipeline")
    print("  3. Enable Editor Scripting Utilities (for the widget Refresh / List Assets)")
    print("  4. Restart the editor")
    print()
    if find_uproject(project_root):
        print(f"  Project: {find_uproject(project_root).name}")
    print(f"  Plugin:  {dest}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

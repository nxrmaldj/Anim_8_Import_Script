# anim8_launcher.py
# Opens the packaged Editor Utility Widget (if present in plugin Content).

import unreal

EDITOR_UTILITIES_ROOT = "/Anim8Pipeline/EditorUtilities"

WIDGET_PATH = "/Anim8Pipeline/EditorUtilities/EUW_Anim8Pipeline"


def find_widget_path():
    """Return the packaged EUW widget path, or None if missing."""
    if unreal.EditorAssetLibrary.does_asset_exist(WIDGET_PATH):
        return WIDGET_PATH
    return None


def open_widget():
    """Open the Anim8 pipeline Editor Utility Widget tab."""
    widget_path = find_widget_path()
    if not widget_path:
        unreal.log_error(
            f"Anim8 widget not found at {WIDGET_PATH}. "
            "See WIDGET_PACKAGE.md"
        )
        return

    asset = unreal.EditorAssetLibrary.load_asset(widget_path)
    subsystem = unreal.get_editor_subsystem(unreal.EditorUtilitySubsystem)
    subsystem.spawn_and_register_tab(asset)
    unreal.log(f"Anim8 Pipeline widget opened: {widget_path}")


def register_tools_menu():
    """Add Tools → Anim8 Pipeline if the main widget asset exists."""
    if not find_widget_path():
        return

    try:
        tool_menus = unreal.ToolMenus.get()
        menu = tool_menus.extend_menu("LevelEditor.MainMenu.Tools")
        entry = unreal.ToolMenuEntry()
        entry.set_editor_property("name", "Anim8Pipeline.OpenWidget")
        entry.set_editor_property("type", unreal.MultiBlockType.MENU_ENTRY)
        entry.set_label("Anim8 Pipeline")
        entry.set_tool_tip("Open the Anim8 staging + sequence builder widget")
        entry.set_string_command(
            unreal.ToolMenuStringCommandType.PYTHON,
            unreal.Name(""),
            "import anim8_launcher; anim8_launcher.open_widget()",
        )
        menu.add_menu_entry("Anim8Pipeline", entry)
        tool_menus.refresh_all_widgets()
    except Exception as exc:
        unreal.log_warning(f"Anim8 Tools menu not registered: {exc}")

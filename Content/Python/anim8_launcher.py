# anim8_launcher.py
# Opens the packaged Editor Utility Widget (if present in plugin Content).

import unreal

EDITOR_UTILITIES_ROOT = "/Anim8Pipeline/EditorUtilities"

# Preferred names — first match wins. Use version suffix when mixing UE generations.
WIDGET_CANDIDATES = (
    "/Anim8Pipeline/EditorUtilities/EUW_Anim8Pipeline5_5",
    "/Anim8Pipeline/EditorUtilities/EUW_Anim8Pipeline",
)


def find_widget_path():
    """Return the first existing EUW widget path under the plugin, or None."""
    for path in WIDGET_CANDIDATES:
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            return path

    if not unreal.EditorAssetLibrary.does_directory_exist(EDITOR_UTILITIES_ROOT):
        return None

    for path in sorted(unreal.EditorAssetLibrary.list_assets(EDITOR_UTILITIES_ROOT, recursive=False)):
        asset_name = str(path).rstrip("/").rsplit("/", 1)[-1]
        if asset_name.startswith("EUW_"):
            return str(path).rstrip("/")

    return None


def open_widget():
    """Open the Anim8 pipeline Editor Utility Widget tab."""
    widget_path = find_widget_path()
    if not widget_path:
        unreal.log_error(
            f"Anim8 widget not found under {EDITOR_UTILITIES_ROOT}. "
            "Package an Editor Utility Widget there (e.g. EUW_Anim8Pipeline5_5) — see WIDGET_PACKAGE.md"
        )
        return

    asset = unreal.EditorAssetLibrary.load_asset(widget_path)
    subsystem = unreal.get_editor_subsystem(unreal.EditorUtilitySubsystem)
    subsystem.spawn_and_register_tab(asset)
    unreal.log(f"Anim8 Pipeline widget opened: {widget_path}")


def register_tools_menu():
    """Add Tools → Anim8 Pipeline if a widget asset exists."""
    if not find_widget_path():
        return

    try:
        tool_menus = unreal.ToolMenus.get()
        menu = tool_menus.extend_menu("LevelEditor.MainMenu.Tools")
        entry = unreal.ToolMenuEntry(
            name="Anim8Pipeline.OpenWidget",
            type=unreal.MultiBlockType.MENU_ENTRY,
            insert_position=unreal.ToolMenuInsert("", unreal.ToolMenuInsertType.DEFAULT),
        )
        entry.set_label("Anim8 Pipeline")
        entry.set_tool_tip("Open the Anim8 staging + sequence builder widget")
        entry.set_string_command(
            unreal.ToolMenuStringCommand(
                name="Anim8PipelineOpen",
                type=unreal.ToolMenuStringCommandType.PYTHON,
                python_command="import anim8_launcher; anim8_launcher.open_widget()",
            )
        )
        menu.add_menu_entry("Anim8Pipeline", entry)
        tool_menus.refresh_all_widgets()
    except Exception as exc:
        unreal.log_warning(f"Anim8 Tools menu not registered: {exc}")

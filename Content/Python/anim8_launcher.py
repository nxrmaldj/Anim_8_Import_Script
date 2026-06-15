# anim8_launcher.py
# Opens the packaged Editor Utility Widget (if present in plugin Content).

import unreal

WIDGET_ASSET_PATH = "/Anim8Pipeline/EditorUtilities/EUW_Anim8Pipeline"


def open_widget():
    """Open the Anim8 pipeline Editor Utility Widget tab."""
    if not unreal.EditorAssetLibrary.does_asset_exist(WIDGET_ASSET_PATH):
        unreal.log_error(
            f"Anim8 widget not found at {WIDGET_ASSET_PATH}. "
            "Package EUW_Anim8Pipeline into the plugin — see WIDGET_PACKAGE.md"
        )
        return

    asset = unreal.EditorAssetLibrary.load_asset(WIDGET_ASSET_PATH)
    subsystem = unreal.get_editor_subsystem(unreal.EditorUtilitySubsystem)
    subsystem.spawn_and_register_tab(asset)
    unreal.log("Anim8 Pipeline widget opened.")


def register_tools_menu():
    """Add Tools → Anim8 Pipeline if the widget asset exists."""
    if not unreal.EditorAssetLibrary.does_asset_exist(WIDGET_ASSET_PATH):
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

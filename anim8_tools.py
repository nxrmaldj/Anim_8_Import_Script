# anim8_tools.py
# Blueprint-callable helpers for the Editor Utility Widget.
#
# If nodes do not appear in the Graph search, copy this file + pipeline_common.py
# into your project's Content/Python/ folder and restart the editor.
#
# Or run once per session in the Python console:
#   import sys; sys.path.append("A:/Anim_8_Scripts"); import anim8_tools

import unreal

from pipeline_common import (
    browse_camera_folder,
    get_suggested_production_project,
    list_production_projects,
)


@unreal.uclass()
class Anim8PipelineTools(unreal.BlueprintFunctionLibrary):
    """Anim8 pipeline actions exposed to Editor Utility Widget Blueprints."""

    @unreal.ufunction(static=True, ret=str, category="Anim8 Pipeline", call_in_editor=True)
    def browse_camera_export_folder():
        """Open folder picker for camera FBX exports. Returns path or empty string."""
        return browse_camera_folder()

    @unreal.ufunction(static=True, ret=unreal.Array(str), category="Anim8 Pipeline", call_in_editor=True)
    def get_production_project_names():
        """All production folder names — use on Event Construct to fill the Project combo."""
        names = list_production_projects()
        result = unreal.Array(str)
        for name in names:
            result.append(name)
        return result

    @unreal.ufunction(static=True, ret=str, category="Anim8 Pipeline", call_in_editor=True)
    def get_suggested_production_project():
        """Default project for the combo (matches open .uproject when possible)."""
        return get_suggested_production_project()

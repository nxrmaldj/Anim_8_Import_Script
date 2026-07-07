# anim8_tools.py
# Blueprint-callable helpers for the Editor Utility Widget.
#
# Loaded automatically when the Anim8 Pipeline plugin is enabled (init_unreal.py).

import unreal

from pipeline_common import (
    browse_camera_folder,
    get_suggested_production_project,
    list_production_projects,
)

import script_3_render_queue


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

    @unreal.ufunction(static=True, ret=int, category="Anim8 Pipeline", call_in_editor=True)
    def add_project_shots_to_render_queue(project_name=""):
        """
        Clear Movie Render Queue and add all main shot sequences for the project.
        Wire the widget Project combo to project_name. Open your render level first.
        Returns the number of jobs added, or -1 on failure.
        """
        import importlib
        importlib.reload(script_3_render_queue)
        result = script_3_render_queue.run(
            project_name=project_name,
            dry_run=False,
            interactive=False,
        )
        return result if result is not None else -1

# anim8_tools.py
# Blueprint-callable helpers for the Editor Utility Widget.
#
# First time in a session, run once in the Python console so nodes appear:
#   import sys; sys.path.append("A:/Anim_8_Scripts"); import anim8_tools
#
# Widget: Find Camera Folder button → Browse Camera Export Folder → Set Text

import unreal

from pipeline_common import pick_folder


@unreal.uclass()
class Anim8PipelineTools(unreal.BlueprintFunctionLibrary):
    """Anim8 pipeline actions exposed to Editor Utility Widget Blueprints."""

    @unreal.ufunction(static=True, ret=str, category="Anim8 Pipeline")
    def browse_camera_export_folder():
        """
        Open a folder picker for Maya camera FBX exports.
        Returns the selected path as a string (empty if cancelled).
        Wire Return Value → Set Text on the Camera Folder input.
        """
        path = pick_folder(title="Select Camera Export Folder (Shot##_cam.fbx)")
        if path:
            unreal.log(f"Camera export folder: {path}")
        return path

# anim8_tools.py
# Blueprint-callable helpers for the Editor Utility Widget.
#
# If "Browse Camera Export Folder" does not appear in the Graph search:
#   Use the Execute Python Command on Find Camera Folder (see WIDGET_GUIDE.md Plan B)
#
# To try loading the Blueprint node (once per session):
#   import sys; sys.path.append("A:/Anim_8_Scripts"); import anim8_tools
#
# For the node to appear every editor launch, copy this file + pipeline_common.py
# into your project's Content/Python/ folder.

import unreal

from pipeline_common import browse_camera_folder


@unreal.uclass()
class Anim8PipelineTools(unreal.BlueprintFunctionLibrary):
    """Anim8 pipeline actions exposed to Editor Utility Widget Blueprints."""

    @unreal.ufunction(static=True, ret=str, category="Anim8 Pipeline", call_in_editor=True)
    def browse_camera_export_folder():
        """
        Open a folder picker for Maya camera FBX exports.
        Returns the selected path as a string (empty if cancelled).
        Wire Return Value → Conv String to Text → Set Text (CameraFolderInput).
        """
        return browse_camera_folder()

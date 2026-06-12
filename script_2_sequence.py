# script_2_sequence.py
# Level Sequence Builder — run AFTER script_1_organize.py has routed assets
# into shot folders.
#
# STATUS: not yet implemented. Build spec agreed and documented in
# SCRIPT_2_PLAN.md — read that file for the full design.
#
# Planned run flow:
#   1. Project selector  — list folders under /Game/Production/, user picks one
#   2. Camera picker     — folder dialog for the Maya export folder on disk
#                          (scanned for Shot##_Camera_anim.fbx files)
#   3. Shot discovery    — every Shot## folder under the chosen project
#   4. Per shot:
#        - Create Level Sequence  Shot##_{ProjectName}  in Shot##/
#        - SKIP the shot if a sequence with that name already exists
#        - Add a Skeletal Mesh track per AnimSequence (skeleton looked up
#          from the AnimSequence asset itself — no character dict)
#        - Add a Geometry Cache track per GeometryCache asset
#        - Spawn CineCamera named after the camera FBX (minus _anim)
#        - Add Camera Cut track
#        - Import camera FBX with match_by_name_only = False
#        - No camera FBX found → build without camera track, log warning
#   5. Log summary

# ─── CONFIG ──────────────────────────────────────────────────────────────────

PROJECT_ROOT = "/Game/Production"
ASSETS_ROOT  = "/Game/Assets"

# ─── END CONFIG ──────────────────────────────────────────────────────────────

import unreal


def run(project_name="", camera_folder="", dry_run=False):
    """
    Build Level Sequences for every shot in the chosen project.

      project_name   blank → selection dialog listing /Game/Production/ folders
      camera_folder  blank → folder picker for the Maya export folder
      dry_run        True  → log the full build plan without creating anything
    """
    unreal.log("Script 2 — Level Sequence Builder: not yet implemented. See SCRIPT_2_PLAN.md")


if __name__ == '__main__':
    run()

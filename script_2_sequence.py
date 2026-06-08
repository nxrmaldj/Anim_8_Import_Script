# script_2_sequence.py
# Run AFTER script_1_import.py has finished for the same shot.
# Run via: Unreal Editor > Python Script Runner
# Or: UnrealEditor.exe MyProject.uproject -ExecutePythonScript="C:/Scripts/script_2_sequence.py"

# ─── CONFIG ──────────────────────────────────────────────────────────────────
# Shared with script_1_import.py — keep both in sync.

SOURCE_FOLDER = "C:/Exports/MyProject"
PROJECT_ROOT  = "/Game/Production"
ASSETS_ROOT   = "/Game/Assets"
PROJECT_NAME  = "FindingKiiboh"  # ← change for each project

KNOWN_CHARACTERS = {
    "Kiiboh":               "/Game/Assets/Characters/Kiiboh/SK_Kiiboh",
    "Kiiboh_Damaged":       "/Game/Assets/Characters/Kiiboh/SK_Kiiboh_Damaged",
    "Kiiboh_Leg_Head_Tail": "/Game/Assets/Characters/Kiiboh/SK_Kiiboh_Leg_Head_Tail",
    "Kiiboh_Part_All":      "/Game/Assets/Characters/Kiiboh/SK_Kiiboh_Part_All",
    "Song":                 "/Game/Assets/Characters/Song/SK_Song",
}

ALEMBIC_SCALE = 1.0

# ← Set this before each run
SHOT_NUMBER = "Shot01"

# ─── END CONFIG ──────────────────────────────────────────────────────────────

# TODO: Script 2 — Level Sequence Builder (not yet implemented)
# See UE_Import_Pipeline_Spec.docx for full spec.
#
# What this script will do:
#   1. Read SHOT_NUMBER from config above
#   2. Scan /Game/Production/{PROJECT_NAME}/{SHOT_NUMBER}/Animation/ for imported assets
#   3. Find {SHOT_NUMBER}_Camera_anim.fbx in SOURCE_FOLDER — derive camera actor name
#   4. Create Level Sequence at /Game/Production/{PROJECT_NAME}/{SHOT_NUMBER}/
#   5. Spawn CineCamera Actor named to match the camera FBX
#   6. Add Camera Cut track to the sequence
#   7. Add Skeletal Mesh tracks for each animation asset (via KNOWN_CHARACTERS lookup)
#   8. Add Geometry Cache tracks for each imported ABC asset
#   9. Import the camera FBX directly into the sequence
#  10. Log a summary of all tracks added + any warnings

import unreal

unreal.log("Script 2 — Level Sequence Builder: not yet implemented.")

# test_organize.py
# Standalone tests for the staging organizer's routing logic.
# Runs outside Unreal Engine — no UE install required.
#
# Usage:
#   python test_organize.py

import sys
import os
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Content", "Python"))

# ─── MOCK UNREAL ─────────────────────────────────────────────────────────────

_mock_unreal = types.ModuleType("unreal")
_mock_unreal.log         = lambda msg: None
_mock_unreal.log_warning = lambda msg: None
_mock_unreal.log_error   = lambda msg: None

sys.modules["unreal"] = _mock_unreal

import script_1_organize as org

route = org.route_asset
clean = org.clean_character_name
parse = org.parse_asset_name

P    = "TestProject"
PROD = org.PROJECT_ROOT
A    = org.ASSETS_ROOT

_passed = 0
_failed = 0

def check(label, got, expected):
    global _passed, _failed
    if got == expected:
        print(f"  PASS  {label}")
        _passed += 1
    else:
        print(f"  FAIL  {label}")
        print(f"        expected : {expected}")
        print(f"        got      : {got}")
        _failed += 1

# ─── parse_asset_name ────────────────────────────────────────────────────────

print("\n── parse_asset_name ─────────────────────────────────────────────────────")

check("Shot01_Song_anim → shot extracted",
      parse("Shot01_Song_anim"), ("Shot01", "Song_anim"))

check("Shot11A_Kiiboh_anim → letter-suffix shot",
      parse("Shot11A_Kiiboh_anim"), ("Shot11A", "Kiiboh_anim"))

check("Dumpster_Location → no shot",
      parse("Dumpster_Location"), (None, "Dumpster_Location"))

# ─── clean_character_name ────────────────────────────────────────────────────

print("\n── clean_character_name ─────────────────────────────────────────────────")

check("SK_Song → Song",                       clean("SK_Song"), "Song")
check("Shot01_Song_anim_Skeleton → Song",     clean("Shot01_Song_anim_Skeleton"), "Song")
check("Song_PhysicsAsset → Song",             clean("Song_PhysicsAsset"), "Song")
check("SK_Kiiboh_Damaged → Kiiboh_Damaged",   clean("SK_Kiiboh_Damaged"), "Kiiboh_Damaged")
check("Shot01_Kiiboh_anim → Kiiboh",          clean("Shot01_Kiiboh_anim"), "Kiiboh")

# ─── route_asset ─────────────────────────────────────────────────────────────

print("\n── route_asset ──────────────────────────────────────────────────────────")

# Animations with shot prefix → shot animation folder
check("AnimSequence with shot → Shot01/Animation",
      route("Shot01_Song_anim", "AnimSequence", P),
      (f"{PROD}/{P}/Shot01/Animation", "shot animation"))

check("GeometryCache with shot → Shot02/Animation",
      route("Shot02_Debris_anim", "GeometryCache", P),
      (f"{PROD}/{P}/Shot02/Animation", "shot animation"))

check("Letter-suffix shot → Shot11A/Animation",
      route("Shot11A_Kiiboh_anim", "AnimSequence", P),
      (f"{PROD}/{P}/Shot11A/Animation", "shot animation"))

# Animation with no shot prefix → _Assets
check("AnimSequence without shot → _Assets",
      route("Idle_Loop_anim", "AnimSequence", P),
      (f"{PROD}/{P}/_Assets", "animation without shot prefix"))

# Character assets → Characters/{Name}
check("SkeletalMesh SK_Song → Characters/Song",
      route("SK_Song", "SkeletalMesh", P),
      (f"{A}/Characters/Song", "character asset"))

check("Skeleton from anim import → Characters/Song",
      route("Shot01_Song_anim_Skeleton", "Skeleton", P),
      (f"{A}/Characters/Song", "character asset"))

check("PhysicsAsset → Characters/Kiiboh",
      route("Kiiboh_PhysicsAsset", "PhysicsAsset", P),
      (f"{A}/Characters/Kiiboh", "character asset"))

# Static meshes → Props
check("StaticMesh → Props",
      route("Shot03_Crane_anim", "StaticMesh", P),
      (f"{A}/Props", "static mesh"))

check("StaticMesh no shot → Props",
      route("Dumpster_Location", "StaticMesh", P),
      (f"{A}/Props", "static mesh"))

# Unhandled classes → left in staging
dest, reason = route("M_Song_Body", "Material", P)
check("Material → left in staging", dest, None)

dest, reason = route("T_Song_Diffuse", "Texture2D", P)
check("Texture2D → left in staging", dest, None)

# ─── SUMMARY ─────────────────────────────────────────────────────────────────

sep = "─" * 60
print(f"\n{sep}")
print(f"Results: {_passed} passed, {_failed} failed")
print(sep)

sys.exit(0 if _failed == 0 else 1)

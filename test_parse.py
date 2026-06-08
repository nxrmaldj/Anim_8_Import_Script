# test_parse.py
# Standalone tests for parse_filename() and destination_for().
# Runs outside Unreal Engine — no UE install required.
#
# Usage:
#   python test_parse.py           (any standard Python 3 install)
#   blender --background --python test_parse.py
#
# All tests print PASS or FAIL. Exit code 0 = all passed, 1 = failures found.

import sys
import types

# ─── MOCK UNREAL ─────────────────────────────────────────────────────────────
# Provide a minimal fake 'unreal' module so script_1_import.py can be imported
# without Unreal Engine being present. Only the symbols used by parse_filename
# and destination_for need to exist.

_mock_unreal = types.ModuleType("unreal")
_mock_unreal.log         = lambda msg: None
_mock_unreal.log_warning = lambda msg: None
_mock_unreal.log_error   = lambda msg: None

sys.modules["unreal"] = _mock_unreal

# ─── IMPORT THE SCRIPT ───────────────────────────────────────────────────────
# __name__ guard in script_1_import.py prevents run() from firing here.

import script_1_import as s1

parse       = s1.parse_filename
destination = s1.destination_for
P           = s1.PROJECT_NAME   # "FindingKiiboh"
PROD        = s1.PROJECT_ROOT   # "/Game/Production"
ASSETS      = s1.ASSETS_ROOT    # "/Game/Assets"

# ─── TEST RUNNER ─────────────────────────────────────────────────────────────

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

# ─── parse_filename TESTS ────────────────────────────────────────────────────

print("\n── parse_filename ───────────────────────────────────────────────────────")

# Camera — must be SKIPPED (kind = 'camera')
r = parse("Shot01_Camera_anim.fbx")
check("Shot01_Camera_anim.fbx → camera",
      (r["kind"], r["shot"], r["token"]),
      ("camera", "Shot01", "Camera"))

# Standard character animation
r = parse("Shot01_Kiiboh_anim.fbx")
check("Shot01_Kiiboh_anim.fbx → anim Kiiboh",
      (r["kind"], r["shot"], r["token"], r["sk_path"]),
      ("anim", "Shot01", "Kiiboh", "/Game/Assets/Characters/Kiiboh/SK_Kiiboh"))

# Multi-token character name — must NOT match the shorter 'Kiiboh' key
r = parse("Shot03_Kiiboh_Damaged_anim.fbx")
check("Shot03_Kiiboh_Damaged_anim.fbx → anim Kiiboh_Damaged",
      (r["kind"], r["shot"], r["token"]),
      ("anim", "Shot03", "Kiiboh_Damaged"))

r = parse("Shot03_Kiiboh_Leg_Head_Tail_anim.fbx")
check("Shot03_Kiiboh_Leg_Head_Tail_anim.fbx → anim Kiiboh_Leg_Head_Tail",
      (r["kind"], r["shot"], r["token"]),
      ("anim", "Shot03", "Kiiboh_Leg_Head_Tail"))

r = parse("Shot03_Kiiboh_Part_All_anim.fbx")
check("Shot03_Kiiboh_Part_All_anim.fbx → anim Kiiboh_Part_All",
      (r["kind"], r["shot"], r["token"]),
      ("anim", "Shot03", "Kiiboh_Part_All"))

r = parse("Shot02_Song_anim.fbx")
check("Shot02_Song_anim.fbx → anim Song",
      (r["kind"], r["shot"], r["token"]),
      ("anim", "Shot02", "Song"))

# Alembic geo cache
r = parse("Shot01_Debris_anim.abc")
check("Shot01_Debris_anim.abc → alembic",
      (r["kind"], r["shot"], r["token"]),
      ("alembic", "Shot01", "Debris"))

r = parse("Shot01_Car_anim.abc")
check("Shot01_Car_anim.abc → alembic",
      (r["kind"], r["shot"]),
      ("alembic", "Shot01"))

# Static mesh fallback — FBX that is not a known character
r = parse("Shot01_Skateboard_anim.fbx")
check("Shot01_Skateboard_anim.fbx → static",
      (r["kind"], r["shot"], r["token"]),
      ("static", "Shot01", "Skateboard"))

r = parse("Shot03_Crane_anim.fbx")
check("Shot03_Crane_anim.fbx → static",
      (r["kind"], r["shot"]),
      ("static", "Shot03"))

# Shared asset — no Shot## prefix
r = parse("Dumpster_Location.abc")
check("Dumpster_Location.abc → shared (no shot)",
      (r["kind"], r["shot"]),
      ("shared", None))

r = parse("Environment_Prop.fbx")
check("Environment_Prop.fbx → shared (no shot)",
      (r["kind"], r["shot"]),
      ("shared", None))

# Shot number with letter suffix
r = parse("Shot11A_Kiiboh_anim.fbx")
check("Shot11A_Kiiboh_anim.fbx → shot='Shot11A'",
      (r["kind"], r["shot"]),
      ("anim", "Shot11A"))

# Case insensitivity — _ANIM suffix in uppercase
r = parse("Shot01_Kiiboh_ANIM.fbx")
check("Shot01_Kiiboh_ANIM.fbx → case-insensitive _anim strip",
      (r["kind"], r["shot"], r["token"]),
      ("anim", "Shot01", "Kiiboh"))

# ─── destination_for TESTS ───────────────────────────────────────────────────

print("\n── destination_for ──────────────────────────────────────────────────────")

check("anim → Production/Shot folder",
      destination("anim", "Shot01"),
      f"{PROD}/{P}/Shot01/Animation")

check("alembic → Production/Shot folder",
      destination("alembic", "Shot03"),
      f"{PROD}/{P}/Shot03/Animation")

check("static → Assets/Props",
      destination("static", "Shot01"),
      f"{ASSETS}/Props")

check("shared → Production/_Assets",
      destination("shared", None),
      f"{PROD}/{P}/_Assets")

# ─── SUMMARY ─────────────────────────────────────────────────────────────────

sep = "─" * 60
print(f"\n{sep}")
print(f"Results: {_passed} passed, {_failed} failed")
print(sep)

sys.exit(0 if _failed == 0 else 1)

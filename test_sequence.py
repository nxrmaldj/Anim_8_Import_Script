# test_sequence.py
# Standalone tests for Script 2's pure logic (shot detection, camera
# matching, sequence naming). Runs outside Unreal — no UE install needed.
#
# Usage:
#   python test_sequence.py

import sys
import types

# ─── MOCK UNREAL ─────────────────────────────────────────────────────────────

_mock_unreal = types.ModuleType("unreal")
_mock_unreal.log         = lambda msg: None
_mock_unreal.log_warning = lambda msg: None
_mock_unreal.log_error   = lambda msg: None

sys.modules["unreal"] = _mock_unreal

import script_2_sequence as s2

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

# ─── is_shot_folder ──────────────────────────────────────────────────────────

print("\n── is_shot_folder ───────────────────────────────────────────────────────")

check("Shot01 → True",        s2.is_shot_folder("Shot01"), True)
check("Shot11A → True",       s2.is_shot_folder("Shot11A"), True)
check("shot03 → True (case)", s2.is_shot_folder("shot03"), True)
check("_Assets → False",      s2.is_shot_folder("_Assets"), False)
check("Animation → False",    s2.is_shot_folder("Animation"), False)
check("Shot → False",         s2.is_shot_folder("Shot"), False)

# ─── camera_name_for ─────────────────────────────────────────────────────────

print("\n── camera_name_for ──────────────────────────────────────────────────────")

check("Shot01_Camera_anim.fbx → Shot01_Camera",
      s2.camera_name_for("Shot01_Camera_anim.fbx"), "Shot01_Camera")

check("Shot11A_Camera_ANIM.fbx → Shot11A_Camera (case)",
      s2.camera_name_for("Shot11A_Camera_ANIM.fbx"), "Shot11A_Camera")

check("Shot01_cam.fbx → Shot01_cam",
      s2.camera_name_for("Shot01_cam.fbx"), "Shot01_cam")

# ─── find_camera_fbx ─────────────────────────────────────────────────────────

print("\n── find_camera_fbx ──────────────────────────────────────────────────────")

# Production naming: Shot##_cam.fbx
files = ["Shot01_cam.fbx", "Shot02_cam.fbx", "Shot11A_cam.fbx"]

check("Shot01 matches Shot01_cam.fbx",
      s2.find_camera_fbx("Shot01", files), "Shot01_cam.fbx")

check("Shot11A matches letter-suffix camera",
      s2.find_camera_fbx("Shot11A", files), "Shot11A_cam.fbx")

check("shot02 case-insensitive match",
      s2.find_camera_fbx("shot02", files), "Shot02_cam.fbx")

check("Shot99 has no camera → None",
      s2.find_camera_fbx("Shot99", files), None)

check("empty file list → None",
      s2.find_camera_fbx("Shot01", []), None)

# Legacy naming still works
legacy = ["Shot01_Camera_anim.fbx"]
check("legacy Shot01_Camera_anim.fbx still matches",
      s2.find_camera_fbx("Shot01", legacy), "Shot01_Camera_anim.fbx")

# ─── camera FBX filename regex (used at scan time) ──────────────────────────

print("\n── camera filename regex ────────────────────────────────────────────────")

check("Shot01_cam.fbx matches",
      bool(s2._CAMERA_FBX_RE.match("Shot01_cam.fbx")), True)

check("Shot01_CAM.fbx matches (case)",
      bool(s2._CAMERA_FBX_RE.match("Shot01_CAM.fbx")), True)

check("Shot01_Camera_anim.fbx matches (legacy)",
      bool(s2._CAMERA_FBX_RE.match("Shot01_Camera_anim.fbx")), True)

check("Shot01_cam_anim.fbx matches",
      bool(s2._CAMERA_FBX_RE.match("Shot01_cam_anim.fbx")), True)

check("Shot01_Kiiboh_anim.fbx does not match",
      bool(s2._CAMERA_FBX_RE.match("Shot01_Kiiboh_anim.fbx")), False)

check("Shot01_cam_v2.fbx does not match (extra suffix)",
      bool(s2._CAMERA_FBX_RE.match("Shot01_cam_v2.fbx")), False)

# ─── sequence_name_for ───────────────────────────────────────────────────────

print("\n── sequence_name_for ────────────────────────────────────────────────────")

check("Shot01 + MyProject → Shot01_MyProject",
      s2.sequence_name_for("Shot01", "MyProject"), "Shot01_MyProject")

resolve = s2.resolve_shots

# ─── resolve_shots ───────────────────────────────────────────────────────────

print("\n── resolve_shots ────────────────────────────────────────────────────────")

all_shots = ["Shot01", "Shot02", "Shot03", "Shot11A"]

check("blank filter → all shots",
      resolve(all_shots), all_shots)

check("single shot filter",
      resolve(all_shots, shot_filter="Shot02"), ["Shot02"])

check("comma-separated filter",
      resolve(all_shots, shot_filter="Shot01,Shot11A"), ["Shot01", "Shot11A"])

check("case-insensitive filter",
      resolve(all_shots, shot_filter="shot03"), ["Shot03"])

check("no match → empty",
      resolve(all_shots, shot_filter="Shot99"), [])

# ─── SUMMARY ─────────────────────────────────────────────────────────────────

sep = "─" * 60
print(f"\n{sep}")
print(f"Results: {_passed} passed, {_failed} failed")
print(sep)

sys.exit(0 if _failed == 0 else 1)

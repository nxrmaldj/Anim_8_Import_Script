# test_sequence.py
# Standalone tests for Script 2's pure logic (shot detection, camera
# matching, sequence naming). Runs outside Unreal — no UE install needed.
#
# Usage:
#   python test_sequence.py

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

check("Shot01_Camera_anim.fbx → Shot01_cam",
      s2.camera_name_for("Shot01_Camera_anim.fbx"), "Shot01_cam")

check("Shot11A_Camera_ANIM.fbx → Shot11A_cam (case)",
      s2.camera_name_for("Shot11A_Camera_ANIM.fbx"), "Shot11A_cam")

check("Shot01_cam.fbx → Shot01_cam",
      s2.camera_name_for("Shot01_cam.fbx"), "Shot01_cam")

check("shot arg overrides filename → Shot03_cam",
      s2.camera_name_for("Shot03_Camera_anim.fbx", shot="Shot03"), "Shot03_cam")

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

check("MyProject → MyProject_Master",
      s2.master_sequence_name_for("MyProject"), "MyProject_Master")

check("Shot01 + MyProject → Shot01_MyProject_Lighting",
      s2.lighting_sequence_name_for("Shot01", "MyProject"), "Shot01_MyProject_Lighting")

# ─── main shot sequence discovery ────────────────────────────────────────────

print("\n── main shot sequence discovery ─────────────────────────────────────────")

check("Shot32_Lighting is lighting",
      s2.is_lighting_sequence_name("Shot32_CoffeeMonster_Fight_Lighting"), True)

check("Shot32 is not lighting",
      s2.is_lighting_sequence_name("Shot32"), False)

check("prefers Shot32_Project over legacy Shot32",
      s2.pick_main_shot_sequence_name(
          ["Shot32", "Shot32_CoffeeMonster_Fight", "Shot32_CoffeeMonster_Fight_Lighting"],
          "Shot32", "CoffeeMonster_Fight"),
      "Shot32_CoffeeMonster_Fight")

check("legacy Shot32 when no project suffix exists",
      s2.pick_main_shot_sequence_name(
          ["Shot32", "Shot32_Lighting"],
          "Shot32", "CoffeeMonster_Fight"),
      "Shot32")

check("ignores lighting only",
      s2.pick_main_shot_sequence_name(["Shot32_Lighting"], "Shot32", "CoffeeMonster_Fight"),
      None)

# ─── sort_shot_names ─────────────────────────────────────────────────────────

print("\n── sort_shot_names ──────────────────────────────────────────────────────")

check("natural shot order",
      s2.sort_shot_names(["Shot11A", "Shot02", "Shot10", "Shot01", "Shot11"]),
      ["Shot01", "Shot02", "Shot10", "Shot11", "Shot11A"])

# ─── frame timing ────────────────────────────────────────────────────────────

print("\n── frame timing ─────────────────────────────────────────────────────────")

check("120f content + preroll → 121 total",
      s2.compute_total_shot_frames(120, has_anim_or_cache=True), 121)

check("120f content, no anim → 120 total",
      s2.compute_total_shot_frames(120, has_anim_or_cache=False), 120)

check("0f content → minimum 1",
      s2.compute_total_shot_frames(0, has_anim_or_cache=False), 1)

check("camera cut always starts frame 0",
      s2.camera_cut_start_frame(), 0)

check("camera binding sections start frame 1 when shot has anims/caches",
      s2.camera_transform_start_frame(has_anim_or_cache=True, content_frames=120), 1)

check("camera binding sections start frame 0 when camera-only",
      s2.camera_transform_start_frame(has_anim_or_cache=False, content_frames=120), 0)

check("Social Media filmback size",
      s2.social_media_filmback_settings(), (13.365, 23.76))

check("Social Media filmback preset name",
      s2.SOCIAL_MEDIA_FILMBACK_PRESET, "Social Media")

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

# ─── camera folder memory (survives pipeline_common reload) ───────────────────

print("\n── camera folder session memory ─────────────────────────────────────────")

import importlib
import pipeline_common as pc

pc.set_last_camera_folder("G:/Export")
importlib.reload(pc)
check("camera folder survives importlib.reload",
      pc.get_last_camera_folder(), "G:/Export")

# ─── SUMMARY ─────────────────────────────────────────────────────────────────

sep = "─" * 60
print(f"\n{sep}")
print(f"Results: {_passed} passed, {_failed} failed")
print(sep)

sys.exit(0 if _failed == 0 else 1)

# script_2_sequence.py
# Level Sequence Builder — run AFTER script_1_organize.py has routed assets
# into shot folders. Full design: SCRIPT_2_PLAN.md
#
# From the Unreal Python console (plugin enabled):
#   import script_2_sequence
#   script_2_sequence.run(dry_run=True)                      # full plan, builds nothing
#   script_2_sequence.run(shot_filter="Shot01", dry_run=False)  # build one shot only
#   script_2_sequence.run(dry_run=False)                     # build everything

# ─── CONFIG ──────────────────────────────────────────────────────────────────

PROJECT_ROOT = "/Game/Production"
ASSETS_ROOT  = "/Game/Assets"

# Sequence display rate (frames per second) used when creating new sequences
SEQUENCE_FPS = 24

# Extra frame at the start of each shot so lighting can load before render.
PREROLL_FRAMES = 1

# ─── END CONFIG ──────────────────────────────────────────────────────────────

import os
import re
import importlib
import unreal

import pipeline_common
importlib.reload(pipeline_common)
from pipeline_common import (
    get_open_project_name,
    resolve_production_project,
    get_last_camera_folder,
    list_production_projects,
)

_SHOT_RE = re.compile(r'^Shot\d+[A-Za-z]?$', re.IGNORECASE)

# Camera FBX filename patterns, e.g. Shot01_cam.fbx or Shot01_Camera_anim.fbx
_CAMERA_FBX_RE = re.compile(
    r'^(Shot\d+[A-Za-z]?)_(cam|camera)(_anim)?\.fbx$', re.IGNORECASE
)


# ─── PURE HELPERS (testable outside UE) ─────────────────────────────────────

def is_shot_folder(name):
    """True when a folder name looks like Shot01 / Shot11A."""
    return bool(_SHOT_RE.match(name))


def camera_name_for(camera_fbx_filename):
    """'Shot01_Camera_anim.fbx' → 'Shot01_Camera' (the CineCamera actor name)."""
    base = os.path.splitext(camera_fbx_filename)[0]
    return re.sub(r'_anim$', '', base, flags=re.IGNORECASE)


def find_camera_fbx(shot, camera_files):
    """
    Find the camera FBX filename for a shot in a list of filenames.
    Accepts Shot##_cam.fbx, Shot##_Camera_anim.fbx and similar variants.
    Matching is case-insensitive. Returns None when the shot has no camera.
    """
    for filename in camera_files:
        match = _CAMERA_FBX_RE.match(filename)
        if match and match.group(1).lower() == shot.lower():
            return filename
    return None


def sequence_name_for(shot, project):
    """'Shot01', 'MyProject' → 'Shot01_MyProject'."""
    return f"{shot}_{project}"


def master_sequence_name_for(project):
    """'MyProject' → 'MyProject_Master'."""
    return f"{project}_Master"


def lighting_sequence_name_for(shot, project):
    """'Shot01', 'MyProject' → 'Shot01_MyProject_Lighting'."""
    return f"{shot}_{project}_Lighting"


def is_lighting_sequence_name(name):
    """True for main or legacy lighting Level Sequence names."""
    return bool(re.search(r"_Lighting$", name or "", re.IGNORECASE))


def pick_main_shot_sequence_name(candidates, shot, project):
    """
    Choose the main shot Level Sequence name from asset names in a shot folder.

    Priority:
      1. Shot##_Project          (current convention)
      2. Shot##                  (legacy)
      3. Shot##_Something        (legacy variant, not lighting)
    Returns None when no suitable candidate exists.
    """
    canonical = sequence_name_for(shot, project)
    scored = []

    for name in candidates:
        if is_lighting_sequence_name(name):
            continue
        if name == master_sequence_name_for(project):
            continue

        if name == canonical:
            scored.append((0, name))
        elif name.lower() == shot.lower():
            scored.append((1, name))
        elif name.lower().startswith(f"{shot.lower()}_"):
            scored.append((2, name))

    if not scored:
        return None

    scored.sort(key=lambda item: (item[0], item[1].lower()))
    return scored[0][1]


def shot_sort_key(name):
    """Natural sort key for Shot01, Shot02, Shot11A, etc."""
    match = re.match(r'^Shot(\d+)([A-Za-z]?)$', name, re.IGNORECASE)
    if not match:
        return (999999, "Z", name.lower())
    return (int(match.group(1)), match.group(2).upper(), name.lower())


def sort_shot_names(shots):
    """Return shot folder names in production order (Shot01, Shot02, Shot11A, …)."""
    return sorted(shots, key=shot_sort_key)


def compute_total_shot_frames(content_frames, has_anim_or_cache=False):
    """
    Parent shot + lighting LS length.

    When anims or geo caches exist, add PREROLL_FRAMES (frame 0 hold for lighting load).
    Camera-only shots keep the raw content length with no preroll.
    """
    content = max(int(content_frames), 0)
    if has_anim_or_cache and content > 0:
        return content + PREROLL_FRAMES
    return max(content, 1)


def camera_start_frame(has_anim_or_cache=False, content_frames=0):
    """Camera Cut track always starts at frame 0."""
    return 0


# ─── DIALOGS ─────────────────────────────────────────────────────────────────

def pick_build_options_dialog(available_shots, project="", title="Select Shots to Build"):
    """
    Checkbox dialog for shots plus optional master / lighting builds.
    Returns dict {shots, build_master, build_lighting} or None on cancel.
    """
    if not available_shots and not project:
        return None

    try:
        import tkinter as tk
        from tkinter import messagebox

        result = {"options": None}

        root = tk.Tk()
        root.title(title)
        root.wm_attributes("-topmost", True)
        root.geometry("380x580")
        root.minsize(340, 400)

        tk.Label(
            root,
            text="Uncheck shots you do NOT want to build.\nHover the list and scroll with the mouse wheel.",
            justify=tk.LEFT,
        ).pack(pady=(8, 4), padx=12, anchor="w")

        outer = tk.Frame(root)
        outer.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 4))

        canvas = tk.Canvas(outer, highlightthickness=0, borderwidth=0)
        scrollbar = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas)
        canvas_window = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_inner_configure(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_configure(event):
            canvas.itemconfigure(canvas_window, width=event.width)

        def _on_mousewheel(event):
            if getattr(event, "delta", 0):
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif getattr(event, "num", None) == 4:
                canvas.yview_scroll(-1, "units")
            elif getattr(event, "num", None) == 5:
                canvas.yview_scroll(1, "units")

        def _bind_wheel(_event=None):
            root.bind_all("<MouseWheel>", _on_mousewheel)
            root.bind_all("<Button-4>", _on_mousewheel)
            root.bind_all("<Button-5>", _on_mousewheel)

        def _unbind_wheel(_event=None):
            root.unbind_all("<MouseWheel>")
            root.unbind_all("<Button-4>")
            root.unbind_all("<Button-5>")

        inner.bind("<Configure>", _on_inner_configure)
        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.bind("<Enter>", _bind_wheel)
        canvas.bind("<Leave>", _unbind_wheel)
        root.protocol("WM_DELETE_WINDOW", lambda: ( _unbind_wheel(), cancel()))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(inner, text="Shots", font=("", 9, "bold")).pack(anchor="w", pady=(0, 4))

        check_vars = {}
        for shot in available_shots:
            var = tk.BooleanVar(value=True)
            check_vars[shot] = var
            tk.Checkbutton(inner, text=shot, variable=var, anchor="w").pack(fill=tk.X, padx=2)

        tk.Frame(inner, height=1, bg="#cccccc").pack(fill=tk.X, pady=10)

        tk.Label(inner, text="Also build", font=("", 9, "bold")).pack(anchor="w", pady=(0, 4))

        lighting_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            inner,
            text="Lighting sequences (per selected shot)",
            variable=lighting_var,
            anchor="w",
        ).pack(fill=tk.X, padx=2)

        master_var = tk.BooleanVar(value=True)
        master_label = master_sequence_name_for(project) if project else "Master Sequence"
        tk.Checkbutton(
            inner,
            text=f"Master sequence: {master_label}",
            variable=master_var,
            anchor="w",
        ).pack(fill=tk.X, padx=2)

        btn_row = tk.Frame(root)
        btn_row.pack(pady=6)

        def select_all():
            for var in check_vars.values():
                var.set(True)

        def select_none():
            for var in check_vars.values():
                var.set(False)

        tk.Button(btn_row, text="Select All", command=select_all, width=12).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_row, text="Select None", command=select_none, width=12).pack(side=tk.LEFT, padx=4)

        def confirm():
            selected_shots = [s for s, var in check_vars.items() if var.get()]
            build_master = master_var.get()
            build_lighting = lighting_var.get()

            if not selected_shots and not build_master:
                messagebox.showwarning(
                    title="Nothing selected",
                    message="Select at least one shot and/or the master sequence.",
                    parent=root,
                )
                return

            _unbind_wheel()
            result["options"] = {
                "shots": selected_shots,
                "build_master": build_master,
                "build_lighting": build_lighting,
            }
            root.destroy()

        def cancel():
            _unbind_wheel()
            result["options"] = None
            root.destroy()

        tk.Button(root, text="Build Selected", command=confirm, width=20).pack(pady=4)
        tk.Button(root, text="Cancel", command=cancel, width=20).pack(pady=2)

        _bind_wheel()
        root.mainloop()
        return result["options"]
    except Exception:
        pass

    return None


def pick_shots_dialog(available_shots, title="Select Shots to Build"):
    """
    Checkbox dialog — shots only (legacy wrapper).
    Returns the list of selected shot names, or [] on cancel / nothing selected.
    """
    options = pick_build_options_dialog(available_shots, project="", title=title)
    if not options:
        return []
    return options["shots"]


def resolve_shots(all_shots, shot_filter="", interactive=False):
    """
    Decide which shots to build.

      interactive=False, shot_filter=""  → all shots
      interactive=True                  → checkbox dialog
      shot_filter="Shot01"              → single shot
      shot_filter="Shot01,Shot05"       → comma-separated list
    """
    if not all_shots:
        return []

    if interactive:
        options = pick_build_options_dialog(all_shots)
        return options["shots"] if options else []

    filt = (shot_filter or "").strip()
    if not filt:
        return list(all_shots)

    if "," in filt:
        requested = {s.strip().lower() for s in filt.split(",") if s.strip()}
        return [s for s in all_shots if s.lower() in requested]

    target = filt.lower()
    return [s for s in all_shots if s.lower() == target]


def confirm_dialog(message, title="Confirm"):
    """
    Yes/No confirmation dialog. Returns True only when the user clicks Yes.
    tkinter first, PowerShell MessageBox fallback.
    """
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", True)
        answer = messagebox.askyesno(title=title, message=message, parent=root)
        root.destroy()
        return bool(answer)
    except Exception:
        pass

    try:
        import subprocess
        ps = (
            "Add-Type -AssemblyName System.Windows.Forms; "
            f"$r = [System.Windows.Forms.MessageBox]::Show('{message}', '{title}', 'YesNo', 'Warning'); "
            "if ($r -eq 'Yes') { 'YES' } else { 'NO' }"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True, text=True, timeout=120
        )
        return result.stdout.strip() == "YES"
    except Exception:
        pass

    return False


# ─── UNREAL HELPERS ──────────────────────────────────────────────────────────

def get_asset_class_name(asset_data):
    try:
        return str(asset_data.asset_class_path.asset_name)   # UE 5.1+
    except AttributeError:
        return str(asset_data.asset_class)                   # older


def list_project_folders():
    """Return the names of all folders directly under /Game/Production/."""
    return list_production_projects()


def list_shot_folders(project):
    """Return shot folder names under /Game/Production/{project}/."""
    base = f"{PROJECT_ROOT}/{project}"
    subpaths = unreal.EditorAssetLibrary.list_assets(
        base, recursive=False, include_folder=True
    )
    shots = []
    for path in subpaths:
        name = str(path).rstrip("/").rsplit("/", 1)[-1]
        if "." not in name and is_shot_folder(name):
            shots.append(name)
    return sort_shot_names(shots)


def collect_shot_assets(project, shot):
    """
    Scan Shot##/Animation/ and return (anim_sequences, geometry_caches)
    as lists of asset package paths.
    """
    folder = f"{PROJECT_ROOT}/{project}/{shot}/Animation"
    anims, caches = [], []

    if not unreal.EditorAssetLibrary.does_directory_exist(folder):
        return anims, caches

    for object_path in unreal.EditorAssetLibrary.list_assets(folder, recursive=True, include_folder=False):
        asset_data = unreal.EditorAssetLibrary.find_asset_data(object_path)
        class_name = get_asset_class_name(asset_data)
        package    = str(object_path).split(".")[0]
        if class_name == "AnimSequence":
            anims.append(package)
        elif class_name == "GeometryCache":
            caches.append(package)

    return sorted(anims), sorted(caches)


def find_main_shot_sequence_path(project, shot):
    """
    Return the content path for a shot's main Level Sequence.

    Supports current names (Shot##_Project) and legacy names (Shot## only).
    Returns None when no main sequence is found.
    """
    shot_folder = f"{PROJECT_ROOT}/{project}/{shot}"
    if not unreal.EditorAssetLibrary.does_directory_exist(shot_folder):
        return None

    canonical = sequence_name_for(shot, project)
    canonical_path = f"{shot_folder}/{canonical}"
    if unreal.EditorAssetLibrary.does_asset_exist(canonical_path):
        return canonical_path

    legacy_path = f"{shot_folder}/{shot}"
    if unreal.EditorAssetLibrary.does_asset_exist(legacy_path):
        return legacy_path

    candidate_names = []
    for object_path in unreal.EditorAssetLibrary.list_assets(
        shot_folder, recursive=False, include_folder=False
    ):
        asset_data = unreal.EditorAssetLibrary.find_asset_data(object_path)
        if get_asset_class_name(asset_data) != "LevelSequence":
            continue
        name = str(object_path).rstrip("/").rsplit("/", 1)[-1].split(".")[0]
        candidate_names.append(name)

    picked = pick_main_shot_sequence_name(candidate_names, shot, project)
    if not picked:
        return None

    return f"{shot_folder}/{picked}"


# ─── SEQUENCE BUILDING ───────────────────────────────────────────────────────

def create_level_sequence(package_path, asset_name, fps=SEQUENCE_FPS):
    """Create and return a new LevelSequence asset at the given frame rate."""
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    sequence = asset_tools.create_asset(
        asset_name=asset_name,
        package_path=package_path,
        asset_class=unreal.LevelSequence,
        factory=unreal.LevelSequenceFactoryNew()
    )
    if sequence:
        sequence.set_display_rate(unreal.FrameRate(fps, 1))
    return sequence


def _set_section_range(section, start_frame, end_frame):
    """Set a Sequencer section's frame range (UE 5.4–5.7 tolerant)."""
    return set_shot_section_range(section, start_frame, end_frame)


def _assign_skeletal_animation(section, anim):
    """Assign an AnimSequence to a skeletal animation section."""
    if hasattr(section, "params"):
        section.params.animation = anim
        return
    section.set_editor_property("params", {"animation": anim})


def _assign_geometry_cache(section, cache):
    """Assign a GeometryCache to a geo cache section when supported."""
    try:
        params = section.get_editor_property("params")
        if hasattr(params, "geometry_cache"):
            params.geometry_cache = cache
            section.set_editor_property("params", params)
    except Exception:
        pass


def offset_binding_section_ranges(binding, offset_frames):
    """Shift every section on a spawnable binding forward by offset_frames."""
    offset = int(offset_frames)
    if offset <= 0 or binding is None:
        return

    tracks = []
    if hasattr(binding, "get_tracks"):
        try:
            tracks = binding.get_tracks()
        except Exception:
            tracks = []

    for track in tracks or []:
        sections = []
        if hasattr(track, "get_sections"):
            try:
                sections = track.get_sections()
            except Exception:
                sections = []
        for section in sections or []:
            try:
                start = _frame_number_value(section.get_start_frame())
                end = _frame_number_value(section.get_end_frame())
                _set_section_range(section, start + offset, end + offset)
            except Exception:
                continue


def set_sequence_playback_range(sequence, total_frames):
    """Set playback start/end on a Level Sequence."""
    total = max(int(total_frames), 1)
    sequence.set_playback_start(0)
    sequence.set_playback_end(total)


def add_anim_track(sequence, anim_package):
    """
    Bind the skeletal mesh referenced by an AnimSequence into the sequence
    and add an animation track with a 1-frame preroll hold plus full clip.
    Returns (ok, message, content_frames).
    """
    anim = unreal.load_asset(anim_package)
    if anim is None:
        return False, f"could not load {anim_package}", 0

    skeleton = anim.get_editor_property("skeleton")
    if skeleton is None:
        return False, f"{anim.get_name()} has no skeleton", 0

    # Find a SkeletalMesh compatible with this skeleton to spawn in the binding
    skeletal_mesh = None
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    for asset_data in registry.get_assets_by_class(
        unreal.TopLevelAssetPath("/Script/Engine", "SkeletalMesh"), True
    ):
        candidate = asset_data.get_asset()
        if candidate and candidate.skeleton == skeleton:
            skeletal_mesh = candidate
            break

    if skeletal_mesh is None:
        return False, f"no SkeletalMesh found for skeleton {skeleton.get_name()}", 0

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    temp_actor = actor_subsystem.spawn_actor_from_object(
        skeletal_mesh, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)
    )
    if temp_actor is None:
        return False, f"could not spawn actor for {skeletal_mesh.get_name()}", 0

    binding = sequence.add_spawnable_from_instance(temp_actor)
    actor_subsystem.destroy_actor(temp_actor)

    anim_track = binding.add_track(unreal.MovieSceneSkeletalAnimationTrack)

    frame_rate = sequence.get_display_rate()
    content_frames = int(anim.get_editor_property("sequence_length") * frame_rate.numerator / frame_rate.denominator)
    content_frames = max(content_frames, 1)
    total_frames = compute_total_shot_frames(content_frames, has_anim_or_cache=True)

    # Frame 0 — 1-frame hold on the first pose
    preroll = anim_track.add_section()
    _assign_skeletal_animation(preroll, anim)
    _set_section_range(preroll, 0, PREROLL_FRAMES)

    # Frame 1+ — full animation
    main = anim_track.add_section()
    _assign_skeletal_animation(main, anim)
    _set_section_range(main, PREROLL_FRAMES, total_frames)

    binding.set_display_name(anim.get_name())
    return True, (
        f"track for {anim.get_name()} (mesh: {skeletal_mesh.get_name()}, "
        f"preroll + {content_frames}f)"
    ), content_frames


def add_geocache_track(sequence, cache_package):
    """
    Add a Geometry Cache spawnable + track with preroll hold and full clip.
    Returns (ok, message, content_frames).
    """
    cache = unreal.load_asset(cache_package)
    if cache is None:
        return False, f"could not load {cache_package}", 0

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    temp_actor = actor_subsystem.spawn_actor_from_object(
        cache, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)
    )
    if temp_actor is None:
        return False, f"could not spawn actor for {cache.get_name()}", 0

    binding = sequence.add_spawnable_from_instance(temp_actor)
    actor_subsystem.destroy_actor(temp_actor)

    track = binding.add_track(unreal.MovieSceneGeometryCacheTrack)

    frame_rate = sequence.get_display_rate()
    try:
        duration_seconds = cache.calculate_duration()
    except Exception:
        duration_seconds = 0
    content_frames = max(int(duration_seconds * frame_rate.numerator / frame_rate.denominator), 1)
    total_frames = compute_total_shot_frames(content_frames, has_anim_or_cache=True)

    preroll = track.add_section()
    _assign_geometry_cache(preroll, cache)
    _set_section_range(preroll, 0, PREROLL_FRAMES)

    main = track.add_section()
    _assign_geometry_cache(main, cache)
    _set_section_range(main, PREROLL_FRAMES, total_frames)

    binding.set_display_name(cache.get_name())
    return True, f"geo cache track for {cache.get_name()} (preroll + {content_frames}f)", content_frames


def add_camera(sequence, camera_fbx_path, camera_name, content_frames=0, total_frames=0,
               has_anim_or_cache=False):
    """
    Spawn a CineCamera, add a Camera Cut track from frame 0, import camera FBX.
    Returns (ok, message).
    """
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    temp_camera = actor_subsystem.spawn_actor_from_class(
        unreal.CineCameraActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)
    )
    if temp_camera is None:
        return False, "could not spawn CineCameraActor"

    cine_component = temp_camera.get_cine_camera_component()
    focus_settings = cine_component.get_editor_property("focus_settings")
    focus_settings.focus_method = unreal.CameraFocusMethod.DISABLE
    cine_component.set_editor_property("focus_settings", focus_settings)

    binding = sequence.add_spawnable_from_instance(temp_camera)
    actor_subsystem.destroy_actor(temp_camera)
    binding.set_display_name(camera_name)

    cam_start = camera_start_frame(has_anim_or_cache, content_frames)
    playback_end = total_frames if total_frames > 0 else max(content_frames, 1)

    cut_track = sequence.add_track(unreal.MovieSceneCameraCutTrack)
    cut_section = cut_track.add_section()
    _set_section_range(cut_section, cam_start, playback_end)

    binding_id = unreal.MovieSceneObjectBindingID()
    try:
        binding_id = sequence.get_binding_id(binding)
    except Exception:
        binding_id = sequence.make_binding_id(binding, unreal.MovieSceneObjectBindingSpace.LOCAL)
    cut_section.set_camera_binding_id(binding_id)

    settings = unreal.MovieSceneUserImportFBXSettings()
    settings.set_editor_property("match_by_name_only", False)
    settings.set_editor_property("create_cameras", False)
    settings.set_editor_property("reduce_keys", False)
    settings.set_editor_property("force_front_x_axis", False)

    world = unreal.UnrealEditorSubsystem().get_editor_world()

    try:
        ok = unreal.SequencerTools.import_level_sequence_fbx(
            world, sequence, [binding], settings, camera_fbx_path
        )
    except Exception as exc:
        return False, f"camera FBX import failed: {exc}"

    if not ok:
        return False, "camera FBX import returned False"

    return True, (
        f"camera '{camera_name}' imported from {os.path.basename(camera_fbx_path)} "
        f"(frames 0–{playback_end})"
    )


def _frame_number_value(frame):
    """Coerce UE FrameNumber / int to a plain int."""
    if frame is None:
        return 0
    if hasattr(frame, "value"):
        return int(frame.value)
    return int(frame)


def get_sequence_duration_frames(sequence, fps=SEQUENCE_FPS):
    """Playback length of a Level Sequence in frames (minimum 1)."""
    if sequence is None:
        return 1

    try:
        start = _frame_number_value(sequence.get_playback_start())
        end = _frame_number_value(sequence.get_playback_end())
        duration = end - start
        if duration > 0:
            return duration
    except Exception:
        pass

    try:
        movie_scene = sequence.get_movie_scene()
        playback = movie_scene.get_playback_range()
        start = _frame_number_value(playback.get_start_frame())
        end = _frame_number_value(playback.get_end_frame())
        duration = end - start
        if duration > 0:
            return duration
    except Exception:
        pass

    return max(int(fps), 1)


def get_or_load_sequence(seq_path):
    """Load an existing Level Sequence asset, or None."""
    if not unreal.EditorAssetLibrary.does_asset_exist(seq_path):
        return None

    asset = unreal.EditorAssetLibrary.load_asset(seq_path)
    if asset is not None:
        return asset

    asset_name = seq_path.rsplit("/", 1)[-1]
    return unreal.load_asset(f"{seq_path}.{asset_name}")


def add_cinematic_shot_track(master_sequence):
    """
    Add the Sequencer Shot Track (MovieSceneCinematicShotTrack) to a master LS.
    Tries UE 5.4–5.7 APIs in order.
    """
    track_class = unreal.MovieSceneCinematicShotTrack
    ext = getattr(unreal, "MovieSceneSequenceExtensions", None)

    if ext is not None:
        for method_name in ("add_track", "add_master_track"):
            method = getattr(ext, method_name, None)
            if method is None:
                continue
            try:
                track = method(master_sequence, track_class)
                if track is not None:
                    return track
            except Exception:
                continue

    for method_name in ("add_track", "add_master_track"):
        method = getattr(master_sequence, method_name, None)
        if method is None:
            continue
        try:
            track = method(track_class)
            if track is not None:
                return track
        except Exception:
            continue

    return None


def add_shot_track_section(shot_track):
    """Add a section to the cinematic shot track."""
    ext = getattr(unreal, "MovieSceneTrackExtensions", None)
    if ext is not None and hasattr(ext, "add_section"):
        try:
            section = ext.add_section(shot_track)
            if section is not None:
                return section
        except Exception:
            pass
    return shot_track.add_section()


def assign_shot_section_sequence(section, shot_sequence):
    """Bind a child Level Sequence onto a cinematic shot section."""
    if hasattr(section, "set_sequence"):
        try:
            section.set_sequence(shot_sequence)
            return
        except Exception:
            pass
    section.set_editor_property("sub_sequence", shot_sequence)


def set_shot_section_range(section, start_frame, end_frame):
    """Set master-timeline frame range for a shot section."""
    start = int(start_frame)
    end = int(end_frame)

    for attempt in (
        lambda: section.set_range(unreal.FrameNumber(start), unreal.FrameNumber(end)),
        lambda: section.set_range(start, end),
        lambda: (
            section.set_start_frame_bounded(start),
            section.set_end_frame_bounded(end),
        ),
        lambda: (
            section.set_start_frame(start),
            section.set_end_frame(end),
        ),
    ):
        try:
            attempt()
            return True
        except Exception:
            continue
    return False


def finalize_master_sequence(master, master_path, total_frames):
    """Save master sequence and mark the package dirty."""
    master.set_playback_start(0)
    master.set_playback_end(int(total_frames))

    try:
        master.modify(True)
    except Exception:
        pass

    try:
        unreal.EditorAssetLibrary.save_loaded_asset(master, only_if_is_dirty=False)
    except Exception:
        unreal.EditorAssetLibrary.save_asset(master_path)


def build_lighting_sequence(shot_folder, seq_name, fps=SEQUENCE_FPS, total_frames=0):
    """
    Create or load an empty lighting Level Sequence in the shot folder.
    Returns (sequence, created) — created is False when the asset already existed.
    """
    seq_path = f"{shot_folder}/{seq_name}"
    if unreal.EditorAssetLibrary.does_asset_exist(seq_path):
        sequence = get_or_load_sequence(seq_path)
        if sequence and total_frames > 0:
            set_sequence_playback_range(sequence, total_frames)
            unreal.EditorAssetLibrary.save_asset(seq_path)
        return sequence, False

    sequence = create_level_sequence(shot_folder, seq_name, fps)
    if sequence is None:
        return None, False

    default_frames = total_frames if total_frames > 0 else max(fps, 1)
    set_sequence_playback_range(sequence, default_frames)
    unreal.EditorAssetLibrary.save_asset(seq_path)
    return sequence, True


def sync_lighting_sequence(shot_folder, lighting_name, total_frames):
    """Set lighting LS playback range to match the parent shot length."""
    lighting_path = f"{shot_folder}/{lighting_name}"
    if not unreal.EditorAssetLibrary.does_asset_exist(lighting_path):
        return None, False

    lighting_seq = get_or_load_sequence(lighting_path)
    if lighting_seq is None:
        return None, False

    set_sequence_playback_range(lighting_seq, total_frames)
    unreal.EditorAssetLibrary.save_asset(lighting_path)
    return lighting_seq, True


def add_lighting_subsequence(main_sequence, lighting_sequence, total_frames):
    """
    Embed the lighting Level Sequence on a MovieSceneSubTrack (default name).
    Returns (ok, message).
    """
    if main_sequence is None or lighting_sequence is None:
        return False, "missing main or lighting sequence"

    total = max(int(total_frames), 1)
    sub_track = None

    for method_name in ("add_master_track", "add_track"):
        method = getattr(main_sequence, method_name, None)
        if method is None:
            continue
        try:
            sub_track = method(unreal.MovieSceneSubTrack)
            if sub_track is not None:
                break
        except Exception:
            continue

    if sub_track is None:
        ext = getattr(unreal, "MovieSceneSequenceExtensions", None)
        if ext is not None:
            for method_name in ("add_track", "add_master_track"):
                method = getattr(ext, method_name, None)
                if method is None:
                    continue
                try:
                    sub_track = method(main_sequence, unreal.MovieSceneSubTrack)
                    if sub_track is not None:
                        break
                except Exception:
                    continue

    if sub_track is None:
        return False, "could not add MovieSceneSubTrack"

    section = sub_track.add_section()
    assign_shot_section_sequence(section, lighting_sequence)
    if not _set_section_range(section, 0, total):
        return False, "could not set lighting subsequence range"

    return True, f"lighting subsequence 0–{total}"


def estimate_shot_duration_frames(project, shot, fps=SEQUENCE_FPS):
    """Estimate shot length from animation / geo cache assets (for dry-run master planning)."""
    anims, caches = collect_shot_assets(project, shot)
    longest = 0

    for anim_package in anims:
        anim = unreal.load_asset(anim_package)
        if anim is not None:
            length_seconds = anim.get_editor_property("sequence_length")
            longest = max(longest, int(length_seconds * fps))

    for cache_package in caches:
        cache = unreal.load_asset(cache_package)
        if cache is not None:
            try:
                duration_seconds = cache.calculate_duration()
                longest = max(longest, int(duration_seconds * fps))
            except Exception:
                pass

    return max(longest, fps)


def collect_master_shot_entries(project, shots, planned_shots=None, fps=SEQUENCE_FPS):
    """
    Shots to place in the master sequence: existing shot sequences plus any
    planned for creation this run (dry run or real build).
    Returns list of (shot, seq_path, duration_frames, estimated).
    """
    project_folder = f"{PROJECT_ROOT}/{project}"
    planned_shots = planned_shots or set()
    entries = []

    for shot in sort_shot_names(shots):
        shot_seq_name = sequence_name_for(shot, project)
        shot_seq_path = f"{project_folder}/{shot}/{shot_seq_name}"

        if unreal.EditorAssetLibrary.does_asset_exist(shot_seq_path):
            seq = get_or_load_sequence(shot_seq_path)
            duration = get_sequence_duration_frames(seq)
            entries.append((shot, shot_seq_path, duration, False))
        elif shot in planned_shots:
            duration = estimate_shot_duration_frames(project, shot, fps)
            entries.append((shot, shot_seq_path, duration, True))

    return entries


def build_master_sequence(project, shots, fps=SEQUENCE_FPS, overwrite=False, dry_run=False,
                          planned_shots=None):
    """
    Assemble a master Level Sequence at /Game/Production/{project}/{project}_Master
    with every shot sequence as a cinematic shot in production order.

    Existing master is never deleted unless overwrite=True.
    planned_shots: shot names that will be created this run (not on disk yet).
    """
    project_folder = f"{PROJECT_ROOT}/{project}"
    master_name = master_sequence_name_for(project)
    master_path = f"{project_folder}/{master_name}"

    shot_entries = collect_master_shot_entries(
        project, shots, planned_shots=planned_shots, fps=fps
    )

    if not shot_entries:
        unreal.log_warning(
            "Master sequence — no shot sequences to assemble "
            "(build shot sequences first, or ensure shots have animation assets)."
        )
        return False

    if unreal.EditorAssetLibrary.does_asset_exist(master_path) and not overwrite:
        unreal.log(f"    → SKIPPED — {master_name} already exists (enable Overwrite to rebuild)")
        return False

    if dry_run:
        unreal.log(f"    [DRY RUN] Would create master: {master_path}")
        unreal.log("    [DRY RUN]   + Shot Track (MovieSceneCinematicShotTrack)")
        frame_cursor = 0
        for shot, shot_seq_path, duration, estimated in shot_entries:
            est_tag = " (estimated duration)" if estimated else ""
            unreal.log(
                f"    [DRY RUN]   + shot {shot}: frames {frame_cursor}–{frame_cursor + duration} "
                f"({shot_seq_path.rsplit('/', 1)[-1]}){est_tag}"
            )
            frame_cursor += duration
        unreal.log(f"    [DRY RUN]   total playback: 0–{frame_cursor} frames ({len(shot_entries)} shots)")
        return True

    if unreal.EditorAssetLibrary.does_asset_exist(master_path):
        unreal.EditorAssetLibrary.delete_asset(master_path)
        unreal.log(f"    ⟳ Deleted existing {master_name} (overwrite)")

    master = create_level_sequence(project_folder, master_name, fps)
    if master is None:
        unreal.log_error(f"    ✗ Could not create master sequence {master_path}")
        return False

    shot_track = add_cinematic_shot_track(master)
    if shot_track is None:
        unreal.log_error("    ✗ Could not add Shot Track (MovieSceneCinematicShotTrack) to master")
        return False

    unreal.log("    ✓ Added Shot Track to master")
    frame_cursor = 0
    sections_added = 0

    for shot, shot_seq_path, _duration_hint, _estimated in shot_entries:
        shot_seq = get_or_load_sequence(shot_seq_path)
        if shot_seq is None:
            unreal.log_warning(f"    ! master — could not load {shot_seq_path}")
            continue

        duration = get_sequence_duration_frames(shot_seq, fps)
        start_frame = frame_cursor
        end_frame = frame_cursor + duration

        section = add_shot_track_section(shot_track)
        if section is None:
            unreal.log_warning(f"    ! master — could not add shot section for {shot}")
            continue

        assign_shot_section_sequence(section, shot_seq)

        if not set_shot_section_range(section, start_frame, end_frame):
            unreal.log_warning(f"    ! master — could not set frame range for {shot}")

        try:
            section.set_shot_display_name(shot)
        except Exception:
            pass

        try:
            section.set_is_active(True)
        except Exception:
            pass

        unreal.log(
            f"    ✓ Shot Track + {shot}: frames {start_frame}–{end_frame} "
            f"→ {shot_seq_path.rsplit('/', 1)[-1]}"
        )
        frame_cursor = end_frame
        sections_added += 1

    if sections_added == 0:
        unreal.log_error("    ✗ Master sequence has no shot sections — not saving")
        return False

    finalize_master_sequence(master, master_path, frame_cursor)
    unreal.log(
        f"    ✓ Created master {master_path} "
        f"(Shot Track, {sections_added} shots, {frame_cursor} frames)"
    )
    return True


# ─── MAIN ────────────────────────────────────────────────────────────────────

def run(project_name="", camera_folder="", shot_filter="", dry_run=False, fps=SEQUENCE_FPS,
        overwrite=False, interactive_shots=False, build_lighting=True, build_master=True):
    """
    Build Level Sequences for shots in the chosen project.

      project_name      from widget Project combo (auto-detect if blank and unambiguous)
      camera_folder     blank → uses last Find Camera Folder pick
      shot_filter       optional: "Shot01" or "Shot01,Shot05" (ignored when interactive_shots=True)
      interactive_shots True  → checkbox dialog to pick shots (all checked by default)
      dry_run           True  → log the full build plan without creating anything
      fps               24, 30, or 60 (default 24)
      overwrite         True  → delete and rebuild existing sequences (asks to confirm first)
      build_lighting    True  → create empty lighting Level Sequence per shot folder
      build_master      True  → assemble all shot sequences into {Project}_Master at project root
    """
    sep = "=" * 60

    if fps not in (24, 30, 60):
        unreal.log_warning(f"Unusual fps value '{fps}' — using it anyway (expected 24, 30, or 60)")

    # ── Resolve project ──────────────────────────────────────────────────────
    projects = list_project_folders()
    if not projects:
        unreal.log_error(f"No project folders found under {PROJECT_ROOT}")
        return

    raw_project = project_name
    project = resolve_production_project(project_name, projects)
    if not project:
        if len(projects) == 1:
            project = projects[0]
        else:
            unreal.log_error(
                "Select a production project in the widget dropdown. "
                f"Received project_name={raw_project!r}. "
                f"Available: {', '.join(projects)}. "
                "Check Format Text pin {project} is wired to SequenceProjectCombo "
                "(Get Selected Option or Get Option String At Index), "
                "not the Organize Project Name text box."
            )
            return
    if not project:
        unreal.log_warning("No project selected — aborting.")
        return
    if project not in projects:
        unreal.log_error(f"Project '{project}' not found under {PROJECT_ROOT}. Found: {projects}")
        return

    # ── Camera folder (from widget text box, or last Find Camera Folder pick) ─
    cam_folder = camera_folder.strip() or get_last_camera_folder()
    camera_files = []
    if not cam_folder:
        unreal.log_warning(
            "No camera folder set — click Find Camera Folder before Build Sequences. "
            "Sequences will be built without cameras."
        )
    elif os.path.isdir(cam_folder):
        camera_files = [f for f in os.listdir(cam_folder) if _CAMERA_FBX_RE.match(f)]
    else:
        unreal.log_error(f"Camera folder does not exist: {cam_folder}")
        return

    # ── Discover shots ───────────────────────────────────────────────────────
    all_shots = list_shot_folders(project)
    build_master_run = build_master
    build_lighting_run = build_lighting
    shots_for_master = list_shot_folders(project)

    if interactive_shots:
        picker = pick_build_options_dialog(all_shots, project=project)
        if picker is None:
            unreal.log_warning("Shot picker cancelled — nothing built.")
            return
        shots = picker["shots"]
        build_master_run = picker["build_master"]
        build_lighting_run = picker["build_lighting"]
        shots_for_master = shots if shots else all_shots
    else:
        shots = resolve_shots(all_shots, shot_filter=shot_filter, interactive=False)

    if not shots and not build_master_run:
        unreal.log_warning(
            f"Nothing selected to build for project '{project}'"
            + (f" (filter: '{shot_filter}')" if shot_filter else "")
        )
        return

    # ── Overwrite confirmation ───────────────────────────────────────────────
    existing = [
        s for s in shots
        if unreal.EditorAssetLibrary.does_asset_exist(
            f"{PROJECT_ROOT}/{project}/{s}/{sequence_name_for(s, project)}"
        )
    ]

    master_name = master_sequence_name_for(project)
    master_path = f"{PROJECT_ROOT}/{project}/{master_name}"
    master_exists = unreal.EditorAssetLibrary.does_asset_exist(master_path)

    if overwrite and (existing or (build_master_run and master_exists)) and not dry_run:
        parts = []
        if existing:
            parts.append(f"{len(existing)} shot sequence(s)")
        if build_master_run and master_exists:
            parts.append("the master sequence")
        confirmed = confirm_dialog(
            f"Are you sure you want to OVERWRITE {' and '.join(parts)} in '{project}'?\n\n"
            "This deletes them and rebuilds from current shot assets. "
            "This cannot be undone.",
            title="Overwrite Level Sequences?"
        )
        if not confirmed:
            unreal.log_warning("Overwrite not confirmed — aborting. "
                               "Run without overwrite to build only missing sequences.")
            return

    unreal.log(f"\n{sep}")
    unreal.log("Script 2 — Level Sequence Builder")
    unreal.log(f"Project : {project}")
    unreal.log(f"FPS     : {fps}")
    unreal.log(f"Cameras : {cam_folder or '(none)'}  ({len(camera_files)} camera FBX found)")
    unreal.log(f"Shots   : {len(shots)}" + (
        "  (picker selection)" if interactive_shots else
        f"  (filter: {shot_filter})" if shot_filter else "  (all)"
    ))
    if overwrite:
        rebuild_note = f"ON — {len(existing)} existing shot sequence(s) will be rebuilt"
        if build_master_run and master_exists:
            rebuild_note += f"; {master_name} will be rebuilt"
        unreal.log(f"Overwrite : {rebuild_note}")
    if build_lighting_run:
        unreal.log("Lighting  : ON — lighting LS + subsequence track per shot")
    if build_master_run:
        unreal.log(f"Master    : ON — {master_name} at {PROJECT_ROOT}/{project}/")
    if dry_run:
        unreal.log("Mode    : DRY RUN — nothing will be created")
    elif not overwrite:
        unreal.log("Preserve: ON — existing shot, lighting, and master sequences are left untouched")
    unreal.log(sep)

    counts = {"built": 0, "skipped": 0, "errors": 0, "lighting": 0}
    missing_cameras = []   # shots that have assets but no camera FBX
    empty_folders   = []   # shots whose Animation folder has nothing usable
    planned_shots_for_master = set()  # shots that will exist after this run

    for shot in shots:
        shot_folder   = f"{PROJECT_ROOT}/{project}/{shot}"
        seq_name      = sequence_name_for(shot, project)
        seq_path      = f"{shot_folder}/{seq_name}"
        lighting_name = lighting_sequence_name_for(shot, project)
        lighting_path = f"{shot_folder}/{lighting_name}"

        unreal.log(f"\n  {shot}")

        if build_lighting_run:
            if dry_run:
                if unreal.EditorAssetLibrary.does_asset_exist(lighting_path) and not overwrite:
                    unreal.log(f"    [DRY RUN] Lighting SKIPPED — {lighting_name} already exists")
                else:
                    action = "create" if not unreal.EditorAssetLibrary.does_asset_exist(lighting_path) else "overwrite"
                    unreal.log(f"    [DRY RUN] Would {action} lighting: {lighting_path}")
            else:
                lighting_exists = unreal.EditorAssetLibrary.does_asset_exist(lighting_path)
                if lighting_exists and not overwrite:
                    unreal.log(f"    → Lighting SKIPPED — {lighting_name} already exists")
                elif lighting_exists and overwrite:
                    unreal.EditorAssetLibrary.delete_asset(lighting_path)
                    unreal.log(f"    ⟳ Deleted existing {lighting_name} (overwrite)")
                    lighting_seq, created = build_lighting_sequence(shot_folder, lighting_name, fps)
                    if lighting_seq:
                        unreal.log(f"    ✓ Created lighting {lighting_path}")
                        counts["lighting"] += 1
                    else:
                        unreal.log_warning(f"    ! lighting failed for {shot}")
                else:
                    lighting_seq, created = build_lighting_sequence(shot_folder, lighting_name, fps)
                    if lighting_seq and created:
                        unreal.log(f"    ✓ Created lighting {lighting_path}")
                        counts["lighting"] += 1
                    elif not lighting_seq:
                        unreal.log_warning(f"    ! lighting failed for {shot}")

        # Existing sequence: skip by default, delete first when overwriting
        if unreal.EditorAssetLibrary.does_asset_exist(seq_path):
            if not overwrite:
                unreal.log(f"    → SKIPPED — {seq_name} already exists")
                counts["skipped"] += 1
                continue
            if dry_run:
                unreal.log(f"    [DRY RUN] Would overwrite existing {seq_name}")
            else:
                unreal.EditorAssetLibrary.delete_asset(seq_path)
                unreal.log(f"    ⟳ Deleted existing {seq_name} (overwrite)")

        anims, caches = collect_shot_assets(project, shot)
        camera_fbx    = find_camera_fbx(shot, camera_files)

        unreal.log(f"    anims={len(anims)}  geo caches={len(caches)}  camera={'yes' if camera_fbx else 'NO'}")

        if not anims and not caches:
            empty_folders.append(shot)

        if not camera_fbx:
            missing_cameras.append(shot)

        if not anims and not caches and not camera_fbx:
            unreal.log_warning(f"    → SKIPPED — nothing to add for {shot}")
            counts["skipped"] += 1
            continue

        if dry_run:
            unreal.log(f"    [DRY RUN] Would create: {seq_path}")
            for a in anims:
                unreal.log(f"    [DRY RUN]   + anim track    : {a.rsplit('/', 1)[-1]} (preroll + full)")
            for c in caches:
                unreal.log(f"    [DRY RUN]   + geo cache     : {c.rsplit('/', 1)[-1]} (preroll + full)")
            if camera_fbx:
                unreal.log(
                    f"    [DRY RUN]   + camera        : {camera_name_for(camera_fbx)} (starts frame 0)"
                )
            else:
                unreal.log(f"    [DRY RUN]   ! no camera FBX — sequence without Camera Cut track")
            if build_lighting_run and unreal.EditorAssetLibrary.does_asset_exist(lighting_path):
                est = estimate_shot_duration_frames(project, shot, fps)
                total_est = compute_total_shot_frames(est, has_anim_or_cache=bool(anims or caches))
                unreal.log(
                    f"    [DRY RUN]   + lighting subseq: {lighting_name} (0–{total_est})"
                )
            elif build_lighting_run:
                unreal.log(f"    [DRY RUN]   + lighting subseq: {lighting_name} (after lighting LS created)")
            planned_shots_for_master.add(shot)
            counts["built"] += 1
            continue

        # ── Real build ───────────────────────────────────────────────────────
        try:
            sequence = create_level_sequence(shot_folder, seq_name, fps)
            if sequence is None:
                unreal.log_error(f"    ✗ Could not create sequence {seq_path}")
                counts["errors"] += 1
                continue

            content_frames = 0
            has_anim_or_cache = bool(anims or caches)

            for anim_package in anims:
                ok, msg, frames = add_anim_track(sequence, anim_package)
                if ok:
                    unreal.log(f"    ✓ {msg}")
                    content_frames = max(content_frames, frames)
                else:
                    unreal.log_warning(f"    ! anim skipped — {msg}")

            for cache_package in caches:
                ok, msg, frames = add_geocache_track(sequence, cache_package)
                if ok:
                    unreal.log(f"    ✓ {msg}")
                    content_frames = max(content_frames, frames)
                else:
                    unreal.log_warning(f"    ! geo cache skipped — {msg}")

            total_frames = compute_total_shot_frames(content_frames, has_anim_or_cache)

            if camera_fbx:
                fbx_path = f"{cam_folder}/{camera_fbx}"
                ok, msg = add_camera(
                    sequence,
                    fbx_path,
                    camera_name_for(camera_fbx),
                    content_frames=content_frames,
                    total_frames=total_frames,
                    has_anim_or_cache=has_anim_or_cache,
                )
                if ok:
                    unreal.log(f"    ✓ {msg}")
                else:
                    unreal.log_warning(f"    ! camera failed — {msg}")
            else:
                unreal.log_warning(f"    ! no camera FBX for {shot} — built without Camera Cut track")

            if total_frames > 0:
                set_sequence_playback_range(sequence, total_frames)
                if has_anim_or_cache:
                    unreal.log(
                        f"    ✓ playback range: 0–{total_frames} frames "
                        f"({content_frames}f content + {PREROLL_FRAMES}f preroll, {fps} fps)"
                    )
                else:
                    unreal.log(f"    ✓ playback range: 0–{total_frames} frames ({fps} fps)")

            if build_lighting_run:
                if not unreal.EditorAssetLibrary.does_asset_exist(lighting_path):
                    lighting_seq, _created = build_lighting_sequence(
                        shot_folder, lighting_name, fps, total_frames=total_frames
                    )
                    if lighting_seq:
                        counts["lighting"] += 1
                else:
                    lighting_seq, _synced = sync_lighting_sequence(
                        shot_folder, lighting_name, total_frames
                    )

                lighting_seq = get_or_load_sequence(lighting_path)
                if lighting_seq and total_frames > 0:
                    ok, msg = add_lighting_subsequence(sequence, lighting_seq, total_frames)
                    if ok:
                        unreal.log(f"    ✓ {msg}")
                    else:
                        unreal.log_warning(f"    ! lighting subsequence — {msg}")
                elif build_lighting_run:
                    unreal.log_warning(f"    ! lighting subsequence skipped — {lighting_name} missing")

            unreal.EditorAssetLibrary.save_asset(seq_path)
            unreal.log(f"    ✓ Created {seq_path}")
            planned_shots_for_master.add(shot)
            counts["built"] += 1

        except Exception as exc:
            unreal.log_error(f"    ✗ Error building {shot}: {exc}")
            counts["errors"] += 1

    unreal.log(f"\n{sep}")
    unreal.log(
        f"Done — Built: {counts['built']}  "
        f"Skipped: {counts['skipped']}  "
        f"Errors: {counts['errors']}  "
        f"Lighting: {counts['lighting']}"
    )

    # ── Master sequence (all shots in production order) ──────────────────────
    if build_master_run:
        unreal.log(f"\n  Master sequence — {master_name}")
        try:
            build_master_sequence(
                project,
                shots_for_master,
                fps=fps,
                overwrite=overwrite,
                dry_run=dry_run,
                planned_shots=planned_shots_for_master,
            )
        except Exception as exc:
            unreal.log_error(f"    ✗ Master sequence failed: {exc}")

    unreal.log(f"\n{sep}")

    # ── Health check ─────────────────────────────────────────────────────────
    if missing_cameras:
        unreal.log_warning(
            f"Cameras missing : {len(missing_cameras)}  ({', '.join(missing_cameras)})"
        )
    else:
        unreal.log("Cameras missing : none")

    if empty_folders:
        unreal.log_warning(
            f"Empty folders   : {len(empty_folders)}  ({', '.join(empty_folders)})"
        )
    else:
        unreal.log("Empty folders   : 0")

    unreal.log(sep + "\n")


if __name__ == '__main__':
    run()

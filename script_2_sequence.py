# script_2_sequence.py
# Level Sequence Builder — run AFTER script_1_organize.py has routed assets
# into shot folders. Full design: SCRIPT_2_PLAN.md
#
# From the Unreal Python console:
#   import sys; sys.path.append("A:/Anim_8_Scripts")
#   import script_2_sequence
#   script_2_sequence.run(dry_run=True)                      # full plan, builds nothing
#   script_2_sequence.run(shot_filter="Shot01", dry_run=False)  # build one shot only
#   script_2_sequence.run(dry_run=False)                     # build everything

# ─── CONFIG ──────────────────────────────────────────────────────────────────

PROJECT_ROOT = "/Game/Production"
ASSETS_ROOT  = "/Game/Assets"

# Sequence display rate (frames per second) used when creating new sequences
SEQUENCE_FPS = 24

# ─── END CONFIG ──────────────────────────────────────────────────────────────

import os
import re
import unreal

from pipeline_common import get_open_project_name, resolve_production_project, get_last_camera_folder

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


# ─── DIALOGS ─────────────────────────────────────────────────────────────────

def ask_choice(options, title="Select Project", default=""):
    """
    Show a list of options and let the user pick one.
    Returns the chosen string, or '' on cancel.
    Pre-selects `default` when it appears in the list.
    """
    if len(options) == 1:
        return options[0]

    try:
        import tkinter as tk
        chosen = {"value": ""}

        root = tk.Tk()
        root.title(title)
        root.wm_attributes("-topmost", True)
        root.geometry("360x320")

        tk.Label(root, text="Select the production folder to build sequences for:").pack(pady=8)

        listbox = tk.Listbox(root)
        select_index = 0
        for i, option in enumerate(options):
            listbox.insert(tk.END, option)
            if default and option.lower() == default.lower():
                select_index = i
        listbox.selection_set(select_index)
        listbox.pack(fill=tk.BOTH, expand=True, padx=12)

        def confirm():
            selection = listbox.curselection()
            if selection:
                chosen["value"] = listbox.get(selection[0])
            root.destroy()

        tk.Button(root, text="OK", command=confirm).pack(pady=8)
        root.mainloop()
        return chosen["value"]
    except Exception:
        pass

    # PowerShell fallback: numbered choice via InputBox
    try:
        import subprocess
        menu = "; ".join(f"{i + 1} = {name}" for i, name in enumerate(options))
        ps = (
            "[System.Reflection.Assembly]::LoadWithPartialName('Microsoft.VisualBasic') | Out-Null; "
            f"[Microsoft.VisualBasic.Interaction]::InputBox('Type the number of the project: {menu}', '{title}', '1')"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True, text=True, timeout=120
        )
        index = int(result.stdout.strip()) - 1
        if 0 <= index < len(options):
            return options[index]
    except Exception:
        pass

    return ""


def pick_shots_dialog(available_shots, title="Select Shots to Build"):
    """
    Checkbox dialog — all shots checked by default. Uncheck any you skip.
    Returns the list of selected shot names, or [] on cancel / nothing selected.
    """
    if not available_shots:
        return []

    try:
        import tkinter as tk
        result = {"shots": None}

        root = tk.Tk()
        root.title(title)
        root.wm_attributes("-topmost", True)
        root.geometry("340x520")

        tk.Label(
            root,
            text="Uncheck shots you do NOT want to build.\n(Ctrl+scroll to scroll the list.)"
        ).pack(pady=8)

        outer = tk.Frame(root)
        outer.pack(fill=tk.BOTH, expand=True, padx=12)

        canvas = tk.Canvas(outer, highlightthickness=0)
        scrollbar = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas)

        inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        check_vars = {}
        for shot in available_shots:
            var = tk.BooleanVar(value=True)
            check_vars[shot] = var
            tk.Checkbutton(inner, text=shot, variable=var, anchor="w").pack(fill=tk.X)

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
            result["shots"] = [s for s, var in check_vars.items() if var.get()]
            root.destroy()

        def cancel():
            result["shots"] = []
            root.destroy()

        tk.Button(root, text="Build Selected", command=confirm, width=20).pack(pady=4)
        tk.Button(root, text="Cancel", command=cancel, width=20).pack(pady=2)

        root.mainloop()
        return result["shots"] if result["shots"] is not None else []
    except Exception:
        pass

    return []


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
        return pick_shots_dialog(all_shots)

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
    subpaths = unreal.EditorAssetLibrary.list_assets(
        PROJECT_ROOT, recursive=False, include_folder=True
    )
    folders = []
    for path in subpaths:
        path = str(path).rstrip("/")
        if "." not in path.rsplit("/", 1)[-1]:
            folders.append(path.rsplit("/", 1)[-1])
    return sorted(folders)


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
    return sorted(shots)


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


def add_anim_track(sequence, anim_package):
    """
    Bind the skeletal mesh referenced by an AnimSequence into the sequence
    and add an animation track playing that AnimSequence.
    Returns (ok, message, duration_frames).
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

    # Spawn a temporary SkeletalMeshActor, build the spawnable from it, then
    # remove the temp actor. Passing the raw mesh asset to
    # add_spawnable_from_instance creates an object binding Sequencer cannot
    # spawn (greyed-out tracks).
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    temp_actor = actor_subsystem.spawn_actor_from_object(
        skeletal_mesh, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)
    )
    if temp_actor is None:
        return False, f"could not spawn actor for {skeletal_mesh.get_name()}", 0

    binding = sequence.add_spawnable_from_instance(temp_actor)
    actor_subsystem.destroy_actor(temp_actor)

    anim_track = binding.add_track(unreal.MovieSceneSkeletalAnimationTrack)
    section = anim_track.add_section()
    section.params.animation = anim

    frame_rate = sequence.get_display_rate()
    duration_frames = int(anim.get_editor_property("sequence_length") * frame_rate.numerator / frame_rate.denominator)
    duration_frames = max(duration_frames, 1)
    section.set_range(0, duration_frames)

    binding.set_display_name(anim.get_name())
    return True, f"track for {anim.get_name()} (mesh: {skeletal_mesh.get_name()})", duration_frames


def add_geocache_track(sequence, cache_package):
    """
    Add a Geometry Cache spawnable + track to the sequence.
    Returns (ok, message, duration_frames).
    """
    cache = unreal.load_asset(cache_package)
    if cache is None:
        return False, f"could not load {cache_package}", 0

    # Same temp-actor pattern as add_anim_track — the binding must come from
    # a spawned GeometryCacheActor, not the raw asset.
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    temp_actor = actor_subsystem.spawn_actor_from_object(
        cache, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)
    )
    if temp_actor is None:
        return False, f"could not spawn actor for {cache.get_name()}", 0

    binding = sequence.add_spawnable_from_instance(temp_actor)
    actor_subsystem.destroy_actor(temp_actor)

    track = binding.add_track(unreal.MovieSceneGeometryCacheTrack)
    section = track.add_section()

    frame_rate = sequence.get_display_rate()
    try:
        duration_seconds = cache.calculate_duration()
    except Exception:
        duration_seconds = 0
    duration_frames = max(int(duration_seconds * frame_rate.numerator / frame_rate.denominator), 1)
    section.set_range(0, duration_frames)

    binding.set_display_name(cache.get_name())
    return True, f"geo cache track for {cache.get_name()}", duration_frames


def add_camera(sequence, camera_fbx_path, camera_name, duration_frames=0):
    """
    Spawn a CineCamera into the sequence, add a Camera Cut track sized to
    the shot, and import the camera FBX onto it with match_by_name_only
    disabled. Returns (ok, message).
    """
    # Spawnable CineCamera with focus disabled (spawn temp actor, configure,
    # build spawnable from it, destroy temp)
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

    # Camera Cut track bound to the camera, covering the whole shot
    cut_track = sequence.add_track(unreal.MovieSceneCameraCutTrack)
    cut_section = cut_track.add_section()
    if duration_frames > 0:
        cut_section.set_range(0, duration_frames)
    binding_id = unreal.MovieSceneObjectBindingID()
    try:
        binding_id = sequence.get_binding_id(binding)        # UE 5.4+
    except Exception:
        binding_id = sequence.make_binding_id(binding, unreal.MovieSceneObjectBindingSpace.LOCAL)
    cut_section.set_camera_binding_id(binding_id)

    # Import the FBX animation onto the camera binding
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

    return True, f"camera '{camera_name}' imported from {os.path.basename(camera_fbx_path)}"


# ─── MAIN ────────────────────────────────────────────────────────────────────

def run(project_name="", camera_folder="", shot_filter="", dry_run=False, fps=SEQUENCE_FPS,
        overwrite=False, interactive_shots=False):
    """
    Build Level Sequences for shots in the chosen project.

      project_name      blank → open Unreal project if folder exists under Production
      camera_folder     disk path from the widget (use Find Camera Folder button)
      shot_filter       optional: "Shot01" or "Shot01,Shot05" (ignored when interactive_shots=True)
      interactive_shots True  → checkbox dialog to pick shots (all checked by default)
      dry_run           True  → log the full build plan without creating anything
      fps               24, 30, or 60 (default 24)
      overwrite         True  → delete and rebuild existing sequences (asks to confirm first)
    """
    sep = "=" * 60

    if fps not in (24, 30, 60):
        unreal.log_warning(f"Unusual fps value '{fps}' — using it anyway (expected 24, 30, or 60)")

    # ── Resolve project ──────────────────────────────────────────────────────
    projects = list_project_folders()
    if not projects:
        unreal.log_error(f"No project folders found under {PROJECT_ROOT}")
        return

    project = resolve_production_project(project_name, projects)
    if not project:
        ue_default = get_open_project_name()
        project = ask_choice(projects, default=ue_default)
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
            "No camera folder set — click Find Camera Folder first, or paste a path "
            "into the Camera Folder field. Sequences will be built without cameras."
        )
    elif os.path.isdir(cam_folder):
        camera_files = [f for f in os.listdir(cam_folder) if _CAMERA_FBX_RE.match(f)]
    else:
        unreal.log_error(f"Camera folder does not exist: {cam_folder}")
        return

    # ── Discover shots ───────────────────────────────────────────────────────
    all_shots = list_shot_folders(project)
    shots = resolve_shots(all_shots, shot_filter=shot_filter, interactive=interactive_shots)

    if not shots:
        unreal.log_warning(
            f"No shots selected for project '{project}'"
            + (f" (filter: '{shot_filter}')" if shot_filter and not interactive_shots else "")
        )
        return

    # ── Overwrite confirmation ───────────────────────────────────────────────
    existing = [
        s for s in shots
        if unreal.EditorAssetLibrary.does_asset_exist(
            f"{PROJECT_ROOT}/{project}/{s}/{sequence_name_for(s, project)}"
        )
    ]

    if overwrite and existing and not dry_run:
        confirmed = confirm_dialog(
            f"Are you sure you want to OVERWRITE {len(existing)} existing "
            f"level sequence(s) in '{project}'?\n\n"
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
        unreal.log(f"Overwrite : ON — {len(existing)} existing sequence(s) will be rebuilt")
    if dry_run:
        unreal.log("Mode    : DRY RUN — nothing will be created")
    unreal.log(sep)

    counts = {"built": 0, "skipped": 0, "errors": 0}
    missing_cameras = []   # shots that have assets but no camera FBX
    empty_folders   = []   # shots whose Animation folder has nothing usable

    for shot in shots:
        shot_folder   = f"{PROJECT_ROOT}/{project}/{shot}"
        seq_name      = sequence_name_for(shot, project)
        seq_path      = f"{shot_folder}/{seq_name}"

        unreal.log(f"\n  {shot}")

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
                unreal.log(f"    [DRY RUN]   + anim track    : {a.rsplit('/', 1)[-1]}")
            for c in caches:
                unreal.log(f"    [DRY RUN]   + geo cache     : {c.rsplit('/', 1)[-1]}")
            if camera_fbx:
                unreal.log(f"    [DRY RUN]   + camera        : {camera_name_for(camera_fbx)} (match_by_name_only=False)")
            else:
                unreal.log(f"    [DRY RUN]   ! no camera FBX — sequence without Camera Cut track")
            counts["built"] += 1
            continue

        # ── Real build ───────────────────────────────────────────────────────
        try:
            sequence = create_level_sequence(shot_folder, seq_name, fps)
            if sequence is None:
                unreal.log_error(f"    ✗ Could not create sequence {seq_path}")
                counts["errors"] += 1
                continue

            longest_frames = 0

            for anim_package in anims:
                ok, msg, frames = add_anim_track(sequence, anim_package)
                if ok:
                    unreal.log(f"    ✓ {msg}")
                    longest_frames = max(longest_frames, frames)
                else:
                    unreal.log_warning(f"    ! anim skipped — {msg}")

            for cache_package in caches:
                ok, msg, frames = add_geocache_track(sequence, cache_package)
                if ok:
                    unreal.log(f"    ✓ {msg}")
                    longest_frames = max(longest_frames, frames)
                else:
                    unreal.log_warning(f"    ! geo cache skipped — {msg}")

            if camera_fbx:
                fbx_path = f"{cam_folder}/{camera_fbx}"
                ok, msg = add_camera(sequence, fbx_path, camera_name_for(camera_fbx), longest_frames)
                if ok:
                    unreal.log(f"    ✓ {msg}")
                else:
                    unreal.log_warning(f"    ! camera failed — {msg}")
            else:
                unreal.log_warning(f"    ! no camera FBX for {shot} — built without Camera Cut track")

            # Playback range = longest animation in the shot
            if longest_frames > 0:
                sequence.set_playback_start(0)
                sequence.set_playback_end(longest_frames)
                unreal.log(f"    ✓ playback range: 0–{longest_frames} frames ({fps} fps)")

            unreal.EditorAssetLibrary.save_asset(seq_path)
            unreal.log(f"    ✓ Created {seq_path}")
            counts["built"] += 1

        except Exception as exc:
            unreal.log_error(f"    ✗ Error building {shot}: {exc}")
            counts["errors"] += 1

    unreal.log(f"\n{sep}")
    unreal.log(
        f"Done — Built: {counts['built']}  "
        f"Skipped: {counts['skipped']}  "
        f"Errors: {counts['errors']}"
    )

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

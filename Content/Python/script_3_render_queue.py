# script_3_render_queue.py
#
# Clear Movie Render Queue and add every main shot Level Sequence for a project.
# Excludes *_Lighting and the project master sequence.
#
# From the Unreal Python console (plugin enabled):
#   import script_3_render_queue
#   script_3_render_queue.run(project_name="MyProject")

import importlib
import unreal

import pipeline_common
importlib.reload(pipeline_common)
from pipeline_common import (
    resolve_production_project_choice,
    list_production_projects,
    normalize_project_name,
    match_production_folder,
)

import script_2_sequence as s2
importlib.reload(s2)


def list_main_shot_sequence_paths(project):
    """
    Return sorted (shot_name, sequence_path) for main shot Level Sequences only.
    Skips lighting and master assets. Supports legacy Shot## names (no _Project).
    """
    entries = []
    for shot in s2.list_shot_folders(project):
        seq_path = s2.find_main_shot_sequence_path(project, shot)
        if seq_path:
            entries.append((shot, seq_path))
    return entries


def package_path_to_soft_path(package_path):
    """Turn /Game/Folder/Asset into /Game/Folder/Asset.Asset for MRQ."""
    package_path = str(package_path).split(".")[0]
    asset_name = package_path.rsplit("/", 1)[-1]
    return unreal.SoftObjectPath(f"{package_path}.{asset_name}")


def soft_path_from_sequence(sequence, package_path):
    """Best SoftObjectPath for a loaded Level Sequence asset."""
    if sequence is not None:
        for getter in ("get_path_name", "get_full_name"):
            method = getattr(sequence, getter, None)
            if method is None:
                continue
            try:
                raw = str(method())
                if raw:
                    # /Script/Engine.LevelSequence'/Game/Path/Asset.Asset'
                    if "'" in raw:
                        raw = raw.split("'")[1]
                    if raw.startswith("/Game/"):
                        return unreal.SoftObjectPath(raw)
            except Exception:
                continue
    return package_path_to_soft_path(package_path)


def _get_movie_pipeline_queue_subsystem():
    for cls_name in ("MoviePipelineQueueSubsystem", "EditorMoviePipelineQueueSubsystem"):
        cls = getattr(unreal, cls_name, None)
        if cls is None:
            continue
        try:
            subsystem = unreal.get_editor_subsystem(cls)
            if subsystem is not None:
                return subsystem
        except Exception:
            continue
    return None


def clear_render_queue(queue):
    """Remove all jobs from the Movie Render Queue."""
    for method_name in ("delete_all_jobs", "clear_queue"):
        method = getattr(queue, method_name, None)
        if method is None:
            continue
        try:
            method()
            return True
        except Exception:
            continue

    try:
        jobs = list(queue.get_jobs())
    except Exception:
        jobs = []

    for job in jobs:
        for method_name in ("delete_job", "remove_job"):
            method = getattr(queue, method_name, None)
            if method is None:
                continue
            try:
                method(job)
                break
            except Exception:
                continue
    return True


def _soft_path_for_current_map():
    """Best-effort SoftObjectPath for the level open in the editor."""
    candidates = []

    try:
        editor_paths = getattr(unreal, "EditorLoadingAndSavingUtils", None)
        if editor_paths is not None:
            for method_name in (
                "get_current_map_package_path",
                "get_editor_world_package_path",
            ):
                method = getattr(editor_paths, method_name, None)
                if method is None:
                    continue
                try:
                    package_path = method()
                    if package_path:
                        candidates.append(str(package_path))
                except Exception:
                    continue
    except Exception:
        pass

    try:
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        if world is not None:
            path = unreal.SystemLibrary.get_path_name(world)
            if path:
                candidates.append(str(path).split(".")[0])
    except Exception:
        pass

    for raw in candidates:
        raw = str(raw).split(".")[0]
        if raw.startswith("/Game/"):
            if "." not in raw.rsplit("/", 1)[-1]:
                asset_name = raw.rsplit("/", 1)[-1]
                return unreal.SoftObjectPath(f"{raw}.{asset_name}")
            return unreal.SoftObjectPath(raw)

    return None


def _initialize_job_configuration(job):
    try:
        config = job.get_configuration()
        if config is not None and hasattr(config, "initialize_transient_settings"):
            config.initialize_transient_settings()
    except Exception:
        pass


def _apply_job_fields(job, label, map_soft_path, sequence_soft_path):
    """Set MRQ job fields using direct attrs and editor properties."""
    if label:
        for attr in ("job_name",):
            if hasattr(job, attr):
                setattr(job, attr, label)
        try:
            job.set_editor_property("job_name", label)
        except Exception:
            pass

    for prop, value in (("map", map_soft_path), ("sequence", sequence_soft_path)):
        if value is None:
            continue
        if hasattr(job, prop):
            setattr(job, prop, value)
        try:
            job.set_editor_property(prop, value)
        except Exception:
            pass


def add_sequence_job(queue, sequence_path, job_label="", map_soft_path=None):
    """
    Allocate one MRQ job for a Level Sequence. Uses the current editor map.
    Returns the job on success, or None.
    """
    sequence = s2.get_or_load_sequence(sequence_path)
    if sequence is None:
        unreal.log_warning(f"  ! Could not load sequence asset: {sequence_path}")
        return None

    map_soft_path = map_soft_path or _soft_path_for_current_map()
    if map_soft_path is None or not str(map_soft_path):
        unreal.log_error(
            "  ! No editor level open — open your render map, then try again."
        )
        return None

    sequence_soft_path = soft_path_from_sequence(sequence, sequence_path)
    label = job_label or sequence_path.rsplit("/", 1)[-1]

    editor_lib = getattr(unreal, "MoviePipelineEditorLibrary", None)
    if editor_lib is not None and hasattr(editor_lib, "create_job_from_sequence"):
        try:
            job = editor_lib.create_job_from_sequence(queue, sequence)
            if job is not None:
                _initialize_job_configuration(job)
                _apply_job_fields(job, label, map_soft_path, sequence_soft_path)
                unreal.log(
                    f"  + MRQ job '{label}'  map={map_soft_path}  seq={sequence_soft_path}"
                )
                return job
        except Exception as exc:
            unreal.log_warning(f"  create_job_from_sequence failed for {label}: {exc}")

    try:
        job = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
    except Exception as exc:
        unreal.log_warning(f"  allocate_new_job failed for {label}: {exc}")
        return None

    _initialize_job_configuration(job)
    _apply_job_fields(job, label, map_soft_path, sequence_soft_path)
    unreal.log(f"  + MRQ job '{label}'  map={map_soft_path}  seq={sequence_soft_path}")
    return job


def open_movie_render_queue_ui():
    """Bring the Movie Render Queue window to the front if possible."""
    editor_lib = getattr(unreal, "MoviePipelineEditorLibrary", None)
    if editor_lib is None:
        return

    for method_name in (
        "open_movie_render_queue",
        "open_movie_pipeline_queue",
        "load_movie_render_queue",
    ):
        method = getattr(editor_lib, method_name, None)
        if method is None:
            continue
        try:
            method()
            unreal.log("Opened Movie Render Queue window.")
            return
        except Exception:
            continue


def run(project_name="", dry_run=False, interactive=False):
    """
    Clear Movie Render Queue and add all main shot sequences for the project.

      project_name  production folder under /Game/Production/
                    from widget: pass SequenceProjectCombo selection
      dry_run       log the plan without touching MRQ
      interactive   open project picker when project_name is blank (console)
    """
    sep = "=" * 60
    unreal.log(f"Script 3 — starting (project_name={project_name!r})")

    projects = list_production_projects()
    if not projects:
        unreal.log_error(f"No project folders found under {s2.PROJECT_ROOT}")
        return -1

    explicit = normalize_project_name(project_name)
    project = resolve_production_project_choice(
        explicit,
        projects,
        interactive=interactive and not explicit,
    )

    if explicit and project not in projects:
        matched = match_production_folder(explicit, projects)
        if matched:
            project = matched
        else:
            unreal.log_error(
                f"Project '{explicit}' not found under {s2.PROJECT_ROOT}. "
                f"Available: {', '.join(projects)}"
            )
            return -1

    if not project:
        unreal.log_error(
            "No production project selected. "
            f"Available: {', '.join(projects)}. "
            "Select a project in the widget dropdown before clicking Add to Render Queue."
        )
        return -1

    if project not in projects:
        unreal.log_error(f"Project '{project}' not found under {s2.PROJECT_ROOT}.")
        return -1

    shot_entries = list_main_shot_sequence_paths(project)
    if not shot_entries:
        unreal.log_warning(
            f"No main shot sequences found for project '{project}'. "
            "Check /Game/Production/{project}/Shot##/ for Level Sequence assets."
        )
        return 0

    map_soft_path = _soft_path_for_current_map()
    if map_soft_path is None and not dry_run:
        unreal.log_error(
            "No editor level is open. Open the level you render from, then click the button again."
        )
        return -1

    unreal.log(f"\n{sep}")
    unreal.log("Script 3 — Add Shots to Movie Render Queue")
    unreal.log(f"Project : {project}")
    unreal.log(f"Map     : {map_soft_path}")
    unreal.log(f"Shots   : {len(shot_entries)}")
    unreal.log(f"Mode    : {'DRY RUN' if dry_run else 'CLEAR queue + ADD jobs'}")
    unreal.log(sep)

    for shot, seq_path in shot_entries:
        seq_label = seq_path.rsplit("/", 1)[-1]
        canonical = s2.sequence_name_for(shot, project)
        legacy_note = " (legacy name)" if seq_label != canonical else ""
        unreal.log(f"  {shot} → {seq_label}{legacy_note}")

    if dry_run:
        unreal.log(f"\n{sep}\nDone — DRY RUN ({len(shot_entries)} jobs would be added)\n{sep}\n")
        return len(shot_entries)

    subsystem = _get_movie_pipeline_queue_subsystem()
    if subsystem is None:
        unreal.log_error(
            "Movie Render Queue subsystem not found. "
            "Enable the Movie Render Queue plugin and restart the editor."
        )
        return -1

    queue = subsystem.get_queue()
    clear_render_queue(queue)

    added = 0
    errors = 0
    for shot, seq_path in shot_entries:
        job = add_sequence_job(
            queue,
            seq_path,
            job_label=s2.sequence_name_for(shot, project),
            map_soft_path=map_soft_path,
        )
        if job is None:
            errors += 1
        else:
            added += 1

    try:
        queued_count = len(queue.get_jobs())
    except Exception:
        queued_count = added

    unreal.log(f"\n{sep}")
    unreal.log(f"Done — Cleared queue, added {added} job(s), errors {errors}")
    unreal.log(f"MRQ queue reports {queued_count} job(s)")
    if queued_count == 0 and added > 0:
        unreal.log_warning(
            "Jobs were created but the queue is empty — check Output Log for map/sequence errors."
        )
    unreal.log("Window → Cinematics → Movie Render Queue")
    unreal.log(f"{sep}\n")

    open_movie_render_queue_ui()
    return added if errors == 0 else -1


if __name__ == "__main__":
    run()

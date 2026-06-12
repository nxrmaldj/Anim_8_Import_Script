# Script 2 — Level Sequence Builder · Agreed Design

Decisions locked in on 2026-06-11. This is the build spec for `script_2_sequence.py`.

---

## Run Flow

1. **Project selector** — scan `/Game/Production/` and list every project folder found. A dialog (later: widget dropdown) lets the user pick which project to build sequences for. Multiple projects in the production folder is the normal state — the same level is reused for many content pieces.
2. **Camera folder picker** — a folder picker opens pointing at the Maya export folder on disk. The script scans it for `Shot##_Camera_anim.fbx` files and matches them to shots by name.
3. **Shot discovery** — every `Shot##` folder under the chosen project is processed automatically. No typing shot numbers.
4. **Build each sequence** (details below).
5. **Summary log** — sequences created, skipped, warnings (missing cameras, unmatched assets).

## Per-Shot Build Steps

| Step | Behavior |
|---|---|
| Sequence asset | `Shot##_{ProjectName}` created directly in `Shot##/` |
| Skip rule | If a Level Sequence with that exact name already exists in the folder → **skip the shot entirely** (no overwrite, same philosophy as Script 1) |
| Skeletal Mesh tracks | One binding + animation track per `AnimSequence` found in `Shot##/Animation/`. The skeleton is looked up **from the AnimSequence asset itself** — no KNOWN_CHARACTERS dict |
| Geometry Cache tracks | One track per `GeometryCache` asset in `Shot##/Animation/` |
| Camera actor | Spawn a CineCamera Actor named after the camera FBX with `_anim` stripped (`Shot01_Camera_anim.fbx` → `Shot01_Camera`) |
| Camera Cut track | Added to the sequence, bound to the CineCamera |
| Camera FBX import | Imported into the sequence with **Match by Camera Name Only = OFF** (`MovieSceneUserImportFBXSettings.match_by_name_only = False`) — naming is cosmetic, not a requirement for the import to succeed |
| Missing camera FBX | Sequence still builds without a Camera Cut track; warning logged |

## Key Differences from the Original Spec (UE_Import_Pipeline_Spec.docx)

- **No KNOWN_CHARACTERS** — skeleton binding comes from each AnimSequence directly
- **No typed SHOT_NUMBER** — all shots build automatically in one run
- **No typed project name** — picked from a list of folders found in `/Game/Production/`
- **Match by name disabled** on camera import (was a hard requirement in the spec)
- Workflow assumes Script 1 (staging organizer) has already routed assets into shot folders

## Entry Point (widget-ready, mirrors Script 1)

```python
def run(project_name="", camera_folder="", dry_run=False):
    # project_name  blank → selection dialog listing /Game/Production/ folders
    # camera_folder blank → folder picker
    # dry_run       True  → log the full build plan without creating anything
```

# Editor Utility Widget — Build Guide

Layout and wiring reference for the Anim8 Pipeline widget. One widget, two
sections: **Organize Staging** (Script 1) and **Build Sequences** (Script 2).

---

## Designer Layout

```
┌─ Anim8 Pipeline ──────────────────────────────┐
│                                               │
│  ── 1 · Organize Staging ──────────────────   │
│  Project Name   [____________________]        │  ← optional: blank = open UE project
│  [ ] Dry Run                                  │
│  [        Organize Staging        ]           │
│                                               │
│  ── 2 · Build Level Sequences ─────────────   │
│  Project Name   [____________________]        │  ← optional: blank = open UE project
│  Camera Folder  [____________________]        │
│  [x] All Shots                                │  ← unchecked → checkbox picker on Run
│  FPS            [ 24 ▼ ]                      │
│  [ ] Dry Run                                  │
│  [ ] Overwrite Existing                       │
│  [       Build Sequences        ]             │
│                                               │
└───────────────────────────────────────────────┘
```

## Widgets to Create (tick "Is Variable" on every one)

### Section 1 — Organize Staging (Script 1)

| Widget type | Variable name | Notes |
|---|---|---|
| Editable Text Box | `OrganizeProjectInput` | Optional — blank uses the open `.uproject` name |
| Check Box | `OrganizeDryRunCheckbox` | Unchecked by default |
| Button | `OrganizeRunButton` | Fires Script 1 |

### Section 2 — Build Sequences (Script 2)

| Widget type | Variable name | Notes |
|---|---|---|
| Editable Text Box | `SequenceProjectInput` | Optional — blank uses open UE project if folder exists; else picker |
| Editable Text Box | `CameraFolderInput` | Optional — blank opens folder picker |
| Check Box | `AllShotsCheckbox` | **Checked by default** — unchecked opens shot checkbox dialog on Run |
| Combo Box (String) | `FpsCombo` | Options: `24`, `30`, `60`. Default `24` |
| Check Box | `SequenceDryRunCheckbox` | Unchecked by default |
| Check Box | `OverwriteCheckbox` | **Unchecked by default** — Python still asks "Are you sure?" |
| Button | `SequenceRunButton` | Fires Script 2 |

---

## Graph Wiring

### Button 1 — OrganizeRunButton → OnClicked

Build this string (Format Text node) and send it to **Execute Python Command**:

```
import sys; sys.path.append("A:/Anim_8_Scripts"); import script_1_organize, importlib; importlib.reload(script_1_organize); script_1_organize.run(project_name="{project}", dry_run={dry})
```

Pin wiring:

| Format pin | Source |
|---|---|
| `project` | `OrganizeProjectInput` → Get Text → To String |
| `dry` | `OrganizeDryRunCheckbox` → Is Checked → Select String (A=`True`, B=`False`) |

### Button 2 — SequenceRunButton → OnClicked

```
import sys; sys.path.append("A:/Anim_8_Scripts"); import script_2_sequence, importlib; importlib.reload(script_2_sequence); script_2_sequence.run(project_name="{project}", camera_folder="{camfolder}", dry_run={dry}, fps={fps}, overwrite={ow}, interactive_shots={pick})
```

Pin wiring:

| Format pin | Source |
|---|---|
| `project` | `SequenceProjectInput` → Get Text → To String |
| `camfolder` | `CameraFolderInput` → Get Text → To String |
| `fps` | `FpsCombo` → Get Selected Option |
| `dry` | `SequenceDryRunCheckbox` → Is Checked → Select String (A=`True`, B=`False`) |
| `ow` | `OverwriteCheckbox` → Is Checked → Select String (A=`True`, B=`False`) |
| `pick` | `AllShotsCheckbox` → Is Checked → Select String **Pick A** pin. A=`False`, B=`True` (checked = all shots, unchecked = open picker) |

---

## Behavior Notes

**All Shots checkbox → `{pick}` pin (no NOT node needed):**

```
AllShotsCheckbox → Is Checked ──► Select String (Pick A)
                                  A = False
                                  B = True
                                  Return Value → {pick}
```

- Checkbox **checked** → Pick A → `False` → build all shots
- Checkbox **unchecked** → Pick B → `True` → opens the shot checkbox dialog

Add a **Select String** node (same type you used for Dry Run). Set **A** to `False` and **B** to `True`. Plug **Is Checked** into **Pick A** — when the box is checked, Pick A is true and you get `False`; when unchecked, you get `True`.

Do **not** use "Invert Select Mesh" — that is unrelated.
- **Blank project name** uses the **open Unreal project name** (your `.uproject`
  file). Script 1 always uses it for `/Game/Production/{name}/`. Script 2 uses
  it only if that folder already exists under Production; otherwise the
  production-folder picker opens (with the UE project pre-selected if listed).
- **Overwrite checkbox** only arms the option — the Python script still shows
  the "Are you sure you want to OVERWRITE N sequences?" Yes/No prompt before
  deleting anything.
- **Select String capitalization matters**: `True` / `False` (Python booleans).
- **importlib.reload** in both commands means every click reads the latest
  script from disk — script updates apply without restarting the editor.
- **Camera folder paths**: forward slashes are safest
  (`G:/Shared drives/...`). Backslashes typed into the text box will reach
  Python inside double quotes, so they generally survive — but forward
  slashes never bite.

## Reference — full Python signatures

```python
script_1_organize.run(staging_path=None, project_name="", dry_run=None)

script_2_sequence.run(project_name="", camera_folder="", shot_filter="",
                      dry_run=False, fps=24, overwrite=False, interactive_shots=False)
```

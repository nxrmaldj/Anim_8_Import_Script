# Anim8 Pipeline — Editor Utility Widget Guide

Complete reference for building and wiring the pipeline widget in Unreal Engine.

---

## What This Widget Does

| Section | Script | Purpose |
|---|---|---|
| **Organize Staging** | `script_1_organize.py` | Moves assets from `/Game/Staging` into production folders |
| **Build Sequences** | `script_2_sequence.py` | Builds Level Sequences per shot (anims, geo caches, cameras) |

**Typical workflow:**
1. TA imports FBX/ABC into `/Game/Staging` using Unreal's normal import window
2. Run **Organize Staging** → assets move to `/Game/Production/{Project}/Shot##/Animation/`
3. Click **Find Camera Folder** → pick the Maya export folder on disk
4. Run **Build Sequences** → Level Sequences are created per shot

---

## Before You Start

**Required plugins (Edit → Plugins):**
- Python Editor Script Plugin — **enabled**
- Editor Scripting Utilities — **enabled** (if available in your UE version)

**Required folders in Content Browser:**
- `/Game/Staging` — TA imports everything here first
- `/Game/Production/` — script creates `{ProjectName}/Shot##/` under here

**Scripts location (for now):**
- `A:/Anim_8_Scripts/` — hardcoded in the widget until the plugin restructure
- After plugin packaging, remove the `sys.path.append(...)` lines from both commands

---

## Step 1 — Create the Widget Asset

1. Content Browser → right-click → **Editor Utilities → Editor Utility Widget**
2. Name it e.g. `EUW_Anim8Pipeline`
3. Open it → you get **Designer** (layout) and **Graph** (logic) tabs

---

## Step 2 — Designer Layout

Build this layout in the **Designer** tab. Use Text blocks for section headers if you want.

```
┌─ Anim8 Pipeline ──────────────────────────────┐
│                                               │
│  ── 1 · Organize Staging ──────────────────   │
│  Project Name   [____________________]        │
│  [ ] Dry Run                                  │
│  [        Organize Staging        ]           │
│                                               │
│  ── 2 · Build Level Sequences ─────────────   │
│  Project Name   [____________________]        │
│  Camera Folder  [____________________]        │
│  [ Find Camera Folder ]                       │
│  [x] All Shots                                │
│  FPS            [ 24 ▼ ]                      │
│  [ ] Dry Run                                  │
│  [ ] Overwrite Existing                       │
│  [       Build Sequences        ]             │
│                                               │
└───────────────────────────────────────────────┘
```

---

## Step 3 — Widget Checklist

For **every** control below: select it in Designer → Details panel → tick **Is Variable** (top-right). The variable name must match exactly.

### Section 1 — Organize Staging

| Widget | Variable name | Default |
|---|---|---|
| Editable Text Box | `OrganizeProjectInput` | empty |
| Check Box | `OrganizeDryRunCheckbox` | unchecked |
| Button | `OrganizeRunButton` | label: "Organize Staging" |

### Section 2 — Build Sequences

| Widget | Variable name | Default |
|---|---|---|
| Editable Text Box | `SequenceProjectInput` | empty |
| Editable Text Box | `CameraFolderInput` | empty, **read-only look** (filled by Find button) |
| Button | `FindCameraFolderButton` | label: "Find Camera Folder" |
| Check Box | `AllShotsCheckbox` | **checked** |
| Combo Box (String) | `FpsCombo` | options: `24`, `30`, `60` — default `24` |
| Check Box | `SequenceDryRunCheckbox` | unchecked |
| Check Box | `OverwriteCheckbox` | **unchecked** |
| Button | `SequenceRunButton` | label: "Build Sequences" |

---

## Step 4 — One-Time Setup Per Editor Session

Before wiring **Find Camera Folder**, run this **once** in the Python console so the Blueprint node appears:

```python
import sys; sys.path.append("A:/Anim_8_Scripts"); import anim8_tools
```

Then in the Graph tab, right-click → search **`Browse Camera Export Folder`**.

### What is "Browse Camera Export Folder"?

It is a **Blueprint node** created by `anim8_tools.py`. It is **not** something built into Unreal by default.

| | |
|---|---|
| **What it does** | Opens a Windows folder picker (same dialog the script uses) |
| **What it returns** | The selected folder path as a **String** (e.g. `G:/Shared drives/.../Export`) |
| **Where to find it** | Right-click in Graph → search `Browse Camera` or look under category **Anim8 Pipeline** |
| **If you can't find it** | Run the Python import above, then search again. Restart the widget editor if needed. |

You wire its **Return Value** into the Camera Folder text box — no Execute Python Command on this button.

---

## Step 5 — Graph Wiring

Switch to the **Graph** tab. You will wire **three buttons**.

### Pattern: Checkbox → Python boolean (used 4 times)

Every checkbox that feeds Python uses a **Select String** node:

```
SomeCheckbox → Is Checked → Select String (Pick A)
                              A = True    (or False for All Shots — see below)
                              B = False   (or True for All Shots)
                              Return Value → Format Text pin
```

**Capitalization matters** — Python expects `True` and `False`, not `true`/`false`.

| Checkbox | Select String A | Select String B | Feeds pin |
|---|---|---|---|
| OrganizeDryRunCheckbox | `True` | `False` | `{dry}` (Script 1) |
| SequenceDryRunCheckbox | `True` | `False` | `{dry}` (Script 2) |
| OverwriteCheckbox | `True` | `False` | `{ow}` |
| AllShotsCheckbox | **`False`** | **`True`** | `{pick}` — **opposite** of the others |

**All Shots logic (no NOT node needed):**
- Checked → `False` → build **all** shots
- Unchecked → `True` → opens **shot checkbox dialog** on Run

Do **not** use "Invert Select Mesh" — that is unrelated.

---

### Button 1 — OrganizeRunButton

**Event:** select `OrganizeRunButton` → Details → Events → **+ On Clicked**

**Chain:**

```
On Clicked (OrganizeRunButton) ──exec──► Execute Python Command
                                              ▲
Format Text → To String ──────────────────────┘
```

**Format Text — paste this entire line into the Format field:**

```
import sys; sys.path.append("A:/Anim_8_Scripts"); import script_1_organize, importlib; importlib.reload(script_1_organize); script_1_organize.run(project_name="{project}", dry_run={dry})
```

**Pin wiring:**

| Format pin | Connect from |
|---|---|
| `{project}` | `OrganizeProjectInput` → **Get Text** → **To String (Text)** |
| `{dry}` | `OrganizeDryRunCheckbox` → **Is Checked** → **Select String** (A=`True`, B=`False`) |

---

### Button 2 — FindCameraFolderButton

Use **Plan B** if you cannot find **Browse Camera Export Folder** in the graph search
(most common when scripts live on `A:/` instead of inside the project).

**Delete any wrong nodes** such as `Sync Browser to Folders` or `Get Camera Param Option` —
those are unrelated Unreal nodes, not part of this pipeline.

---

#### Plan B — Execute Python Command (recommended)

```
On Clicked (FindCameraFolderButton) ──exec──► Execute Python Command
```

**Python Command** — paste this single line:

```
import sys; sys.path.append("A:/Anim_8_Scripts"); import pipeline_common as pc, importlib; importlib.reload(pc); pc.browse_camera_folder()
```

What happens:
1. Folder picker opens
2. Script remembers the path for **Build Sequences**
3. Output Log shows: `Camera export folder set: G:/your/path`

**Optional:** copy that path from the log into **Camera Folder** text box so you can see it in the UI.
Build Sequences works either way — text box **or** last picked folder.

---

#### Plan A — Browse Camera Export Folder node (optional)

Only works if Unreal registers the Python Blueprint library.

**One-time per session** — Python console:

```python
import sys; sys.path.append("A:/Anim_8_Scripts"); import anim8_tools
```

Then search the graph for **`Browse Camera Export Folder`** (category: **Anim8 Pipeline**).

```
On Clicked → Browse Camera Export Folder → Conv String to Text → Set Text (CameraFolderInput)
```

**To make Plan A appear every launch:** copy `anim8_tools.py` and `pipeline_common.py`
into your project's `Content/Python/` folder and restart the editor.

---

### Button 3 — SequenceRunButton

**Event:** `SequenceRunButton` → **On Clicked**

**Chain:**

```
On Clicked (SequenceRunButton) ──exec──► Execute Python Command
                                              ▲
Format Text → To String ──────────────────────┘
```

**Format Text — paste this entire line into the Format field:**

```
import sys; sys.path.append("A:/Anim_8_Scripts"); import script_2_sequence, importlib; importlib.reload(script_2_sequence); script_2_sequence.run(project_name="{project}", camera_folder="{camfolder}", dry_run={dry}, fps={fps}, overwrite={ow}, interactive_shots={pick})
```

**Pin wiring:**

| Format pin | Connect from |
|---|---|
| `{project}` | `SequenceProjectInput` → **Get Text** → **To String (Text)** |
| `{camfolder}` | `CameraFolderInput` → **Get Text** → **To String (Text)** |
| `{fps}` | `FpsCombo` → **Get Selected Option** |
| `{dry}` | `SequenceDryRunCheckbox` → **Is Checked** → **Select String** (A=`True`, B=`False`) |
| `{ow}` | `OverwriteCheckbox` → **Is Checked** → **Select String** (A=`True`, B=`False`) |
| `{pick}` | `AllShotsCheckbox` → **Is Checked** → **Select String** (A=`False`, B=`True`) |

---

## Step 6 — Compile, Save, Run

1. **Compile** the widget (Compile button top-left)
2. **Save**
3. Content Browser → right-click widget → **Run Editor Utility Widget**
4. Dock the panel wherever you like (Outliner, Details, etc.)

---

## How to Use (Operator Guide)

### Organize Staging
1. Import assets into `/Game/Staging`
2. Leave **Project Name** blank (uses open `.uproject` name) or type override
3. Check **Dry Run** first to preview moves in Output Log
4. Uncheck Dry Run → click **Organize Staging**
5. Right-click Staging → **Fix Up Redirectors**

### Build Sequences
1. Click **Find Camera Folder** → select Maya export folder (`Shot##_cam.fbx` files)
2. Confirm path appears in **Camera Folder** text box
3. Leave **Project Name** blank (auto-detect) or pick from dialog if multiple production folders
4. **All Shots** checked = build everything; unchecked = checkbox dialog to pick shots
5. Set **FPS** (24 / 30 / 60)
6. Check **Dry Run** → click **Build Sequences** → review log + health check
7. Uncheck Dry Run → run for real
8. **Overwrite Existing** — only when rebuilding; Python asks "Are you sure?" before deleting sequences

---

## Output Log — What to Expect

**Script 1 dry run:**
```
[DRY RUN] Would move → /Game/Production/MyProject/Shot01/Animation/Shot01_Kiiboh_anim
```

**Script 2 summary (end of run):**
```
Done — Built: 38  Skipped: 4  Errors: 0
Cameras missing : 2  (Shot07, Shot19)
Empty folders   : 0
```

**Harmless warning (camera still imports):**
```
failed to find any matching camera for Shot##
```
Unreal tries a name match first, then imports onto the spawnable anyway. Safe to ignore.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Can't find **Browse Camera Export Folder** | Run `import anim8_tools` in Python console (Step 4). Reopen widget Graph. |
| **Execute Python Command** node missing | Enable Python Editor Script Plugin, restart editor |
| Button does nothing | Check white **exec** wire: On Clicked → Execute Python Command |
| Python error on Run | Window → Developer Tools → **Output Log** — read the red error |
| `No camera folder set` | Click **Find Camera Folder** before Build Sequences |
| Wrong production folder | Type project name in text box, or pick from dialog when multiple exist |
| Script changes not applying | `importlib.reload` in Format Text handles this — recompile widget if you changed the command string |
| Checkbox values wrong | Select String must use `True`/`False` with capital T and F |

---

## Future: Plugin Packaging

When scripts move into a content-only plugin (`Plugins/Anim8Pipeline/Content/Python/`):

1. Remove `sys.path.append("A:/Anim_8_Scripts");` from both Format Text commands
2. Commands become:
   ```
   import script_1_organize, importlib; importlib.reload(script_1_organize); ...
   ```
3. Copy widget into plugin Content folder — team drops plugin folder into any project

---

## Python Reference (for console testing)

```python
import sys; sys.path.append("A:/Anim_8_Scripts")
import script_1_organize, script_2_sequence

# Script 1
script_1_organize.run(dry_run=True)

# Script 2
script_2_sequence.run(dry_run=True)                              # all shots, dry run
script_2_sequence.run(shot_filter="Shot01", dry_run=False)       # one shot
script_2_sequence.run(dry_run=False, interactive_shots=True)     # shot picker dialog
script_2_sequence.run(dry_run=False, overwrite=True)             # rebuild (asks confirm)
```

**Full signatures:**

```python
script_1_organize.run(staging_path=None, project_name="", dry_run=None)

script_2_sequence.run(
    project_name="",
    camera_folder="",
    shot_filter="",
    dry_run=False,
    fps=24,
    overwrite=False,
    interactive_shots=False,
)
```

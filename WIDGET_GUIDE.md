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
│  Project        [ TestRun          ▼ ]        │  ← dropdown, filled on widget open
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
| Combo Box (String) | `SequenceProjectCombo` | empty — filled automatically on widget open (see Event Construct) |
| Button | `FindCameraFolderButton` | label: "Find Camera Folder" |
| Check Box | `AllShotsCheckbox` | **checked** |
| Combo Box (String) | `FpsCombo` | options: `24`, `30`, `60` — default `24` |
| Check Box | `SequenceDryRunCheckbox` | unchecked |
| Check Box | `OverwriteCheckbox` | **unchecked** |
| Button | `SequenceRunButton` | label: "Build Sequences" |

**Removed from Section 2:** Project Name text box and Camera Folder text box — project is a **dropdown in the widget**, camera path is set by **Find Camera Folder** (stored in memory, no popup on Run).

---

## Step 4 — Load Anim8 Blueprint Nodes

Run this **once per editor session** in the Python console (also required after editor restart):

```python
import sys; sys.path.append("A:/Anim_8_Scripts"); import anim8_tools
```

**Best fix (nodes always available):** copy `anim8_tools.py` and `pipeline_common.py` into your project's **`Content/Python/`** folder and restart the editor.

Nodes you need (category **Anim8 Pipeline**):

| Node | Purpose |
|---|---|
| **Get Production Project Names** | Returns all folders under `/Game/Production/` |
| **Get Suggested Production Project** | Default selection (matches open `.uproject` when possible) |
| **Browse Camera Export Folder** | Optional — use Execute Python for Find button instead |

---

## Step 5 — Event Construct (fill Project dropdown)

**When does this run?** Once, when you open the widget. It scans `/Game/Production/` and fills the Project combo so you never get a popup on Build Sequences.

**Two jobs, in order:**
1. Add every production folder name as a combo option
2. Select the best default (usually the open `.uproject` name)

---

### Reading your graph (word by word)

If your graph looks like **Event Construct → For Each Loop ← Make Array ← Project Name Input**, here is what each piece means:

| Node | What it is | What it does in your graph |
|---|---|---|
| **Event Construct** | Red event node | “The widget just opened — run setup now.” Fires **once** per open. |
| **Project Name Input** | Your old text box variable | One **single string** someone typed (or empty). **Not** a list of all production folders. |
| **Make Array** | Builds an array from pins | Takes that **one** string and wraps it in an array with **one item**. So the loop only ever sees one name — not every folder under `/Game/Production/`. |
| **For Each Loop** | Repeats for each array item | **Exec in** — starts the loop. **Array in** — what to loop over. **Loop Body** — “do this for each item” (**yours is empty — nothing happens**). **Array Element** — the current name (e.g. `TestRun`). **Completed** — “loop finished” (use this for Set Selected Option). |

**What is missing in your screenshot:**
1. Something that lists **all** folders under `/Game/Production/` (not one text box value)
2. **Loop Body** wired to **Add Option** on `SequenceProjectCombo`
3. **Completed** wired to **Set Selected Option**

---

### Pick one method

| Method | When to use |
|---|---|
| **A — Manual combo (easiest)** | One or two projects; skip Event Construct entirely |
| **B — Pure Blueprint (recommended)** | Auto-fill; **no** Anim8 nodes; **no** Execute Python on Construct |
| **C — Anim8 Python nodes** | After copying scripts to `Content/Python/` and restart |

**Can you use Execute Python on Event Construct instead?**  
Not in a useful way. **Execute Python Command** runs a script but **does not return a list back to Blueprint**. You cannot plug it into **For Each Loop → Array**. Python on the **buttons** (Organize / Build Sequences) is correct; Event Construct should use **Blueprint** (Method B) or **manual options** (Method A).

---

### Method A — Manual combo (no Event Construct)

1. Designer → select **SequenceProjectCombo**
2. Details → **Options** → **+** add each project name (`TestRun`, etc.)
3. Set **Default Option** if you want
4. Delete your Event Construct graph (or leave it unwired)

Build Sequences still uses **Get Selected Option → `{project}`** — that part you already wired correctly.

---

### Method B — Pure Blueprint (recommended — use this)

Uses Unreal’s built-in **List Assets** node. No Anim8 nodes. No Execute Python on Event Construct.

**Before you start**
- Edit → Plugins → **Editor Scripting Utilities** → enabled (restart if you just turned it on)
- In Content Browser, confirm `/Game/Production/` has at least one folder (e.g. `TestRun`)
- In your Event Construct graph, **delete** the old **Project Name Input → Make Array** wires (keep Event Construct + For Each Loop if already placed)

---

#### Checklist — wire in this order

**Part 1 — Get the folder list**

| Step | Action |
|---|---|
| 1 | Graph tab → you should have **Event Construct** and **For Each Loop** |
| 2 | Right-click empty space → search **`List Assets`** → pick the one under **Editor Scripting** / **Editor Asset Library** |
| 3 | On **List Assets**, set **Directory Path** = `/Game/Production/` |
| 4 | **Recursive** = **unchecked** (false) |
| 5 | If you see **Include Folder** = **checked** (true) |
| 6 | Drag **Return Value** (purple array) → **For Each Loop → Array** |
| 7 | White wire: **Event Construct** → **Clear Options** on `SequenceProjectCombo` → **For Each Loop** (exec) |
| 8 | Optional: after **Replace**, add **Branch** → Condition = string **Is Not Empty** → only then **Add Option** (skips blank entries) |

**Part 2 — Add each folder name to the combo**

List Assets returns full paths like `/Game/Production/TestRun`. The combo only needs `TestRun`.

**Use Replace (easiest — no Split, no Get Last Array):**

| Step | Action |
|---|---|
| 8 | In **My Blueprint** panel (left), drag **SequenceProjectCombo** into the graph → choose **Add Option** |
| 9 | White wire: **For Each Loop → Loop Body** → **Add Option** (exec) |
| 10 | Right-click → search **`Replace`** (pick the **String** one, not material/replace nodes) |
| 11 | **Replace → Source String** (or **In String**) ← **For Each Loop → Array Element** |
| 12 | **Replace → Search String** (or **From**) = `/Game/Production/` — type it exactly |
| 13 | **Replace → Replace String** (or **To**) = leave **empty** |
| 14 | **Replace → Return Value** → **Add Option → Item** (pink string) |

**Trailing slash?** If the dropdown shows `TestRun/` instead of `TestRun`, add a **second Replace** between the first Replace and **Add Option**:
- **Source String** ← first Replace **Return Value**
- **Search String** = `/`
- **Replace String** = empty
- **Return Value** → **Add Option → Item**

*(Build Sequences also strips trailing slashes in Python — belt and suspenders.)*

<details><summary>Alternative if Replace looks wrong — Parse Into Array + Length + Get</summary>

| Step | Action |
|---|---|
| 10 | Right-click → search **`Parse Into Array`** (not Split String) |
| 11 | **Source String** ← **Array Element** |
| 12 | **Delimiter** pin ← type `/` (forward slash). If no Delimiter pin, drag from **Source String** and search **Parse Into Array** from the context menu instead |
| 13 | Drag from **Parse Into Array → Return Value** (purple) → release → search **`Length`** |
| 14 | **Length → Return Value** → **Subtract** (or **int - int**) → second pin = **`1`** |
| 15 | Drag from **Parse Into Array → Return Value** again → release → search **`Get`** |
| 16 | **Get → Index** ← Subtract result · **Get → Return Value** → **Add Option → Item** |

</details>

**Part 3 — Pre-select a default**

| Step | Action |
|---|---|
| 16 | Drag **SequenceProjectCombo** → choose **Set Selected Option** |
| 17 | White wire: **For Each Loop → Completed** → **Set Selected Option** (exec) |
| 18 | Right-click → search **`Get Game Name`** → **Return Value** → **Set Selected Option → Option** |
| 19 | **Recommended:** skip Get Game Name — use **Set Selected Index** with Index **`0`** wired from **Completed** instead (Get Game Name often does not match any combo option) |

**Part 4 — Finish**

| Step | Action |
|---|---|
| 20 | **Compile** (top-left) → fix any red errors |
| 21 | **Save** |
| 22 | Content Browser → right-click widget → **Run Editor Utility Widget** |
| 23 | Open **Project** dropdown → should show `TestRun` (and any other production folders) |

---

#### What your finished graph should look like

```
Event Construct ──exec──► For Each Loop ◄──array── List Assets (/Game/Production/)
                              │
                    Loop Body ──exec──► Add Option (SequenceProjectCombo)
                              │              ▲
                              │         Item │
                              └── Array Element ──► Replace (/Game/Production/ → "")

                    Completed ──exec──► Set Selected Option (SequenceProjectCombo)
                                              ▲
                                         Option │
                                              └── Get Game Name
```

---

#### If something goes wrong

| Symptom | Fix |
|---|---|
| Can't find **List Assets** | Enable **Editor Scripting Utilities** plugin, restart editor |
| Combo empty after run | **Loop Body** not wired to **Add Option**, or List Assets path wrong |
| Combo shows full paths like `/Game/Production/TestRun` | **Replace** not wired to **Add Option → Item**, or Search String typo |
| Can't find Delimiter / Get Last Array | Use **Replace** instead (Part 2 above) — skip Split entirely |
| Wrong project pre-selected | Use **Set Selected Index 0** instead of Get Game Name |
| Still stuck | Fall back to **Method A** (manual Options on combo in Designer) — see below |

---

### Method C — Anim8 Python nodes (if you copy scripts into the project)

Copy `anim8_tools.py` + `pipeline_common.py` → your project **`Content/Python/`** → **restart editor**.

Then search graph for **Get Production Project Names** (category **Anim8 Pipeline**).

```
Event Construct
    │ exec
    ▼
For Each Loop ◄──── Array ──── Get Production Project Names (Return Value)
    │
    │ Loop Body (exec)
    ▼
Add Option (SequenceProjectCombo)
    Item ◄──── Array Element

For Each Loop Completed (exec)
    ▼
Set Selected Option (SequenceProjectCombo)
    Option ◄──── Get Suggested Production Project (Return Value)
```

**Important:** `Get Production Project Names` has **no white exec pin** — only connect **Return Value** to **Array**.

---

### Common mistakes

| Mistake | Result |
|---|---|
| **Make Array** + text box as the loop source | Only one name loops — not all production folders |
| **Loop Body** not wired to **Add Option** | Loop runs but combo stays empty |
| Wiring **Event Construct** straight to **Set Selected Option** | Default runs before options exist |
| Forgetting **Completed** | Options added but nothing pre-selected |
| **Execute Python Command** on Event Construct expecting an array back | Python cannot feed **For Each Loop** — use Method B instead |
| Anim8 nodes not found | Use Method A or B; or copy scripts to `Content/Python/` for Method C |

**No tkinter / external window** — project selection stays inside your utility widget.

---

## Step 6 — Graph Wiring

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
import sys; sys.path.append("A:/Anim_8_Scripts"); import pipeline_common, script_1_organize, importlib; importlib.reload(pipeline_common); importlib.reload(script_1_organize); script_1_organize.run(project_name="{project}", dry_run={dry})
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

No text box needed — the path is stored in memory for the session. Check the Output Log to confirm.

---

#### Plan A — Browse Camera Export Folder node (optional)

Only works if Unreal registers the Python Blueprint library.

**One-time per session** — Python console:

```python
import sys; sys.path.append("A:/Anim_8_Scripts"); import anim8_tools
```

Then search the graph for **`Browse Camera Export Folder`** (category: **Anim8 Pipeline**).

```
On Clicked → Browse Camera Export Folder
```

Return value is stored automatically via `browse_camera_folder()` — no Set Text wiring needed.

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
import sys; sys.path.append("A:/Anim_8_Scripts"); import pipeline_common, script_2_sequence, importlib; importlib.reload(pipeline_common); importlib.reload(script_2_sequence); script_2_sequence.run(project_name="{project}", camera_folder="", dry_run={dry}, fps={fps}, overwrite={ow}, interactive_shots={pick})
```

**Pin wiring:**

| Format pin | Connect from |
|---|---|
| `{project}` | `SequenceProjectCombo` → **Get Selected Option** → Format Text `{project}` |

**Important:** Wire `{project}` from **SequenceProjectCombo** only — **not** the Organize section text box (that field is empty and will send `project_name=''`).

**If Get Selected Option still sends empty**, use this wiring instead:

| Pin | Connect from |
|---|---|
| `{project}` | `SequenceProjectCombo` → **Get Selected Index** → **Get Option String At Index** (same combo, Index pin) |
| `{dry}` | `SequenceDryRunCheckbox` → **Is Checked** → **Select String** (A=`True`, B=`False`) |
| `{ow}` | `OverwriteCheckbox` → **Is Checked** → **Select String** (A=`True`, B=`False`) |
| `{pick}` | `AllShotsCheckbox` → **Is Checked** → **Select String** (A=`False`, B=`True`) |
| `{fps}` | `FpsCombo` → **Get Selected Option** |

**No `{camfolder}` pin** — camera path comes from **Find Camera Folder** memory (`camera_folder=""` in the command above).

---

## Step 7 — Compile, Save, Run

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
1. **Project** dropdown lists folders under `/Game/Production/` (filled on widget open)
2. Click **Find Camera Folder** → select Maya export folder (`Shot##_cam.fbx` files)
3. Confirm path in Output Log: `Camera export folder set: ...`
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
| Can't find **Browse Camera Export Folder** | Run `import anim8_tools` in Python console (Step 4). Or use Plan B Execute Python on Find button. |
| Can't find **Get Production Project Names** | Same as above — copy scripts to `Content/Python/` and restart editor |
| **Execute Python Command** node missing | Enable Python Editor Script Plugin, restart editor |
| Button does nothing | Check white **exec** wire: On Clicked → Execute Python Command |
| Python error on Run | Window → Developer Tools → **Output Log** — read the red error |
| `No camera folder set` | Click **Find Camera Folder** before Build Sequences (path is remembered for the session even when scripts reload) |
| Sequences build but no Camera Cut track | Output Log shows `0 camera FBX found` — wrong export folder or FBX names must match `Shot##_cam.fbx` |
| `Select a production project... Received project_name=''` | `{project}` wired to wrong pin (often empty Organize text box) or combo has no real selection — use **Get Option String At Index**; on Event Construct use **Set Selected Index 0** not Get Game Name |
| Project combo empty on open | Event Construct not wired — see Step 5, or add options manually in Designer |
| `cannot import name 'list_production_projects' from 'pipeline_common'` | Stale Python cache — update Build Sequences Format Text to reload `pipeline_common` first (see Step 6), or restart the editor |
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

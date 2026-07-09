# Anim8 Pipeline — Editor Utility Widget Guide

Complete reference for building and wiring the pipeline widget in Unreal Engine.

---

## What This Widget Does

| Section | Script | Purpose |
|---|---|---|
| **Organize Staging** | `script_1_organize.py` | Moves assets from `/Game/Staging` into production folders |
| **Build Sequences** | `script_2_sequence.py` | Builds shot sequences (preroll + lighting subsequence) and master |
| **Add to Render Queue** | `script_3_render_queue.py` | Clears MRQ and adds all main shot sequences |

**MRQ button not working?** → [MRQ_BUTTON.md](MRQ_BUTTON.md) (fix wiring in `EUW_Anim8Pipeline`)

**Typical workflow:**
1. TA imports FBX/ABC into `/Game/Staging` using Unreal's normal import window
2. Run **Organize Staging** → assets move to `/Game/Production/{Project}/Shot##/Animation/`
3. Click **Find Camera Folder** → pick the Maya export folder on disk
4. Run **Build Sequences** → shot Level Sequences with preroll anims, lighting subsequence, and optional `{Project}_Master`

---

## Before You Start

**Required plugins (Edit → Plugins):**
- Python Editor Script Plugin — **enabled**
- Editor Scripting Utilities — **enabled** (if available in your UE version)

**Required folders in Content Browser:**
- `/Game/Staging` — TA imports everything here first
- `/Game/Production/` — script creates `{ProjectName}/Shot##/` under here

**Scripts location:**

| Setup | Where Python lives |
|---|---|
| **Plugin (recommended)** | `YourProject/Plugins/Anim8Pipeline/Content/Python/` — auto-loaded, no path hacks |
| **Legacy dev copy** | `sys.path.append(".../Content/Python")` if scripts sit outside the project |

See [PLUGIN_INSTALL.md](PLUGIN_INSTALL.md) for plugin install. Widget commands below use the **plugin** form (no `sys.path.append`).

**After the widget works:** package it into the plugin so the team does not rebuild it — [WIDGET_PACKAGE.md](WIDGET_PACKAGE.md).

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
│  Project  [ TestRun ▼ ]  [ Refresh ]          │  ← Refresh after new /Game/Production/ folders
│  [ Find Camera Folder ]                       │
│  [x] All Shots                                │
│  FPS            [ 24 ▼ ]                      │
│  [ ] Dry Run                                  │
│  [ ] Overwrite Existing                       │
│  [       Build Sequences        ]             │
│                                               │
│  ── 3 · Movie Render Queue ─────────────────   │
│  Project  [ TestRun ▼ ]  [ Refresh ]          │
│  [        Create MRQ Jobs         ]           │
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
| Combo Box (String) | `SequenceProjectCombo` | empty — filled on widget open + **Refresh** (see Step 5) |
| Button | `RefreshProjectsButton` | label: "Refresh" (small, beside Project combo) |
| Button | `FindCameraFolderButton` | label: "Find Camera Folder" |
| Check Box | `AllShotsCheckbox` | **checked** |
| Combo Box (String) | `FpsCombo` | options: `24`, `30`, `60` — default `24` |
| Check Box | `SequenceDryRunCheckbox` | unchecked |
| Check Box | `OverwriteCheckbox` | **unchecked** |
| Button | `SequenceRunButton` | label: "Build Sequences" |

### Section 3 — Movie Render Queue

| Widget | Variable name | Default |
|---|---|---|
| Combo Box (String) | `RenderQueueProjectCombo` | filled on widget open + **Refresh** (see [MRQ_BUTTON.md](MRQ_BUTTON.md)) |
| Button | `RefreshRenderQueueButton` | label: "Refresh" |
| Button | `CreateMrqButton` | label: "Create MRQ Jobs" |

Full MRQ dropdown + button wiring: **[MRQ_BUTTON.md](MRQ_BUTTON.md)** (step-by-step, same pattern as Build Sequences).

**Removed from Section 2:** Project Name text box and Camera Folder text box — project is a **dropdown in the widget**, camera path is set by **Find Camera Folder** (stored in memory, no popup on Run).

---

## Step 4 — Anim8 Blueprint nodes (optional)

With the **Anim8 Pipeline** plugin enabled, Blueprint nodes register automatically on editor start (`init_unreal.py`).

Nodes (category **Anim8 Pipeline**):

| Node | Purpose |
|---|---|
| **Get Production Project Names** | Fill Project combo (Method C) |
| **Get Suggested Production Project** | Default combo selection |
| **Browse Camera Export Folder** | Optional — Execute Python for Find button works without this |

If nodes are missing: confirm plugin is enabled → restart editor.

---

## Step 5 — Fill the Project dropdown (+ Refresh button)

### What is `RefreshProjectCombo`?

It is **not** a built-in Unreal thing. It is just a **name you give to a red node** in your graph.

Think of it like a **recipe card** titled “fill the project dropdown.”  
You write the steps **once** on that card, then trigger it from two places:

1. When the widget opens (**Event Construct**)
2. When you click **Refresh**

That way you do not copy-paste the same nodes twice.

---

### Part A — Add the Refresh button (Designer tab)

1. Open your widget → **Designer** tab  
2. From the **Palette** (left), drag a **Button** onto the layout — put it next to the Project dropdown  
3. Select the button → **Details** panel (right) → change the label text to **Refresh**  
4. Details → tick **Is Variable**  
5. Set the variable name to **`RefreshProjectsButton`**

---

### Part B — Create the recipe card (Graph tab)

1. Open the **Graph** tab  
2. **Right-click** on empty space  
3. Click **Add Event** → **Custom Event**  
4. A red node appears. Click its name at the top and rename it to **`RefreshProjectCombo`**

You now have an empty red node. Everything below goes **starting from this node** (not from Event Construct).

---

### Part C — Build the dropdown fill (inside `RefreshProjectCombo`)

Do these in order. Every **white wire** is execution (the flow of “do this, then this”).

**Step 1 — Clear old list**

`Clear Options` is **not** in the Details panel. It is a **Graph function** on the combo box.

1. Left panel **My Blueprint** → drag **`SequenceProjectCombo`** into the graph  
2. Pick **Get SequenceProjectCombo** (not Set — Get only shows Get/Set on first drag; that is normal)  
3. Drag from the **blue output pin** on that Get node into empty graph space  
4. Release → search **`Clear Options`**  
   - If nothing shows: **uncheck Context Sensitive** (top-left of search box) and search again  
   - Pick **Clear Options** under **Combo Box String**  
5. **White wire:** `RefreshProjectCombo` → **Clear Options** (exec)  
6. The Get node’s blue pin also connects to **Clear Options → Target** (the combo to clear)

**Can’t find Clear Options at all?** Skip Step 1 for now — wire `RefreshProjectCombo` straight to **For Each Loop**. Refresh may duplicate names until you fix this. Confirm in Designer your widget type is **Combo Box (String)**, not a generic Combo Box.

**Step 2 — Get folders from Content Browser**

1. Right-click → search **`List Assets`** (under Editor Scripting)  
2. Set **Directory Path** to `/Game/Production/` (no **s** — not `Productions`)  
3. **Recursive** = off  
4. **Include Folder** = **ON / checked** ← **required** or the list is empty (folders are not assets)  
5. Right-click → add **For Each Loop**  
6. **White wire:** **Clear Options** → **For Each Loop** (if **List Assets** has no white exec pin, skip it — only connect the purple **Return Value** wire)  
7. **Purple wire:** **List Assets → Return Value** → **For Each Loop → Array**

**Step 3 — Add each folder name to the dropdown**

1. Drag **`SequenceProjectCombo`** → **Add Option**  
2. **White wire:** **For Each Loop → Loop Body** → **Add Option**  
3. Right-click → **Replace** (the **String** one)  
4. **Replace → Source String** ← **For Each Loop → Array Element**  
5. **Replace → Search String** = `/Game/Production/`  
6. **Replace → Replace String** = leave empty  
7. If names show with a trailing `/`, add a **second Replace** that removes `/`  
8. **Replace → Return Value** → **Add Option → Item**

**Step 4 — Pick the first project by default**

1. Drag **`SequenceProjectCombo`** → **Set Selected Index**  
2. Set **Index** to **`0`**  
3. **White wire:** **For Each Loop → Completed** → **Set Selected Index**

**Compile** and **Save**.

---

### Part D — Hook up the two triggers

You already built the recipe. Now tell Unreal **when** to run it.

**When widget opens**

1. If you do not have **Event Construct**, right-click → **Add Event → Event Construct**  
2. **White wire:** **Event Construct** → **`RefreshProjectCombo`**

**When Refresh is clicked**

1. Left panel **My Blueprint** → drag **`RefreshProjectsButton`** into the graph  
2. From the pin menu, pick **On Clicked** (or select the button in Designer → Details → Events → **+ On Clicked**)  
3. **White wire:** **On Clicked** → **`RefreshProjectCombo`**

**Compile** and **Save**.

---

### Test it

1. Run the widget  
2. Project dropdown should list folders from `/Game/Production/`  
3. In Content Browser, create a new folder under `/Game/Production/` (e.g. `MyNewProject`)  
4. Click **Refresh** — the new name should appear **without** closing Unreal

---

### If you already wired Event Construct the old way

You probably have **Event Construct → For Each Loop → …** already working.

1. Create **`RefreshProjectCombo`** (Part B)  
2. **Cut** all nodes after Event Construct (List Assets, For Each Loop, Add Option, Replace, Set Selected Index — everything except Event Construct)  
3. **Paste** them next to **`RefreshProjectCombo`**  
4. Connect **`RefreshProjectCombo`** → first node (**Clear Options** or **For Each Loop**) with a white wire  
5. Connect **Event Construct** → **`RefreshProjectCombo`** only (one white wire)  
6. Connect **RefreshProjectsButton → On Clicked** → **`RefreshProjectCombo`**

---

### Reference (optional — skip if overwhelmed)

<details><summary>Word-by-word node explanations</summary>

| Node | Plain English |
|---|---|
| **Event Construct** | Widget just opened — run setup once |
| **Custom Event** | Your own named action you can call from multiple places |
| **Clear Options** | Empty the dropdown before refilling |
| **List Assets** | Ask Content Browser what lives in `/Game/Production/` |
| **For Each Loop** | Do the same thing for every folder found |
| **Add Option** | Add one name to the dropdown |
| **Replace** | Turn `/Game/Production/TestRun` into `TestRun` |
| **Set Selected Index 0** | Select the first item in the list |

</details>

<details><summary>Other methods (manual combo, Python nodes)</summary>

See **Method A** and **Method C** below if you are not using List Assets.

</details>

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
- Right-click in Graph → **Add Event → Custom Event** → name it **`RefreshProjectCombo`**
- Put **all** populate logic inside this event (not directly on Event Construct)
- In your Event Construct graph, **delete** the old **Project Name Input → Make Array** wires

**After wiring `RefreshProjectCombo`:**
- **Event Construct** → **RefreshProjectCombo** (white exec)
- **RefreshProjectsButton → On Clicked** → **RefreshProjectCombo** (white exec)

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
| 7 | White wire: **`RefreshProjectCombo`** (Custom Event entry) → **Clear Options** on `SequenceProjectCombo` → **For Each Loop** (exec) |
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
- Checked → `False` → build **all** shots (no picker)
- Unchecked → `True` → opens **shot checkbox dialog** on Run — pick shots, lighting, and **master sequence**

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
import pipeline_common, script_1_organize, importlib; importlib.reload(pipeline_common); importlib.reload(script_1_organize); script_1_organize.run(project_name="{project}", dry_run={dry})
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
import pipeline_common as pc, importlib; importlib.reload(pc); pc.browse_camera_folder()
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
import anim8_tools
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
import pipeline_common, script_2_sequence, importlib; importlib.reload(pipeline_common); importlib.reload(script_2_sequence); script_2_sequence.run(project_name="{project}", camera_folder="", dry_run={dry}, fps={fps}, overwrite={ow}, interactive_shots={pick})
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

### Button 4 — CreateMrqButton

See **[MRQ_BUTTON.md](MRQ_BUTTON.md)** for the full step-by-step (dropdown, Refresh, button wiring).

**Quick wiring:**

```
On Clicked (CreateMrqButton) ──exec──► Add Project Shots To Render Queue
                                              ▲
RenderQueueProjectCombo → Get Selected Option ┘  (Project Name pin)
```

**Execute Python alternate** — use `{project}` from **`RenderQueueProjectCombo`** (not SequenceProjectCombo):

```
import pipeline_common, script_3_render_queue, importlib; importlib.reload(pipeline_common); importlib.reload(script_3_render_queue); script_3_render_queue.run(project_name="{project}", interactive=False)
```

**Before clicking:** open your **render level**. MRQ needs a map.

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
4. **All Shots** checked = build everything; unchecked = checkbox dialog (scroll with mouse wheel) to pick shots, lighting, and master
5. Set **FPS** (24 / 30 / 60)
6. Check **Dry Run** → click **Build Sequences** → review log + health check
7. Uncheck Dry Run → run for real
8. **Overwrite Existing** — only when rebuilding; Python asks "Are you sure?" before deleting sequences

### Per-shot timeline (Build Sequences)

Each main shot sequence is built with:

| Track | Frames |
|---|---|
| Skeletal anims / Alembic | Frame **0** = 1-frame hold (first pose); frame **1+** = full clip |
| Camera Cut | Frame **0** → end (MRQ render starts at 0) |
| Camera spawn / sections (actor + component) | Frame **0** → end |
| Camera transform & component keys | First keys at frame **1** when shot has anims/caches |
| Lighting subsequence (`MovieSceneSubTrack`) | **0 → total** (matches full shot length, e.g. 121) |
| Lighting LS asset playback | Same **0 → total** as the parent shot |

Master sequence assembly is **unchanged** — rebuild master separately if needed.

### Add to Render Queue
1. Select **Project** (same dropdown as Build Sequences, or a dedicated combo)
2. Click **Add Shots to Render Queue**
3. Open **Window → Cinematics → Movie Render Queue** — all main shots are listed
4. Set output/preset in MRQ manually, then render

---

## Output Log — What to Expect

**Script 1 dry run:**
```
[DRY RUN] Would move → /Game/Production/MyProject/Shot01/Animation/Shot01_Kiiboh_anim
```

**Script 2 summary (end of run):**
```
Done — Built: 38  Skipped: 4  Errors: 0

  Master sequence — MyProject_Master
    [DRY RUN] Would create master: /Game/Production/MyProject/MyProject_Master
    [DRY RUN]   + shot Shot01: frames 0–120 (Shot01_MyProject) (estimated duration)
    [DRY RUN]   + shot Shot02: frames 120–240 (Shot02_MyProject) (estimated duration)
    [DRY RUN]   total playback: 0–240 frames (2 shots)
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
| Refresh makes dropdown **empty** | **Include Folder** = ON on List Assets · path = `/Game/Production/` (not Productions) · add **Branch → Is Not Empty** before Add Option |
| Project combo empty / missing new folder | Click **Refresh** after creating a folder under `/Game/Production/` |
| `cannot import name 'list_production_projects' from 'pipeline_common'` | Stale Python cache — update Build Sequences Format Text to reload `pipeline_common` first (see Step 6), or restart the editor |
| Script changes not applying | `importlib.reload` in Format Text handles this — recompile widget if you changed the command string |
| Checkbox values wrong | Select String must use `True`/`False` with capital T and F |
| Widget won't open / compile errors in UE 5.4 (built in 5.7) | **UE assets are not backward-compatible.** Rebuild the widget in your target engine — see [UE version compatibility](#ue-version-compatibility-54-vs-57) below |

---

## UE version compatibility (5.4 vs 5.7)

**Yes — building the widget in UE 5.7 is very likely why it fails in 5.4.**

Unreal `.uasset` files (including Editor Utility Widgets) are saved for a specific engine version. A widget created in **5.7 cannot be opened or run in 5.4** — you will see load errors, missing pins, or a blank/broken widget.

### What still works in 5.4 without rebuilding the widget

The **Python scripts** (`script_1_organize.py`, `script_2_sequence.py`) are designed for UE 5.4+ and can be run from the **Python console** even when the packaged widget fails:

```python
import script_1_organize, script_2_sequence
script_1_organize.run(dry_run=True)
script_2_sequence.run(dry_run=True)   # builds shots + lighting + master
```

Install the plugin with `install_plugin.bat`, enable **Python Editor Script Plugin**, restart the editor.

### Fix: rebuild the widget in UE 5.4

1. Open your **5.4** project with the plugin installed
2. Follow **Steps 1–7** in this guide to create `EUW_Anim8Pipeline` **inside 5.4**
3. Package it to `/Anim8Pipeline/EditorUtilities/EUW_Anim8Pipeline` — see [WIDGET_PACKAGE.md](WIDGET_PACKAGE.md)
4. Copy the new `.uasset` into this repo's `Content/EditorUtilities/` so the team gets a 5.4-compatible widget

### Team on mixed UE versions

| Engine | Widget |
|---|---|
| UE 5.4 | Build and save widget in 5.4 |
| UE 5.7 | Build and save widget in 5.7 |

Keep separate widget `.uasset` files per engine generation, or standardize the studio on one UE version.

### Required plugins (all supported versions)

- **Python Editor Script Plugin**
- **Editor Scripting Utilities** (for List Assets on the Project dropdown)
- **Anim8 Pipeline** (this plugin)

---

## Plugin install

See [PLUGIN_INSTALL.md](PLUGIN_INSTALL.md) — copy to `Plugins/Anim8Pipeline/`, enable plugin, restart editor.

Widget commands use short imports (no `sys.path.append`).

---

## Python Reference (for console testing)

```python
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
    build_lighting=True,
    build_master=True,
)
```

# MRQ — Add Shots to Movie Render Queue (widget setup)

Step-by-step to add a **dedicated project dropdown + Refresh + Create MRQ** button to your Editor Utility Widget.

The Python script (`script_3_render_queue.py`) is already written — you only need widget controls and graph wiring.

---

## What the button does

1. Reads the **MRQ Project** dropdown you select
2. Finds every **main** shot Level Sequence under `/Game/Production/{Project}/Shot##/`
3. **Skips** `*_Lighting` and `{Project}_Master`
4. **Clears** Movie Render Queue
5. **Adds one MRQ job per shot** (uses the level you have open as the render map)
6. Opens the MRQ window

---

## Prerequisites

| Plugin | Required |
|---|---|
| Python Editor Script Plugin | Yes |
| Anim8 Pipeline | Yes |
| **Movie Render Queue** | Yes |
| Editor Scripting Utilities | Yes (List Assets for dropdown) |

Restart the editor after enabling plugins.

**Before clicking the button:** open the **level you render from** in the viewport. MRQ needs a map.

---

## Step 1 — Designer layout

Add **Section 3** below Build Sequences:

```
── 3 · Movie Render Queue ─────────────────
Project  [ CoffeeMonster_Fight ▼ ]  [ Refresh ]
[        Create MRQ Jobs        ]
```

---

## Step 2 — Widget variables (Designer → Is Variable)

| Widget | Variable name | Notes |
|---|---|---|
| Combo Box (String) | `RenderQueueProjectCombo` | MRQ project picker |
| Button | `RefreshRenderQueueButton` | label: **Refresh** |
| Button | `CreateMrqButton` | label: **Create MRQ Jobs** (or "Add Shots to Render Queue") |

---

## Step 3 — Fill the MRQ dropdown (copy Build Sequences pattern)

This is the same recipe as `RefreshProjectCombo` in [WIDGET_GUIDE.md](WIDGET_GUIDE.md) Step 5, but for **`RenderQueueProjectCombo`**.

### Create custom event

1. Graph tab → right-click → **Add Event → Custom Event**
2. Rename to **`RefreshRenderQueueProjectCombo`**

### Inside the custom event (same as Section 2 Refresh)

| Step | Node | Settings |
|---|---|---|
| 1 | **Clear Options** on `RenderQueueProjectCombo` | |
| 2 | **List Assets** | Path `/Game/Production/`, Recursive OFF, **Include Folder ON** |
| 3 | **For Each Loop** | Array ← List Assets Return Value |
| 4 | **Replace** | Remove `/Game/Production/` prefix from folder path |
| 5 | **Add Option** on `RenderQueueProjectCombo` | Item ← Replace result |
| 6 | **Set Selected Index** `0` | After For Each **Completed** |

### Hook triggers

| When | Wire |
|---|---|
| **Event Construct** | → `RefreshRenderQueueProjectCombo` |
| **RefreshRenderQueueButton → On Clicked** | → `RefreshRenderQueueProjectCombo` |

**Tip:** On Event Construct you can chain **both** refreshes:

```
Event Construct → RefreshProjectCombo → RefreshRenderQueueProjectCombo
```

---

## Step 4 — Wire Create MRQ Jobs button

### Option A — Anim8 Blueprint node (recommended)

1. Graph → search **`Add Project Shots To Render Queue`** (category **Anim8 Pipeline**)
2. If missing: restart editor after plugin install, or Python console: `import anim8_tools`

```
On Clicked (CreateMrqButton)
    → Add Project Shots To Render Queue
        Project Name ← RenderQueueProjectCombo → Get Selected Option
```

If **Get Selected Option** is empty at runtime:

| Pin | Wire from |
|---|---|
| Project Name | `RenderQueueProjectCombo` → **Get Selected Index** → **Get Option String At Index** |

### Option B — Execute Python Command

```
On Clicked (CreateMrqButton) → Execute Python Command
```

**Format Text** (paste entire line):

```
import pipeline_common, script_3_render_queue, importlib; importlib.reload(pipeline_common); importlib.reload(script_3_render_queue); script_3_render_queue.run(project_name="{project}", interactive=False)
```

| Pin | Wire from |
|---|---|
| `{project}` | `RenderQueueProjectCombo` → **Get Selected Option** |

**Do NOT** wire `{project}` to Organize text box or `SequenceProjectCombo` unless you want them linked — use **`RenderQueueProjectCombo`**.

**Do NOT** use `interactive=True` — that opens a popup picker instead of using your dropdown.

**Compile → Save**

---

## Step 5 — Test

1. Open your render level
2. Select a project in **Render Queue → Project** dropdown
3. Click **Create MRQ Jobs**
4. Check **Output Log**:

```
Script 3 — Add Shots to Movie Render Queue
Project : YourProject
  Shot01 → Shot01_YourProject
  + MRQ job 'Shot01_YourProject'  map=...  seq=...
Done — Cleared queue, added N job(s)
```

5. **Window → Cinematics → Movie Render Queue** — all main shots listed

### Console test (bypass widget)

```python
import importlib, script_3_render_queue
importlib.reload(script_3_render_queue)
script_3_render_queue.run(project_name="YourProject", dry_run=True)
script_3_render_queue.run(project_name="YourProject")
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Button does nothing | White exec wire: On Clicked → node / Execute Python |
| `project_name=''` | Wire **RenderQueueProjectCombo**, not Organize text box |
| Popup picker appears | Remove `interactive=True` from Python command |
| `No editor level is open` | Open your render map first |
| `No main shot sequences found` | Run **Build Sequences** first |
| `Movie Render Queue subsystem not found` | Enable MRQ plugin, restart |
| Node not in graph search | Restart editor; `import anim8_tools` in Python console |

---

See also: [WIDGET_GUIDE.md](WIDGET_GUIDE.md), [PLUGIN_INSTALL.md](PLUGIN_INSTALL.md)

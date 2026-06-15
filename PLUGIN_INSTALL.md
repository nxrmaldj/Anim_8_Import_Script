# Anim8 Pipeline — Plugin Install

Simplest way to run the pipeline in any Unreal project.

---

## Install (pick one)

### Option A — Installer script (easiest)

1. Double-click **`install_plugin.bat`** (or run `python install_plugin.py`)
2. Pick your **Unreal project folder** (where the `.uproject` file lives)  
   — or pick the project's **`Plugins`** folder
3. Continue with **Enable plugins** below

### Option B — Manual copy

Copy this repo into your Unreal project:

```
YourProject/
└── Plugins/
    └── Anim8Pipeline/          ← folder name must be Anim8Pipeline
        ├── Anim8Pipeline.uplugin
        └── Content/
            └── Python/
                ├── script_1_organize.py
                ├── script_2_sequence.py
                ├── pipeline_common.py
                ├── anim8_tools.py
                └── init_unreal.py
```

You can rename the repo folder from `Anim_8_Scripts` to `Anim8Pipeline` when copying manually.

### Enable plugins in Unreal

**Edit → Plugins**, search and enable:

| Plugin | Required |
|---|---|
| **Python Editor Script Plugin** | Yes |
| **Anim8 Pipeline** | Yes |
| **Editor Scripting Utilities** | Yes (for widget List Assets node) |

Restart the editor when prompted.

### Create folders + widget

In Content Browser, create if missing:

- `/Game/Staging`
- `/Game/Production`

**Widget:** build once using [WIDGET_GUIDE.md](WIDGET_GUIDE.md), then package it into the plugin using [WIDGET_PACKAGE.md](WIDGET_PACKAGE.md). After that, open it via **Tools → Anim8 Pipeline**.

---

## Widget Python commands (plugin)

**Organize Staging:**

```
import pipeline_common, script_1_organize, importlib; importlib.reload(pipeline_common); importlib.reload(script_1_organize); script_1_organize.run(project_name="{project}", dry_run={dry})
```

**Find Camera Folder:**

```
import pipeline_common as pc, importlib; importlib.reload(pc); pc.browse_camera_folder()
```

**Build Sequences:**

```
import pipeline_common, script_2_sequence, importlib; importlib.reload(pipeline_common); importlib.reload(script_2_sequence); script_2_sequence.run(project_name="{project}", camera_folder="", dry_run={dry}, fps={fps}, overwrite={ow}, interactive_shots={pick})
```

---

## Verify it loaded

**Output Log** after editor restart — no Python errors from `init_unreal.py`.

**Python console:**

```python
import script_1_organize
script_1_organize.run(dry_run=True)
```

**Graph search** (widget): `Browse Camera Export Folder` or `Get Production Project Names` under **Anim8 Pipeline**.

---

## Update the plugin

1. Pull latest from GitHub (or copy new files over `Plugins/Anim8Pipeline/`)
2. Restart the editor (or click Run — `importlib.reload` in widget commands picks up script changes without restart)

---

## Dev without installing (legacy)

If scripts still live on disk outside the project (e.g. `A:/Anim_8_Scripts/Content/Python/`):

```python
import sys; sys.path.append("A:/Anim_8_Scripts/Content/Python")
```

Prefer the plugin install for the team — no hardcoded paths.

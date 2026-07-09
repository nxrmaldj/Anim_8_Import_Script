# Anim8 Pipeline — Plugin Install

Simplest way to run the pipeline in any Unreal project.

---

## Install (pick one)

### Prerequisite — Python 3 (installer only)

The **`install_plugin.bat`** script needs Python on your PC (Unreal’s built-in Python is **not** used for install).

1. Download **Python 3** from [python.org/downloads](https://www.python.org/downloads/)  
   **Or install from terminal (Windows):**
   ```powershell
   winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
   ```
2. Run the installer → check **“Add python.exe to PATH”** → Install (winget does this automatically)
3. **Windows only:** Settings → **Apps** → **Advanced app settings** → **App execution aliases** → turn **Off** the aliases for `python.exe` and `python3.exe` (they send you to the Microsoft Store instead of real Python)
4. Open a **new** terminal and verify:

   ```powershell
   python --version
   ```

   You should see something like `Python 3.12.x`.

### Option A — Installer script (easiest)

1. Double-click **`install_plugin.bat`** (or in Cursor terminal: `python install_plugin.py`)
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
        ├── Config/
        │   └── DefaultEngine.ini    ← Social Media filmback preset
        ├── Resources/
        │   └── Icon128.png          ← plugin icon (Edit → Plugins)
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

### Social Media filmback preset

The installer copies `Config/DefaultEngine.ini` **and** patches your project's `Config/DefaultEngine.ini` directly (plugin config merge alone is unreliable for project plugins):

| Setting | Value |
|---|---|
| Name | **Social Media** |
| Sensor width | 13.365 mm |
| Sensor height | 23.76 mm |

After install + restart: select a **Cine Camera Actor** → **Filmback** dropdown → **Social Media**.

This adds the preset only — it does not change the default filmback for new cameras unless you set that in your project's own `Config/DefaultEngine.ini`.

### Plugin icon (optional)

1. Save your PNG as **128×128** (square)
2. Put it in the repo at **`Resources/Icon128.png`**
3. Re-run **`install_plugin.bat`** (or copy `Resources/` into the installed plugin)
4. Restart the editor — icon shows in **Edit → Plugins** next to **Anim8 Pipeline**

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

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Widget broken / won't compile in UE 5.4 | Widget was likely saved in a newer UE (e.g. 5.7). **Rebuild the widget in 5.4** — see [WIDGET_GUIDE.md](WIDGET_GUIDE.md#ue-version-compatibility-54-vs-57) |
| Tools → Anim8 Pipeline missing | Package widget to `/Anim8Pipeline/EditorUtilities/EUW_Anim8Pipeline` |
| Python import errors | Enable **Python Editor Script Plugin**, restart editor |
| Scripts work but widget doesn't | Use Python console as a workaround until widget is rebuilt for your UE version |

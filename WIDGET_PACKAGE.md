# Anim8 Pipeline — Package Your Editor Utility Widget

Your widget is a **`.uasset` file** (Blueprint). It lives in the plugin’s **Content** folder so it travels with the scripts.

---

## One-time: move your widget into the plugin

Do this in the project where you already built and wired the widget.

### 1. Install the plugin in that project

Run `install_plugin.bat` so you have:

```
YourProject/Plugins/Anim8Pipeline/
```

### 2. Turn on plugin content in Content Browser

Content Browser → **Settings** (bottom right) → enable **Show Plugin Content**

You should see a folder named **Anim8 Pipeline** (or **Anim8Pipeline**).

### 3. Create a folder for the widget

Under **Anim8 Pipeline** → right-click → **New Folder** → name it **`EditorUtilities`**

Full path:

```
/Anim8Pipeline/EditorUtilities/
```

### 4. Move your widget asset

Find your existing widget (e.g. `/Game/EUW_Anim8Pipeline`).

**Option A — drag**

- Drag the widget into `/Anim8Pipeline/EditorUtilities/`

**Option B — Move To**

- Right-click the widget → **Asset Actions → Move To** → pick `EditorUtilities` under the plugin

### 5. Rename (recommended)

Name the asset **`EUW_Anim8Pipeline`** so it matches what the plugin expects.

### 6. Update Python commands (plugin form)

Open the widget → **Graph** tab → update each **Execute Python Command** / **Format Text** to use **no** `sys.path.append`:

**Organize:**
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

**Compile → Save.**

### 7. Copy widget into the repo (for your team)

Copy the `.uasset` (and any `.umap` if you created one — you shouldn’t need one) into the git repo:

```
Anim_8_Scripts/Content/EditorUtilities/EUW_Anim8Pipeline.uasset
```

Then `install_plugin.bat` will copy it to other projects automatically.

---

## How to run the widget (after packaging)

### Option A — Tools menu (automatic)

If the widget is at `/Anim8Pipeline/EditorUtilities/EUW_Anim8Pipeline`:

**Tools → Anim8 Pipeline**

(Added by the plugin on editor start.)

### Option B — Content Browser

1. **Show Plugin Content** ON  
2. **Anim8 Pipeline → EditorUtilities → EUW_Anim8Pipeline**  
3. Right-click → **Run Editor Utility Widget**  
4. Dock the panel where you like

### Option C — Python console

```python
import anim8_launcher
anim8_launcher.open_widget()
```

---

## Install on another project

1. Run **`install_plugin.bat`** → pick that project  
2. If you packaged the `.uasset` in the repo, it copies with the plugin  
3. Enable plugins → restart editor  
4. **Tools → Anim8 Pipeline**

No need to rebuild the widget from scratch.

---

## Checklist before sharing

| Check | Done? |
|---|---|
| Widget lives at `/Anim8Pipeline/EditorUtilities/EUW_Anim8Pipeline` | |
| Format Text uses plugin imports (no `A:/` path) | |
| Widget compiles with no errors | |
| `install_plugin.bat` tested on a second project | |
| `/Game/Staging` and `/Game/Production` exist in target project | |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| No **Anim8 Pipeline** in Tools menu | Widget not at expected path — check name and folder |
| Button does nothing | Plugin not enabled, or Format Text still uses old `sys.path` |
| Widget missing after install | Copy `.uasset` into repo `Content/EditorUtilities/` and re-run installer |
| Can't see plugin folder | **Show Plugin Content** in Content Browser |

---

See also: [WIDGET_GUIDE.md](WIDGET_GUIDE.md) (how to build the widget), [PLUGIN_INSTALL.md](PLUGIN_INSTALL.md) (plugin install).

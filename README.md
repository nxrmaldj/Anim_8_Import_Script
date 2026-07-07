# Anim_8 Import Pipeline

Unreal Engine Python tools that organize Maya-exported assets into a clean production folder structure and build Level Sequences per shot.

---

## Quick start (plugin)

1. Run **`install_plugin.bat`** → pick your Unreal project folder
2. Enable **Python Editor Script Plugin** + **Anim8 Pipeline** in Edit → Plugins
3. Restart the editor
4. Build the widget — see [WIDGET_GUIDE.md](WIDGET_GUIDE.md)

Full steps — [PLUGIN_INSTALL.md](PLUGIN_INSTALL.md)

---

## Progress

- [x] Script 1 — staging organizer
- [x] Script 2 — Level Sequence builder (+ master + lighting sequences)
- [x] Editor Utility Widget (organize + build sequences)
- [x] Plugin package (`Anim8Pipeline.uplugin` + `Content/Python/`)

---

## Workflow

1. TA imports FBX/ABC into `/Game/Staging` via Unreal's native import window
2. **Organize Staging** — routes assets by type into production folders
3. **Find Camera Folder** — pick Maya export folder on disk
4. **Build Sequences** — Level Sequence per shot (anims, geo caches, cameras), empty lighting sequence per shot, master sequence with all shots in order
5. Right-click Staging → **Fix Up Redirectors**

---

## Scripts

| File | Purpose |
|---|---|
| `Content/Python/script_1_organize.py` | Staging → production routing |
| `Content/Python/script_2_sequence.py` | Level Sequence builder |
| `Content/Python/script_3_render_queue.py` | Clear MRQ + add main shots |
| `Content/Python/pipeline_common.py` | Shared helpers |
| `Content/Python/anim8_tools.py` | Blueprint nodes for the widget |

---

## Console (with plugin enabled)

```python
import script_1_organize
script_1_organize.run(project_name="MyProject", dry_run=True)

import script_2_sequence
script_2_sequence.run(project_name="MyProject", dry_run=True)
```

---

## Testing (outside Unreal)

```bash
python test_organize.py
python test_sequence.py
```

---

## Docs

| Doc | Contents |
|---|---|
| [NAMING_CONVENTIONS.md](NAMING_CONVENTIONS.md) | Maya export + UE asset naming rules |
| [MRQ_BUTTON.md](MRQ_BUTTON.md) | Fix Add to Render Queue widget button |
| [PLUGIN_INSTALL.md](PLUGIN_INSTALL.md) | Copy plugin, enable, verify |
| [WIDGET_GUIDE.md](WIDGET_GUIDE.md) | Build and wire the EUW |
| [WIDGET_PACKAGE.md](WIDGET_PACKAGE.md) | Move EUW into plugin + run on any project |
| [SCRIPT_2_PLAN.md](SCRIPT_2_PLAN.md) | Script 2 design spec |

---

## Folder structure

```
/Game/
├── Staging/                      ← TA imports here
├── Production/
│   └── {ProjectName}/
│       └── Shot##/
│           └── Animation/
└── Assets/
    ├── Characters/{Name}/
    └── Props/
```

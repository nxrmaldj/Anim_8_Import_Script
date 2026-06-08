# Anim_8 Import Pipeline

Unreal Engine Python scripts that automate the import of Maya-exported FBX and Alembic files and build Level Sequences per shot.

Works with any Unreal Engine animation project — set `PROJECT_NAME` in the config block and the scripts adapt automatically.

---

## Scripts

| Script | Status | Purpose |
|---|---|---|
| `script_1_import.py` | ✅ Ready | Scan export folder → detect file types → create Content Browser folders → import everything to the right place |
| `script_2_sequence.py` | 🔜 Coming soon | Build Level Sequence per shot with camera, skeletal mesh, and geometry cache tracks |

---

## How to Run

**Option A — Unreal Python Script Runner**

1. Open Unreal Editor
2. Go to **Editor → Python Script Runner** (or the Tools menu)
3. Open the script and click **Run**

**Option B — Command Line**

```
UnrealEditor.exe MyProject.uproject -ExecutePythonScript="C:/Scripts/script_1_import.py"
```

---

## Config

Both scripts share the same config block at the top of each file. **You only change values in one place per project.**

```python
SOURCE_FOLDER   = "C:/Exports/MyProject"   # flat folder of Maya exports on disk
PROJECT_ROOT    = "/Game/Production"        # never changes
ASSETS_ROOT     = "/Game/Assets"            # never changes
PROJECT_NAME    = "FindingKiiboh"           # ← change per project

KNOWN_CHARACTERS = {
    "Kiiboh": "/Game/Assets/Characters/Kiiboh/SK_Kiiboh",
    # Add more characters here
}

ALEMBIC_SCALE = 1.0
```

---

## Filename Convention

All exported files must follow this naming convention:

| Pattern | Type | Example |
|---|---|---|
| `Shot##_Camera_anim.fbx` | Camera (Script 2 only) | `Shot01_Camera_anim.fbx` |
| `Shot##_{CharName}_anim.fbx` | Character Animation | `Shot03_Kiiboh_Damaged_anim.fbx` |
| `Shot##_{AssetName}_anim.abc` | Alembic Geo Cache | `Shot01_Car_anim.abc` |
| `Shot##_{AssetName}_anim.fbx` | Static Mesh / Prop | `Shot03_Crane_anim.fbx` |
| `{AssetName}.abc` (no shot prefix) | Shared Asset | `Dumpster_Location.abc` |

---

## Folder Structure Created

```
/Game/
├── Production/
│   └── {PROJECT_NAME}/
│       ├── Shot01/
│       │   └── Animation/        ← anim FBXs + ABC geo caches
│       ├── Shot02/
│       │   └── Animation/
│       └── _Assets/              ← files with no shot number
└── Assets/
    ├── Characters/               ← existing SK assets (not recreated)
    └── Props/                    ← static meshes from unknown FBXs
```

`Shot##/` folder names come directly from the filename — `Shot11A` is treated as its own shot with no special handling needed.

---

## Script 1 — Detection Order

Detection runs top to bottom; first match wins.

1. `_Camera_` token → **SKIP** (handled by Script 2)
2. Name matches a key in `KNOWN_CHARACTERS` → import as **Animation FBX**
3. Extension is `.abc` → import as **Alembic / GeometryCache**
4. Extension is `.fbx` (fallback) → import as **Static Mesh**
5. No `Shot##` prefix → import to **`_Assets/`** shared folder

---

## Checklist — Before Running on a New Project

- [ ] Set `SOURCE_FOLDER` to the Maya export folder on disk
- [ ] Set `PROJECT_NAME`
- [ ] Update `KNOWN_CHARACTERS` with this project's characters
- [ ] Verify `ALEMBIC_SCALE` looks correct after first import (usually `1.0`)
- [ ] Run **Script 1** first
- [ ] Then run **Script 2** per shot *(coming soon)*

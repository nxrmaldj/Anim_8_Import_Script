# Anim_8 Import Pipeline

Unreal Engine Python tools that organize Maya-exported assets into a clean production folder structure and build Level Sequences per shot.

Works with any Unreal Engine animation project — the project name is typed in at run time, so nothing is hardcoded per production.

---

## Progress

- [x] Script 1 — staging organizer (routes assets by real type, dry run, tested in production)
- [x] Standalone test suite for routing logic (19 tests, no UE install needed)
- [x] Editor Utility Widget — project name field, dry-run checkbox, Run button (dockable UI, built in-editor)
- [x] Widget → Python wiring via Execute Python Command (auto-reloads script on every click)
- [x] Script 2 design agreed — see [SCRIPT_2_PLAN.md](SCRIPT_2_PLAN.md)
- [ ] Script 2 — Level Sequence Builder (next up)
- [ ] Add Script 2 button/controls to the widget
- [ ] Package widget into a content-only plugin for easy transfer between projects

---

## Workflow

1. The TA imports all FBX/ABC batches into `/Game/Staging` using Unreal's **native import window** (skeleton linking, LODs, etc. are handled there, the normal way)
2. Run the organizer script
3. Every asset is routed by its **real asset type** into the correct production folder
4. Right-click Staging → **Fix Up Redirectors** to finish cleaning the folder

---

## Scripts

| Script | Status | Purpose |
|---|---|---|
| `script_1_organize.py` | ✅ Ready | Scan `/Game/Staging` → route each asset by type/name → move into production folders |
| `script_2_sequence.py` | 🔜 Coming soon | Build Level Sequence per shot with camera, skeletal mesh, and geometry cache tracks |

---

## How to Run

**Option A — Unreal Python console**

```python
import sys; sys.path.append("A:/Anim_8_Scripts")
import script_1_organize
script_1_organize.run(project_name="MyProject", dry_run=True)   # preview first
script_1_organize.run(project_name="MyProject", dry_run=False)  # then for real
```

**Option B — Python Script Runner**

Open `script_1_organize.py` and click Run — a dialog asks for the project name.

**Option C — Editor Utility Widget** *(planned)*

A widget with a project name field, dry-run checkbox, and Run button that calls `script_1_organize.run(...)` directly.

---

## Routing Rules

Assets are routed by their actual Unreal class — no guessing from filenames:

| Asset in staging | Class | Moves to |
|---|---|---|
| `Shot01_Song_anim` | AnimSequence | `/Game/Production/{Project}/Shot01/Animation/` |
| `Shot02_Debris_anim` | GeometryCache | `/Game/Production/{Project}/Shot02/Animation/` |
| `SK_Song`, `Song_Skeleton`, physics assets | SkeletalMesh / Skeleton / PhysicsAsset | `/Game/Assets/Characters/Song/` |
| Any static mesh | StaticMesh | `/Game/Assets/Props/` |
| Anim with no `Shot##` prefix | AnimSequence | `/Game/Production/{Project}/_Assets/` |
| Materials, textures, anything else | — | **Left in staging** with a warning |

**Safety:**
- Never overwrites — existing assets at the destination are skipped and logged
- Dry run mode prints the full move plan without touching anything
- Re-running is safe; already-moved assets are simply no longer in staging

---

## Folder Structure Created

```
/Game/
├── Staging/                      ← TA imports everything here first
├── Production/
│   └── {PROJECT_NAME}/
│       ├── Shot01/
│       │   └── Animation/        ← anims + geo caches
│       ├── Shot02/
│       │   └── Animation/
│       └── _Assets/              ← assets with no shot number
└── Assets/
    ├── Characters/
    │   └── {CharacterName}/      ← SK meshes, skeletons, physics assets
    └── Props/                    ← static meshes
```

`Shot##` names come directly from the asset name — `Shot11A` is treated as its own shot with no special handling.

---

## Naming Convention

Exports out of Maya should follow this pattern (the asset name in UE mirrors the filename):

| Pattern | Type | Example |
|---|---|---|
| `Shot##_Camera_anim.fbx` | Camera (Script 2 only) | `Shot01_Camera_anim.fbx` |
| `Shot##_{CharName}_anim.fbx` | Character Animation | `Shot03_Kiiboh_Damaged_anim.fbx` |
| `Shot##_{AssetName}_anim.abc` | Alembic Geo Cache | `Shot01_Car_anim.abc` |
| `Shot##_{AssetName}_anim.fbx` | Static Mesh / Prop | `Shot03_Crane_anim.fbx` |
| `{AssetName}.abc` (no shot prefix) | Shared Asset | `Dumpster_Location.abc` |

---

## Testing

Routing logic can be tested outside Unreal with any Python 3:

```bash
python test_organize.py
```

This mocks the `unreal` module and verifies shot parsing, character name cleanup, and every routing rule.

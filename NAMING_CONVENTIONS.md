# Anim8 Pipeline — Naming Conventions

Approved naming for Maya exports and Unreal assets. The pipeline scripts parse these patterns automatically.

**Rule of thumb:** start asset names with **`Shot##_`** when the file belongs to a shot. Use two digits minimum (`Shot01`, not `Shot1`).

---

## Shot numbers

| Format | Valid | Notes |
|---|---|---|
| `Shot01` | Yes | Standard |
| `Shot11A` | Yes | Letter suffix for split shots |
| `shot01` | Yes | Case-insensitive in scripts |
| `Shot1` | No | Must be zero-padded (`Shot01`) |
| `Scene01` | No | Must start with `Shot` |

---

## Maya export filenames (disk)

These are the names on the export folder you pick with **Find Camera Folder**.

### Character / prop animation (FBX)

```
Shot##_CharacterName_anim.fbx
```

| Example | Use |
|---|---|
| `Shot01_Kiiboh_anim.fbx` | Character animation |
| `Shot03_Crane_anim.fbx` | Prop / static mesh animation |
| `Shot11A_Song_anim.fbx` | Letter-suffix shot |

### Geometry cache (Alembic)

```
Shot##_AssetName_anim.abc
```

| Example | Use |
|---|---|
| `Shot01_Car_anim.abc` | Per-shot geo cache |
| `Dumpster_Location.abc` | Shared asset (no shot prefix) → `_Assets` folder |

### Camera (FBX) — pick one style per project

**Recommended (production):**

```
Shot##_cam.fbx
```

| Example | Valid |
|---|---|
| `Shot01_cam.fbx` | Yes |
| `Shot02_CAM.fbx` | Yes (case-insensitive) |
| `Shot11A_cam.fbx` | Yes |

**Legacy (still supported):**

```
Shot##_Camera_anim.fbx
Shot##_cam_anim.fbx
```

| Example | Valid |
|---|---|
| `Shot01_Camera_anim.fbx` | Yes |
| `Shot01_cam_anim.fbx` | Yes |

**Not valid for cameras:**

| Example | Why |
|---|---|
| `Shot01_Kiiboh_anim.fbx` | Character anim, not a camera |
| `Shot01_cam_v2.fbx` | Extra suffix breaks pattern |
| `Shot01_camera_extra.fbx` | Does not match supported patterns |

---

## Unreal asset names (after import)

Import into **`/Game/Staging`** using Unreal’s normal import window. The asset name in UE should match the file name (without path).

### Routed by Organize Staging

| Asset class | Name pattern | Moves to |
|---|---|---|
| AnimSequence | `Shot##_…_anim` | `/Game/Production/{Project}/Shot##/Animation/` |
| GeometryCache | `Shot##_…` | `/Game/Production/{Project}/Shot##/Animation/` |
| AnimSequence (no shot) | `Idle_Loop_anim` | `/Game/Production/{Project}/_Assets/` |
| SkeletalMesh / Skeleton / PhysicsAsset | `Shot##_Char_anim…` or `SK_Char` | `/Game/Assets/Characters/{CharacterName}/` |
| StaticMesh | `Shot##_Prop_anim` | `/Game/Assets/Props/` |

### Character folder name

Derived from the asset name — shot prefix and suffixes are stripped:

| Asset name | Character folder |
|---|---|
| `Shot01_Song_anim` | `Song` |
| `Shot01_Kiiboh_anim_Skeleton` | `Kiiboh` |
| `SK_Song` | `Song` |

### Left in Staging (warning logged)

- Materials, textures, and other classes without a shot prefix
- Redirectors (skipped automatically)

---

## Production folder layout (created by scripts)

```
/Game/Production/{ProjectName}/
├── {ProjectName}_Master        ← master sequence (all shots in order)
├── Shot01/
│   ├── Shot01_{Project}        ← shot sequence (anims, caches, camera)
│   ├── Shot01_{Project}_Lighting
│   └── Animation/              ← anims + geo caches for Shot01
├── Shot02/
│   ├── Shot02_{Project}
│   ├── Shot02_{Project}_Lighting
│   └── Animation/
├── Shot11A/
│   └── Animation/
└── _Assets/                    ← animations with no Shot##_ prefix
```

**Production project folder** = folder name under `/Game/Production/` (e.g. `CoffeeMonster_Fight`, `TestRun`). Must match what you select in the widget dropdown.

---

## Level Sequence naming (Build Sequences)

| Item | Pattern | Example |
|---|---|---|
| Shot sequence | `Shot##_{ProjectName}` | `Shot01_CoffeeMonster_Fight` |
| Shot sequence location | `/Game/Production/{Project}/Shot##/` | Same folder as the shot |
| Lighting sequence | `Shot##_{ProjectName}_Lighting` | `Shot01_CoffeeMonster_Fight_Lighting` |
| Lighting location | `/Game/Production/{Project}/Shot##/` | Next to the shot sequence |
| Master sequence | `{ProjectName}_Master` | `CoffeeMonster_Fight_Master` |
| Master location | `/Game/Production/{Project}/` | Project root (not inside a shot folder) |
| Master structure | One **Shot Track** with each shot LS as a section | Same as UE “Add Master Sequence” |
| Camera actor in sequence | From camera FBX name | `Shot01_cam` or `Shot01_Camera` |

One Level Sequence per shot folder. The **master** sequence stitches every shot sequence together in shot order (`Shot01`, `Shot02`, `Shot11A`, …). Empty **lighting** sequences are created per shot for the lighting team.

**Safe to re-run:** with **Overwrite Existing** unchecked (default), Build Sequences only creates what is missing — shot, lighting, and master sequences you already have are **never deleted or modified**. Check **Overwrite** only when you intentionally want to rebuild from scratch.

---

## Quick reference card

```
Maya export folder (disk):
  Shot01_Kiiboh_anim.fbx      character animation
  Shot01_Car_anim.abc         geometry cache
  Shot01_cam.fbx              camera (recommended)

After import → /Game/Staging → Organize Staging:
  → /Game/Production/{Project}/Shot01/Animation/
  → /Game/Assets/Characters/Kiiboh/
  → /Game/Assets/Props/

Build Sequences:
  → Level Sequence: Shot01_{Project}
  → Lighting sequence: Shot01_{Project}_Lighting (empty, per shot folder)
  → Master sequence: {Project}_Master (all shots in order, at project root)
  → Camera from Shot01_cam.fbx in export folder
```

---

## Naming checklist for artists

- [ ] Shot prefix: `Shot##_` (two digits, optional letter: `Shot11A`)
- [ ] Animations end with `_anim`
- [ ] Cameras: `Shot##_cam.fbx` (or legacy `Shot##_Camera_anim.fbx`)
- [ ] One camera file per shot in the export folder
- [ ] Import everything to `/Game/Staging` before running Organize
- [ ] Pick the correct **production project** in the widget before Build Sequences

---

## Related docs

| Doc | Contents |
|---|---|
| [README.md](README.md) | Pipeline overview |
| [PLUGIN_INSTALL.md](PLUGIN_INSTALL.md) | Install plugin |
| [WIDGET_GUIDE.md](WIDGET_GUIDE.md) | Widget setup |

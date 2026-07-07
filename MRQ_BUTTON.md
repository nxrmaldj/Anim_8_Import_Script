# Fix — Add Shots to Render Queue (MRQ button)

Use this if the **Add Shots to Render Queue** button does nothing, opens a project picker instead of using the combo, or MRQ stays empty.

---

## Before you click the button

1. **Movie Render Queue** plugin enabled → restart editor
2. **Open your render level** in the editor (MRQ needs a map — jobs won't appear without one)
3. **Select a project** in the widget **Project** dropdown (`SequenceProjectCombo`)
4. Python console once per session (if Anim8 nodes missing): `import anim8_tools`

---

## Fix the widget graph (UE 5.5)

Open **`EUW_Anim8Pipeline5_5`** → **Graph** tab.

### Delete broken MRQ wiring

Remove any MRQ button nodes that:
- Call `script_3_render_queue.run()` with **no** `{project}` pin
- Use `interactive=True` (causes popup picker instead of combo)
- Wire `{project}` to the **Organize** text box (always empty)

### Wire Option A — Anim8 Blueprint node (recommended)

1. **RenderQueueButton** → **On Clicked**
2. Add node: **`Add Project Shots To Render Queue`** (category **Anim8 Pipeline**)
3. Connect:
   - **Exec:** On Clicked → node input
   - **Project Name:** `SequenceProjectCombo` → **Get Selected Option**

If Get Selected Option is empty at runtime:

| Pin | Wire from |
|---|---|
| Project Name | `SequenceProjectCombo` → **Get Selected Index** → **Get Option String At Index** |

### Wire Option B — Execute Python Command

On Clicked → **Execute Python Command** ← **Format Text** → To String

**Format field (paste entire line):**

```
import pipeline_common, script_3_render_queue, importlib; importlib.reload(pipeline_common); importlib.reload(script_3_render_queue); script_3_render_queue.run(project_name="{project}", interactive=False)
```

| Pin | Wire from |
|---|---|
| `{project}` | `SequenceProjectCombo` → Get Selected Option (or Get Option String At Index) |

**Compile → Save** the widget.

---

## Verify in Output Log

After clicking the button you should see:

```
Script 3 — starting (project_name='YourProject')
Map     : /Game/Maps/YourMap.YourMap
  + MRQ job 'Shot01_YourProject'  map=...  seq=...
Done — Cleared queue, added N job(s)
MRQ queue reports N job(s)
```

Then open **Window → Cinematics → Movie Render Queue**.

---

## Common errors

| Log message | Fix |
|---|---|
| `project_name=''` | Wire combo to Project Name / `{project}` |
| `No editor level is open` | Open your render map first |
| `No main shot sequences found` | Build sequences first, or check legacy `Shot##` names exist |
| `Movie Render Queue subsystem not found` | Enable MRQ plugin, restart |
| Popup picker instead of combo | Remove `interactive=True`; wire `{project}` from combo |

---

## Console test (bypass widget)

```python
import importlib, script_3_render_queue
importlib.reload(script_3_render_queue)
script_3_render_queue.run(project_name="CoffeeMonster_Fight", interactive=False)
```

See also: [WIDGET_GUIDE.md](WIDGET_GUIDE.md) Button 4, [PLUGIN_INSTALL.md](PLUGIN_INSTALL.md)

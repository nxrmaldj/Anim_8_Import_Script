# New Game Project — Agent Handoff

Paste this file (or the prompt below) into a **new Cursor chat** when setting up a fresh Unreal game + GitHub repo.

---

## Copy-paste prompt for new agent

```
I am starting a NEW Unreal game project in a NEW Cursor workspace and NEW GitHub repo.

Context:
- Anim8 Pipeline plugin source lives at: A:\Anim_8_Scripts (GitHub: Anim_8_Import_Script)
- Plugin installs to: YourProject/Plugins/Anim8Pipeline/
- Installer: A:\Anim_8_Scripts\install_plugin.bat or python install_plugin.py
- Plugin includes: Python scripts, EUW widget, icon, Tools → Anim8 Pipeline menu

What I need you to do (step by step, don't stop until done or blocked):
1. Ask me for: game name, Unreal project folder path, GitHub repo name (public/private)
2. Verify the Unreal project exists (or tell me to create it in Epic Launcher first)
3. Run install_plugin.py targeting that project folder
4. Add a standard Unreal .gitignore to the game project root
5. git init, first commit (exclude Binaries, Intermediate, Saved, DerivedDataCache)
6. Create GitHub repo with gh and push (ask before push if needed)

Do NOT modify A:\Anim_8_Scripts unless I ask — work in the NEW game folder only.

Docs in plugin repo for reference:
- PLUGIN_INSTALL.md
- NAMING_CONVENTIONS.md
- WIDGET_GUIDE.md
```

---

## How to start clean in Cursor

1. **File → Open Folder** → select your **new game** folder (or create empty folder first)
2. **New Chat** (Ctrl+L or New Agent) — do NOT continue this old thread
3. Paste the prompt above
4. Give the agent: game name, path, GitHub repo name when asked

---

## If the agent stops after "thinking briefly"

Common causes:
- **Waiting for your input** — check if it asked a question
- **Task too vague** — use the prompt above with explicit steps
- **Missing path** — agent can't create UE project in Launcher; you create project first, then agent does git + plugin install
- **GitHub push needs approval** — approve the push command in Cursor
- **Wrong folder open** — agent only sees the workspace folder; open the GAME folder in Cursor first

Retry with: "Continue from step X. Game path is: D:\Projects\MyGame. Repo name: MyGame."

---

## Two repos (don't merge)

| Repo | Purpose |
|---|---|
| `Anim_8_Import_Script` | Plugin tool (A:\Anim_8_Scripts) |
| New game repo | Unreal .uproject + Content + Plugins/Anim8Pipeline |

---

## Manual fallback (no agent)

```powershell
# 1. Create UE project in Epic Launcher first

# 2. Install plugin
cd A:\Anim_8_Scripts
python install_plugin.py
# pick game folder

# 3. In game folder
cd D:\Projects\MyNewGame
git init
# add Unreal .gitignore
git add .
git commit -m "feat: initial project with Anim8 Pipeline"

gh repo create MyNewGame --private --source=. --remote=origin --push
```

---

## After setup

1. Edit → Plugins → Python Editor Script Plugin + Anim8 Pipeline + Editor Scripting Utilities
2. Restart UE
3. Create /Game/Staging and /Game/Production/YourProjectName
4. Tools → Anim8 Pipeline

See NAMING_CONVENTIONS.md for export naming.

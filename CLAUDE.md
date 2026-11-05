# sounds – the central ElevenLabs sound factory for all of the owner's apps

Talk to the owner in Hebrew (masculine forms). Before generating or changing anything, say what you'll do and wait for his OK.
Ask one question at a time.

## How it works
- The ElevenLabs key lives ONLY here, as the repository secret `ELEVENLABS_API_KEY`. Never put a key in an app's code
  (the apps are public GitHub Pages sites) – apps only play ready-made mp3 files.
- Each app has a folder: `projects/<app>/list.json` (`{"items": [...]}`). Generated files land next to it.
- `tools/eleven.py` (run by `.github/workflows/eleven.yml`, manual `workflow_dispatch`) makes only files that don't exist yet.
  Item types and fields are documented at the top of `tools/eleven.py`: `tts`, `sfx`, `design`, `search`.
- Budget per run (`config.json`): 2000 text chars, 10 sound effects. Over budget → nothing is made. A failed item doesn't stop the rest.
- `voices.json` (root) is refreshed every run: the voices in the account.

## Adding sounds for an app
1. Add items to `projects/<app>/list.json` (create the folder for a new app). Use a new file name for every new try –
   an existing file is never regenerated. To redo a file, delete the mp3 or use a new name.
2. Commit + push to `main`.
3. Start the workflow: `gh api -X POST repos/mazivco-design/SOUNDS/actions/workflows/eleven.yml/dispatches -f ref=main`
   (optional: `-f 'inputs[project]=<app>'`). Wait for the run (`.../actions/workflows/eleven.yml/runs?per_page=1`), then `git pull`.
4. Send the owner the mp3s to listen to before wiring them into the app.

## Using the files in an app
- URL: `https://mazivco-design.github.io/SOUNDS/projects/<app>/<file>.mp3` (GitHub Pages, branch `main`, root).
  All of the owner's Pages sites share the origin `mazivco-design.github.io`, so `fetch`/Web Audio works with no CORS issue.
- Or copy the mp3 into the app's own repo (safer for offline / cache control). Trim silence and normalize with ffmpeg if needed:
  `silenceremove` at both ends, `loudnorm=I=-16:TP=-1.5`.

## Known limits / lessons (from ninja-voice-game)
- The key has no `voices_write` permission: library voices are used directly by `voice_id` (find them with a `search` item).
- ElevenLabs blocks voice *design* from a description that mentions a child or an age.
- `eleven_v3` with emotion tags like `[worried]`, `[happy]` sounds natural; `stability` 1.0 + `seed` 42 = consistent but flatter,
  0.5 = livelier. Strong tags (`[panicked] [shouting]`) can sound hysterical.
- Voices chosen so far (ninja-voice-game): Sarah `[warm]` (narrator/demo words), Harry `[worried]` (ninja), Lukas (friend ninja,
  library id wSqOdjeNqDrHcoK0zorF), Teddy Twinkle (cart kid, library id XjGYkUkzth8BPs29fmcV), Roger (merchant).
  ninja-voice-game still has its own copy of this setup in `audio/eleven/` – leave it as is.

"""ElevenLabs generator for all of the apps – runs inside GitHub Actions (the API key lives only there, as a secret).

Every app has its own folder: projects/<app>/list.json. The finished files are saved next to the list,
so projects/<app>/<file>.mp3 is served at https://mazivco-design.github.io/SOUNDS/projects/<app>/<file>.mp3
Only files that don't exist yet are made (credits are never spent twice).

List entries (projects/<app>/list.json → {"items": [...]}):
  {"file": "help", "type": "tts", "text": "Help!", "voice": "Sarah", "model": "eleven_v3", "seed": 42, "settings": {"stability": 0.5}}
  {"file": "help", "type": "tts", "text": "Help!", "voice_id": "<library voice id>"}   # library voices work by id, no need to add them
  {"file": "sfx-mud", "type": "sfx", "text": "soft mud splash", "seconds": 1.2}
  {"file": "design-x", "type": "design", "description": "...", "text": "100+ chars", "count": 3}
  {"file": "lib-heroes", "type": "search", "params": {"search": "hero", "gender": "male", "page_size": 30}}
An item that fails doesn't stop the others – whatever was made is still saved.
Run for one app only: PROJECT=<app> (the workflow's "project" input).
"""
import base64, glob, json, os, sys, urllib.request, urllib.error
from urllib.parse import urlencode

KEY = os.environ.get('ELEVENLABS_API_KEY', '').strip()
ONLY = os.environ.get('PROJECT', '').strip()
API = 'https://api.elevenlabs.io/v1'
cfg = json.load(open('config.json', encoding='utf-8'))
BUDGET_CHARS, MAX_SFX = cfg.get('budget_chars', 2000), cfg.get('max_sfx', 10)
MODEL = cfg.get('model', 'eleven_multilingual_v2')

if not KEY: sys.exit('ELEVENLABS_API_KEY secret is missing')


class ApiError(Exception):
    pass


def call(method, path, body=None):
    req = urllib.request.Request(API + path, method=method, headers={'xi-api-key': KEY, 'Content-Type': 'application/json'},
                                 data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        raise ApiError(f'{method} {path} -> HTTP {e.code}: {e.read()[:400]!r}')


def done(d, it):
    if it['type'] == 'search': return os.path.exists(f"{d}/{it['file']}.json")
    if it['type'] == 'design': return os.path.exists(f"{d}/{it['file']}-1.mp3")
    return os.path.exists(f"{d}/{it['file']}.mp3")


todo = []                                                             # (folder, item) for every app
for lst in sorted(glob.glob('projects/*/list.json')):
    d = os.path.dirname(lst)
    if ONLY and os.path.basename(d) != ONLY: continue
    todo += [(d, it) for it in json.load(open(lst, encoding='utf-8'))['items'] if not done(d, it)]

chars = sum(len(it['text']) for _, it in todo if it['type'] in ('tts', 'design'))
sfx = sum(1 for _, it in todo if it['type'] == 'sfx')
print(f'to make: {len(todo)} items, {chars} text chars, {sfx} sound effects')
if chars > BUDGET_CHARS or sfx > MAX_SFX:
    sys.exit(f'over budget (chars {chars}/{BUDGET_CHARS}, sfx {sfx}/{MAX_SFX}) – nothing made')

voices = json.loads(call('GET', '/voices'))['voices']
slim = [{'name': v['name'], 'id': v['voice_id'], 'category': v.get('category'), 'labels': v.get('labels'), 'description': v.get('description')} for v in voices]
json.dump(slim, open('voices.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
by_name = {v['name'].split(' ')[0].split('-')[0].strip().lower(): v['voice_id'] for v in voices}
by_name.update({v['name'].lower(): v['voice_id'] for v in voices})

failed = 0
for d, it in todo:
    name = f"{d}/{it['file']}"
    try:
        if it['type'] == 'search':                                       # חיפוש בספרייה הגדולה – שומרים את התוצאות
            res = json.loads(call('GET', '/shared-voices?' + urlencode(it['params'])))
            out = [{'name': v.get('name'), 'voice_id': v.get('voice_id'), 'accent': v.get('accent'), 'age': v.get('age'),
                    'gender': v.get('gender'), 'use_case': v.get('use_case'), 'descriptive': v.get('descriptive'),
                    'description': (v.get('description') or '')[:200], 'preview_url': v.get('preview_url')}
                   for v in res.get('voices', [])]
            json.dump(out, open(f'{name}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            print('made', name, len(out), 'voices'); continue
        if it['type'] == 'tts':
            vid = it.get('voice_id') or by_name.get(it.get('voice', '').lower())
            if not vid:
                print(f"!! voice {it.get('voice')} not found – skipped {name}"); failed += 1; continue
            body = {'text': it['text'], 'model_id': it.get('model', MODEL)}
            if 'settings' in it: body['voice_settings'] = it['settings']
            if 'seed' in it: body['seed'] = it['seed']
            audio = call('POST', f'/text-to-speech/{vid}?output_format=mp3_44100_128', body)
            open(f'{name}.mp3', 'wb').write(audio)
            print('made', name, len(audio), 'bytes')
        elif it['type'] == 'design':                                   # קול חדש לפי תיאור – כל דוגמה נשמרת כקובץ
            body = {'voice_description': it['description'], 'text': it['text'], 'model_id': it.get('model', 'eleven_ttv_v3')}
            res = json.loads(call('POST', '/text-to-voice/design', body))
            meta = []
            for i, pv in enumerate(res.get('previews', [])[:it.get('count', 3)]):
                open(f'{name}-{i + 1}.mp3', 'wb').write(base64.b64decode(pv['audio_base_64']))
                meta.append({'file': f"{it['file']}-{i + 1}", 'generated_voice_id': pv.get('generated_voice_id')})
                print('made', f'{name}-{i + 1}')
            json.dump(meta, open(f'{name}.json', 'w'), indent=1)
        else:                                                          # sfx – אפקט קול לפי תיאור
            body = {'text': it['text'], 'prompt_influence': it.get('influence', 0.5)}
            if 'seconds' in it: body['duration_seconds'] = it['seconds']
            audio = call('POST', '/sound-generation?output_format=mp3_44100_128', body)
            open(f'{name}.mp3', 'wb').write(audio)
            print('made', name, len(audio), 'bytes')
    except ApiError as e:
        failed += 1
        print('!!', name, e)

if failed: print(f'!! {failed} item(s) failed')

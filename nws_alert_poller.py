#!/usr/bin/env python3
import json, os, subprocess, urllib.request, urllib.error, hashlib, re, time
from pathlib import Path

SUBS_FILE   = Path("/etc/asterisk/nws_subscriptions.json")
SOUNDS_DIR  = Path("/var/lib/asterisk/sounds/custom")
STATE_FILE  = Path("/var/lib/asterisk/nws_alert_state.json")

USER_AGENT  = os.getenv("NWS_USER_AGENT", "FreePBX-NWS-Alert/1.0 (contact: yourname@example.com)")
NWS_URL     = "https://api.weather.gov/alerts/active?status=actual&message_type=alert,update"

CACHE_PREFIX   = "nws_"
CACHE_TTL_SECS = 2 * 24 * 3600

def load_json(path, default):
    try: return json.loads(path.read_text())
    except Exception: return default

def save_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2))

def fetch_alerts():
    req = urllib.request.Request(NWS_URL, headers={"User-Agent": USER_AGENT, "Accept": "application/geo+json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.load(resp).get("features", [])
    except urllib.error.HTTPError as e:
        try: body = e.read().decode("utf-8", "ignore")
        except Exception: body = ""
        print(f"NWS HTTPError {e.code}: {e.reason}\n{body}")
        return []
    except urllib.error.URLError as e:
        print(f"NWS URLError: {e}")
        return []

def sanitize_id(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "_", s)[:80]

def _first_ref_id_from_string(refs_str: str):
    m = re.search(r'[^,\s]+,([^,\s]+),[^,\s]+', refs_str or "")
    return m.group(1) if m else None

def canonical_alert_group_id(props: dict) -> str:
    refs = props.get("references")
    ref_id = None
    if isinstance(refs, str):
        ref_id = _first_ref_id_from_string(refs)
    elif isinstance(refs, list):
        for item in refs:
            if isinstance(item, str):
                ref_id = _first_ref_id_from_string(item)
                if ref_id: break
    if ref_id: return ref_id
    return props.get("id") or hashlib.sha1(json.dumps(props, sort_keys=True).encode()).hexdigest()

def tts_wav16_base(text: str, same_code: str, group_id: str) -> str:
    SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
    gid_short = sanitize_id(group_id) or hashlib.sha1(group_id.encode()).hexdigest()[:10]
    base = f"{CACHE_PREFIX}{same_code}_{gid_short}"
    final_wav = SOUNDS_DIR / f"{base}.wav"
    final_wav16 = SOUNDS_DIR / f"{base}.wav16"
    if final_wav16.exists():
        return f"custom/{base}"
    tmp_in  = Path("/tmp/nws_tts_in.wav")
    tmp_out = Path("/tmp/nws_tts_out.wav")
    subprocess.run(["pico2wave","-l","en-US","-w",str(tmp_in), text], check=True)
    subprocess.run(["sox", str(tmp_in), "-r","16000","-c","1","-b","16","-e","signed-integer", str(tmp_out), "norm","-3"], check=True)
    if final_wav.exists(): final_wav.unlink(missing_ok=True)
    if final_wav16.exists(): final_wav16.unlink(missing_ok=True)
    tmp_out.replace(final_wav)
    final_wav.rename(final_wav16)
    try:
        import pwd, grp
        os.chown(final_wav16, pwd.getpwnam("asterisk").pw_uid, grp.getgrnam("asterisk").gr_gid)
    except Exception:
        pass
    os.chmod(final_wav16, 0o644)
    try: tmp_in.unlink(missing_ok=True)
    except Exception: pass
    return f"custom/{base}"

def page_extension(ext: str, playback_base: str):
    subprocess.run([
        "asterisk","-rx",
        f"channel originate Local/*80{ext}@from-internal application Playback {playback_base}"
    ], check=False)

def cleanup_old_audio():
    now = time.time()
    for p in SOUNDS_DIR.glob(f"{CACHE_PREFIX}*.wav16"):
        try:
            if now - p.stat().st_mtime > CACHE_TTL_SECS: p.unlink()
        except Exception: pass
    for p in SOUNDS_DIR.glob(f"{CACHE_PREFIX}*.wav"):
        try:
            if now - p.stat().st_mtime > CACHE_TTL_SECS: p.unlink()
        except Exception: pass

def main():
    subs = load_json(SUBS_FILE, [])
    state = load_json(STATE_FILE, {"seen_pairs": []})
    seen_pairs = set(state.get("seen_pairs", []))  # "<group_id>|<ext>"

    alerts = fetch_alerts()
    new_seen_pairs = set(seen_pairs)

    for f in alerts:
        props = f.get("properties", {}) or {}
        same_list = (props.get("geocode", {}) or {}).get("SAME", []) or []
        if not same_list: continue

        group_id = canonical_alert_group_id(props)

        event    = props.get("event","Weather Alert")
        area     = props.get("areaDesc","")
        headline = props.get("headline","")
        msg = f"National Weather Service. {event}. Affected area: {area}. {headline}"
        if len(msg) > 900: msg = msg[:900] + "..."

        ext_to_code = {}
        for sub in subs:
            ext = sub.get("extension")
            codes = sub.get("codes", [])
            if not ext or not codes: continue
            inter = sorted(set(codes).intersection(same_list))
            if not inter: continue
            if f"{group_id}|{ext}" in seen_pairs: continue
            ext_to_code[ext] = inter[0]

        if not ext_to_code: continue

        code_to_playbase = {}
        for code in sorted(set(ext_to_code.values())):
            try: code_to_playbase[code] = tts_wav16_base(msg, code, group_id)
            except Exception as e: print(f"TTS fail for code {code} group {group_id}: {e}")

        for ext, code in ext_to_code.items():
            playbase = code_to_playbase.get(code)
            if not playbase: continue
            try:
                page_extension(ext, playbase)
                new_seen_pairs.add(f"{group_id}|{ext}")
            except Exception as e:
                print(f"Page fail ext {ext} group {group_id}: {e}")

    save_json(STATE_FILE, {"seen_pairs": sorted(new_seen_pairs)})
    cleanup_old_audio()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import sys, os, json, re, hashlib, subprocess, tempfile
from pathlib import Path

DB = Path("/etc/asterisk/nws_subscriptions.json")
SOUNDS_DIR = Path("/var/lib/asterisk/sounds/custom")
VOICE = "en-US"

def load_db():
    try:
        return json.loads(DB.read_text())
    except Exception:
        return []

def save_db(data):
    DB.parent.mkdir(parents=True, exist_ok=True)
    DB.write_text(json.dumps(data, indent=2))

def upsert_code(ext, code):
    data = load_db()
    row = next((r for r in data if r.get("extension") == ext), None)
    if not row:
        row = {"extension": ext, "codes": []}
        data.append(row)
    if code not in row["codes"]:
        row["codes"].append(code)
        save_db(data)

def remove_code(ext, code):
    data = load_db()
    for r in data:
        if r.get("extension") == ext and code in r.get("codes", []):
            r["codes"] = [c for c in r["codes"] if c != code]
            save_db(data)
            return True
    return False

def list_codes(ext):
    for r in load_db():
        if r.get("extension") == ext:
            return r.get("codes", [])
    return []

def agi_read_env():
    while True:
        line = sys.stdin.readline()
        if not line or line.strip() == "":
            break

def agi_cmd(cmd):
    sys.stdout.write(cmd.strip() + "\n")
    sys.stdout.flush()
    sys.stdin.readline()

def speak_tts(text):
    SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
    base = "tts_" + hashlib.sha1(text.encode()).hexdigest()[:12]
    raw = Path(tempfile.gettempdir()) / (base + ".wav")
    final = SOUNDS_DIR / (base + ".wav")
    final16 = SOUNDS_DIR / (base + ".wav16")
    subprocess.run(["pico2wave", "-l", VOICE, "-w", str(raw), text], check=True)
    subprocess.run([
        "sox", str(raw), "-r", "16000", "-c", "1", "-b", "16", "-e", "signed-integer",
        str(final), "norm", "-3"
    ], check=True)
    if final16.exists():
        final16.unlink(missing_ok=True)
    final.rename(final16)
    try:
        os.chown(final16, os.getpwnam("asterisk").pw_uid, os.getgrnam("asterisk").gr_gid)  # type: ignore
    except Exception:
        pass
    agi_cmd(f"STREAM FILE custom/{base} \"\"")
    try:
        raw.unlink(missing_ok=True)
    except Exception:
        pass

def main():
    agi_read_env()
    args = dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a)
    mode = args.get("mode", "").strip()
    ext = re.sub(r"\D", "", args.get("ext", ""))
    code = re.sub(r"\D", "", args.get("code", ""))

    if not ext:
        speak_tts("Sorry. No extension detected.")
        return

    if mode == "add":
        if len(code) != 6:
            speak_tts("Invalid code.")
            return
        upsert_code(ext, code)
        speak_tts("Code saved. Thank you.")
        return

    if mode == "remove":
        if len(code) != 6:
            speak_tts("Invalid code.")
            return
        ok = remove_code(ext, code)
        speak_tts("Code removed." if ok else "That code was not found.")
        return

    if mode == "list":
        codes = list_codes(ext)
        if not codes:
            speak_tts("You are not subscribed to any codes.")
        else:
            speak_tts("You are subscribed to the following codes: " + ", ".join(codes))
        return

    speak_tts("Unknown request.")
    return

if __name__ == "__main__":
    main()

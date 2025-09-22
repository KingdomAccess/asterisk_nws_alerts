# FreePBX NWS SAME Alert System

Deliver **National Weather Service (NWS)** alerts to FreePBX phones via **auto-answer paging** with **local text-to-speech (TTS)**.
Users subscribe by dialing a menu, entering their **SAME (FIPS) codes**, and will be auto-called when matching alerts are active.

---

## What’s Included (repo files)

| Repo file                  | Purpose                                                                |
| -------------------------- | ---------------------------------------------------------------------- |
| `same_subs.py`             | AGI script for users to **add/remove/list** SAME codes by phone        |
| `extensions_custom.conf`   | Dialplan additions (binds **7788** to the subscription menu)           |
| `generatePrompts.sh`       | Generates the **menu audio prompts** (wideband)                        |
| `nws_alert_poller.py`      | Polls NWS API, generates TTS audio, **auto-answers** target extensions |
| `nws-alert-poller.service` | systemd unit to keep the poller running continuously                   |

> **Important:** Where this guide says `you@domain.com`, change it to **your real email**. NWS requires a valid contact in the User-Agent.

---

## Requirements

* A working **FreePBX/Asterisk** system
* Linux shell access (root)
* Packages: `libttspico-utils` (pico2wave TTS), `sox`

```bash
apt-get update
apt-get install -y libttspico-utils sox
```

---

## Install (step-by-step)

### 1) Copy files to their destinations

```bash
# AGI (subscription menu backend)
cp same_subs.py /var/lib/asterisk/agi-bin/

# Dialplan additions (subscription menu on 7788)
cp extensions_custom.conf /etc/asterisk/

# Prompt generator (you can keep it in the repo root or move it)
cp generatePrompts.sh /usr/local/bin/

# Poller (fetch NWS alerts + place auto-answer calls)
cp nws_alert_poller.py /usr/local/bin/

# Systemd unit (keeps the poller running)
cp nws-alert-poller.service /etc/systemd/system/
```

### 2) Make scripts executable (and set AGI ownership)

```bash
chmod +x /var/lib/asterisk/agi-bin/same_subs.py
chown asterisk:asterisk /var/lib/asterisk/agi-bin/same_subs.py

chmod +x /usr/local/bin/nws_alert_poller.py
chmod +x /usr/local/bin/generatePrompts.sh 2>/dev/null || true
chmod +x generatePrompts.sh 2>/dev/null || true
```

### 3) Generate the menu prompts

This script creates the audio used by the phone menu (7788) into FreePBX’s sounds directory.
If you want to change the wording later, edit `generatePrompts.sh` and rerun it.

```bash
./generatePrompts.sh
```

> If the script isn’t in your current directory, run `/usr/local/bin/generatePrompts.sh`.

### 4) Reload FreePBX to load the new dialplan

```bash
fwconsole reload
```

### 5) Configure and start the poller (systemd)

1. **Edit `nws-alert-poller.service`** and replace the placeholder email:

   * Find `Environment=NWS_USER_AGENT=FreePBX-NWS-Alert/1.0 (contact: you@domain.com)`
   * Change to your real email (e.g., `ops@yourcompany.com`).

2. **Enable and start the service:**

   ```bash
   systemctl daemon-reload
   systemctl enable --now nws-alert-poller
   systemctl status nws-alert-poller
   ```

---

## FreePBX / Phone Settings

* **Intercom / Auto-Answer:**
  In FreePBX, ensure the **Intercom prefix** (typically `*80`) is **enabled** (Admin → Feature Codes).
  On phones, enable “Auto Answer by Call-Info/Alert-Info” (name varies by vendor).

* **Wideband (HD) audio:**
  Enable **G.722** on extensions/phones and in FreePBX so alerts and prompts play in higher quality.

---

## How It Works (user flow)

1. **Subscribe by phone:**
   Dial **7788** from any extension:

   * Press **1** to add a 6-digit SAME code
   * Press **2** to remove a code
   * Press **3** to hear your current codes

2. **When an alert is active:**
   The poller:

   * Queries the NWS API with a valid User-Agent (includes your email)
   * Matches each alert’s SAME codes to your subscribers
   * Generates an HD TTS file (per SAME code + alert thread)
   * **Auto-answers** target extensions using the FreePBX intercom prefix

3. **No duplicates:**
   Each extension is called **once per alert thread** (initial + updates), even if multiple SAME codes match.

---

## Data & Audio Locations (FYI)

* Subscriptions (written by the menu/AGI):
  `/etc/asterisk/nws_subscriptions.json`

* De-duplication state (written by poller):
  `/var/lib/asterisk/nws_alert_state.json`

* Audio cache (per SAME + alert group), wideband:
  `/var/lib/asterisk/sounds/custom/nws_<SAME>_<GROUP>.wav16`

---

## Testing & Troubleshooting

* **Dialplan loaded?**

  ```bash
  asterisk -rx "dialplan show 7788@from-internal"
  ```

* **Reload after changes:**

  ```bash
  fwconsole reload
  ```

* **Poller logs:**

  ```bash
  journalctl -xeu nws-alert-poller --no-pager
  ```

* **Sounds directory permissions (if you see write errors):**

  ```bash
  mkdir -p /var/lib/asterisk/sounds/custom
  chown -R asterisk:asterisk /var/lib/asterisk/sounds/custom
  chmod -R 755 /var/lib/asterisk/sounds/custom
  ```

---

## Notes & Reminders

* Replace **`you@domain.com`** anywhere it appears with your **real, reachable email address**.
  The NWS API rejects generic/missing User-Agents.

* Ensure your phones/extensions negotiate **G.722** to actually hear HD audio; otherwise Asterisk will transcode to narrowband.

* This project is a starting point—harden and monitor your PBX according to your environment’s best practices.

---

If you get stuck on any step, open an issue with your **FreePBX version**, a **snippet of `journalctl -xeu nws-alert-poller`**, and what you’ve tried so far.

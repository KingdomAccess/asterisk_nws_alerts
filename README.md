# FreePBX NWS SAME Alert System

## 🌩 How It Works (Quick Start)

This system transforms your FreePBX into a **live weather alerting platform** with alerts from the **National Weather Service (NWS) API**. Once installed:

1. **Dial the SAME menu extension** (default **7788**, customizable in `extensions_custom.conf`).

   * Press **1** → Add a SAME (FIPS) code (6 digits)
   * Press **2** → Remove a SAME code
   * Press **3** → Hear a list of your subscribed SAME codes

2. **Sit back and relax** ☕
   When the NWS issues an alert for any of your SAME codes:

   * The system **immediately fetches the alert**
   * Generates **crystal-clear HD audio** using local text-to-speech
   * Your phone **auto-answers via intercom** and plays the warning
   * The call will display as **System Alert** instead of “Unknown Caller”

3. **No spam, no repeats**
   Each extension gets called **once per alert thread** (initial + updates), even if multiple SAME codes overlap.

⚡ In short: you’ll never miss a weather warning again, and your PBX becomes the smartest, fastest alerting tool around.

---

## What’s Included (repo files)

| Repo file                  | Purpose                                                                |
| -------------------------- | ---------------------------------------------------------------------- |
| `same_subs.py`             | AGI script for users to **add/remove/list** SAME codes by phone        |
| `extensions_custom.conf`   | Dialplan additions (binds SAME menu to an extension, default **7788**) |
| `generatePrompts.sh`       | Generates the **menu audio prompts** (wideband)                        |
| `nws_alert_poller.py`      | Polls NWS API, generates TTS audio, **auto-answers** target extensions |
| `nws-alert-poller.service` | systemd unit to keep the poller running continuously                   |
| `multiPage.sh`             | Manual sender script to page multiple extensions with TTS + delay      |

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

# Manual pager (for testing or ad-hoc alerts)
cp multiPage.sh /usr/local/bin/
```

### 2) Make scripts executable (and set AGI ownership)

```bash
chmod +x /var/lib/asterisk/agi-bin/same_subs.py
chown asterisk:asterisk /var/lib/asterisk/agi-bin/same_subs.py

chmod +x /usr/local/bin/nws_alert_poller.py
chmod +x /usr/local/bin/generatePrompts.sh
chmod +x /usr/local/bin/multiPage.sh
```

### 3) Generate the menu prompts

```bash
/usr/local/bin/generatePrompts.sh
```

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

## Customization

* **SAME Menu Extension:**
  Default is **7788**. Change it in `extensions_custom.conf` under `[from-internal-custom]`.

* **Caller ID for Alerts:**
  Pages display as **System Alert** with number **0000**. Change the name/number in:

  * `nws_alert_poller.py` → `page_extension()` function
  * `multiPage.sh` → the `asterisk -rx` line

* **Pre-play Delay:**
  Some phones take a second to auto-answer. Delay is handled by chaining `silence/1` files before playback.

  * Change default seconds in systemd unit:

    ```
    Environment=NWS_PREWAIT_SEC=2
    ```
  * Or override per manual page run:

    ```bash
    ./multiPage.sh -e 1001 -m "Test" -d 3
    ```

* **User-Agent Contact Email:**
  Change `you@domain.com` to your real, reachable email in the systemd unit. Required by NWS.

---

## FreePBX / Phone Settings

* **Intercom / Auto-Answer:**
  In FreePBX, ensure the **Intercom prefix** (typically `*80`) is **enabled** (Admin → Feature Codes).
  On phones, enable “Auto Answer by Call-Info/Alert-Info” (name varies by vendor).

* **Wideband (HD) audio:**
  Enable **G.722** on extensions/phones and in FreePBX so alerts and prompts play in higher quality.

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

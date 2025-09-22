📡 FreePBX NWS SAME Alert System

This project integrates the National Weather Service (NWS) Alerts API with FreePBX to automatically deliver voice alerts via paging/intercom to selected extensions.

Users can dial into a special menu, subscribe to their SAME (FIPS) codes, and automatically receive text-to-speech (TTS) alerts when warnings are issued for their area.

✨ Features

User Menu (extension 7788)

Press 1 → Add a SAME code

Press 2 → Remove a SAME code

Press 3 → List current codes

Automatic Paging

Polls the NWS API for active alerts

Generates high-quality audio using local TTS

Auto-answers phones via the FreePBX intercom prefix (*80)

De-duplication

Each extension receives each alert only once, even if it covers multiple SAME codes

Easy Testing

Manual script provided to send test TTS messages to any extension

📂 Repository Contents

same_subs.py
Handles subscription logic (add/remove/list SAME codes).

extensions_custom.conf
Custom FreePBX dialplan additions (binds extension 7788 to the menu).

generatePrompts.sh
Helper script to generate the audio prompts used by the subscription menu.

nws_alert_poller.py
Polls the NWS API, generates alert audio, and originates paging calls.

nws-alert-poller.service
A systemd service unit file to keep the poller running continuously.

🚀 Installation

Dependencies
Install required tools:

apt-get update
apt-get install -y libttspico-utils sox


Deploy files
Copy each file from this repo to its destination:

same_subs.py → /var/lib/asterisk/agi-bin/

extensions_custom.conf → /etc/asterisk/

generatePrompts.sh → Anywhere convenient (e.g. /usr/local/bin/)

nws_alert_poller.py → /usr/local/bin/

nws-alert-poller.service → /etc/systemd/system/

Make scripts executable:

chmod +x /var/lib/asterisk/agi-bin/same_subs.py
chmod +x /usr/local/bin/nws_alert_poller.py
chmod +x generatePrompts.sh


Generate prompts
Run:

./generatePrompts.sh


This will create the menu audio files inside FreePBX’s sounds directory.

Reload FreePBX

fwconsole reload


Enable the poller service
Update the systemd service file (nws-alert-poller.service) with your email address in the NWS_USER_AGENT environment variable (e.g., replace you@domain.com).
Then run:

systemctl daemon-reload
systemctl enable --now nws-alert-poller

🧪 Testing

Dial 7788 from any extension to subscribe to a SAME code.

Check logs for the poller:

journalctl -xeu nws-alert-poller --no-pager


To force a test message, use the manual paging script (not in repo, but included in instructions):

./nws_tts_page.sh -e 1001 -m "This is a test of the paging system."

🔧 Customization

Email Address
Update nws-alert-poller.service and replace you@domain.com with your actual contact email.
NWS requires a valid User-Agent string when hitting their API.

Extension Numbers
Adjust the intercom prefix (*80) or the subscription menu extension (7788) in extensions_custom.conf if needed.

Codecs
Enable G.722 (wideband) on your phones and in FreePBX for higher-quality audio.

🛠 Troubleshooting

No audio or garbled prompts?
Ensure libttspico-utils and sox are installed.

No alerts arriving?
Check /etc/asterisk/nws_subscriptions.json — subscriptions must exist.

Phones not auto-answering?
Confirm *80 intercom prefix is enabled in FreePBX and phones are set to trust intercom auto-answer.

📧 Notes

This project is a starting point — it’s up to you to maintain and secure your FreePBX server.

Always replace placeholders like you@domain.com with real, valid details.

Alerts are issued immediately by the NWS API, but actual delivery depends on poller frequency and phone configuration.

✨ That’s it! Once installed, your FreePBX will call subscribed extensions with live NWS weather alerts.

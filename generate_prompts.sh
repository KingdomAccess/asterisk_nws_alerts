# Main menu
pico2wave -l en-US -w /tmp/same_main_raw.wav \
"NWS SAME code subscription menu... If you don't know the same codes for your area, please visit weather dot G O V slash N W R slash counties... Press 1 to add a code.. Press 2 to remove a code.. Press 3 to hear a list of your codes......."
sox /tmp/same_main_raw.wav -r 16000 -c 1 -b 16 -e signed-integer \
/var/lib/asterisk/sounds/custom/same-main-menu.wav norm -3
mv /var/lib/asterisk/sounds/custom/same-main-menu.wav \
   /var/lib/asterisk/sounds/custom/same-main-menu.wav16
rm -f /tmp/same_main_raw.wav

# Add prompt
pico2wave -l en-US -w /tmp/same_enter_raw.wav \
"Please enter your six digit S A M E code."
sox /tmp/same_enter_raw.wav -r 16000 -c 1 -b 16 -e signed-integer \
/var/lib/asterisk/sounds/custom/same-enter.wav norm -3
mv /var/lib/asterisk/sounds/custom/same-enter.wav \
   /var/lib/asterisk/sounds/custom/same-enter.wav16
rm -f /tmp/same_enter_raw.wav

# Remove prompt
pico2wave -l en-US -w /tmp/same_remove_raw.wav \
"Enter the S A M E code you wish to remove."
sox /tmp/same_remove_raw.wav -r 16000 -c 1 -b 16 -e signed-integer \
/var/lib/asterisk/sounds/custom/same-remove.wav norm -3
mv /var/lib/asterisk/sounds/custom/same-remove.wav \
   /var/lib/asterisk/sounds/custom/same-remove.wav16
rm -f /tmp/same_remove_raw.wav

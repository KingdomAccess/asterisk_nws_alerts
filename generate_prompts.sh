#!/bin/bash
set -euo pipefail

SOUNDS_DIR="/var/lib/asterisk/sounds/custom"
mkdir -p "$SOUNDS_DIR"

gen() {
  local text="$1"
  local base="$2"
  local tmp="/tmp/${base}_raw.wav"
  local out="$SOUNDS_DIR/${base}.wav"
  local out16="$SOUNDS_DIR/${base}.wav16"

  pico2wave -l en-US -w "$tmp" "$text"
  sox "$tmp" -r 16000 -c 1 -b 16 -e signed-integer "$out" norm -3
  mv -f "$out" "$out16"
  rm -f "$tmp"
}

# Prompts
gen ".NWS S A M E code subscription Menu. press 1 to add a code. Press 2 to remove a code. Press 3 to list your codes." "same-main-menu"
gen "Please enter your six digit S A M E code." "same-enter"
gen "Enter the S A M E code you wish to remove." "same-remove"

chown asterisk:asterisk "$SOUNDS_DIR"/same-*.wav16 || true
chmod 644 "$SOUNDS_DIR"/same-*.wav16
echo "Prompts generated in $SOUNDS_DIR (wav16)"

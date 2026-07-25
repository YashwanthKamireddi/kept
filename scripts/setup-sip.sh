#!/usr/bin/env bash
# Register a Twilio Elastic SIP Trunk with LiveKit as an OUTBOUND trunk, so the
# server can dial storytellers out. Produces the SIP_TRUNK_ID for .env.
#
# Prerequisites:
#   1. LiveKit CLI installed:  https://docs.livekit.io/home/cli/  (the `lk` binary)
#   2. Authenticated:          lk cloud auth           (opens a browser)
#   3. In Twilio: a SIP Trunk with a Termination URI (e.g. kept.pstn.twilio.com)
#      + a Credential List (username/password) + a Voice-capable phone number.
#
# Usage:
#   TWILIO_TERMINATION_URI=kept.pstn.twilio.com \
#   TWILIO_SIP_USER=youruser TWILIO_SIP_PASS=yourpass \
#   TWILIO_NUMBER=+1XXXXXXXXXX \
#   ./scripts/setup-sip.sh
set -euo pipefail

: "${TWILIO_TERMINATION_URI:?set TWILIO_TERMINATION_URI (e.g. kept.pstn.twilio.com)}"
: "${TWILIO_SIP_USER:?set TWILIO_SIP_USER (Twilio SIP credential-list username)}"
: "${TWILIO_SIP_PASS:?set TWILIO_SIP_PASS (Twilio SIP credential-list password)}"
: "${TWILIO_NUMBER:?set TWILIO_NUMBER (your Twilio number, E.164, e.g. +15551234567)}"

if ! command -v lk >/dev/null 2>&1; then
  echo "error: 'lk' (LiveKit CLI) not found. Install: https://docs.livekit.io/home/cli/" >&2
  exit 1
fi

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT
cat >"$tmp" <<JSON
{
  "trunk": {
    "name": "kept-twilio-outbound",
    "address": "${TWILIO_TERMINATION_URI}",
    "numbers": ["${TWILIO_NUMBER}"],
    "auth_username": "${TWILIO_SIP_USER}",
    "auth_password": "${TWILIO_SIP_PASS}"
  }
}
JSON

echo "Creating LiveKit outbound SIP trunk -> ${TWILIO_TERMINATION_URI} ..."
out="$(lk sip outbound create "$tmp")"
echo "$out"

trunk_id="$(printf '%s' "$out" | grep -oE 'ST_[A-Za-z0-9]+' | head -1 || true)"
if [ -n "$trunk_id" ]; then
  echo
  echo "SIP_TRUNK_ID=${trunk_id}"
  echo "Add that line to your .env (replacing the empty SIP_TRUNK_ID=)."
else
  echo "Trunk created, but couldn't parse the ST_ id from output — copy it from above into .env as SIP_TRUNK_ID=." >&2
fi

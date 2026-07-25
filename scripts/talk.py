"""Talk to Kept in your browser — ONE command, no external site, no tokens.

Starts the voice worker if it isn't already running, dispatches the 'katha'
agent into a room, writes a tiny local web page wired to that room, and opens
it. Click "Connect & Talk", allow your mic, and speak.

    uv run --package katha-voice python scripts/talk.py

Stop the worker afterwards with:  pkill -f 'katha_voice[.]worker'
"""

import asyncio
import pathlib
import subprocess
import sys
import time
import webbrowser
from datetime import timedelta

from katha_core.config import settings
from livekit import api

ROOM = "kept-test"
WORKER_LOG = "/tmp/kept-worker.log"


def ensure_worker() -> None:
    """Start the voice worker detached if it isn't already up, and wait for it
    to register with LiveKit. Leaves it running so the call can continue."""
    already = subprocess.run(
        ["pgrep", "-f", "katha_voice[.]worker"], capture_output=True, text=True
    ).stdout.strip()
    if already:
        print("Voice worker already running.")
        return
    print("Starting the voice worker…")
    with open(WORKER_LOG, "w") as logf:
        subprocess.Popen(
            [sys.executable, "-m", "katha_voice.worker", "dev"],
            stdout=logf,
            stderr=logf,
            start_new_session=True,  # survives this script exiting
        )
    for _ in range(45):
        time.sleep(1)
        try:
            if "registered worker" in pathlib.Path(WORKER_LOG).read_text():
                print("Voice worker registered.")
                return
        except FileNotFoundError:
            pass
    print(f"Worker didn't confirm registration in ~45s — see {WORKER_LOG}")

PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>Talk to Kept</title>
<style>
  body{font-family:Georgia,serif;background:#14181f;color:#f6f2e9;margin:0;height:100vh;
       display:flex;flex-direction:column;align-items:center;justify-content:center;gap:28px}
  h1{color:#c9a24b;font-weight:800;letter-spacing:.5px;margin:0}
  button{font:600 20px system-ui;padding:16px 34px;border:none;border-radius:12px;
         background:#c9a24b;color:#14181f;cursor:pointer}
  button:disabled{opacity:.5;cursor:default}
  #status{opacity:.75;font:15px system-ui;max-width:460px;text-align:center;line-height:1.5}
</style></head><body>
  <h1>Kept</h1>
  <button id="go">Connect &amp; Talk</button>
  <div id="status">Click connect, then allow your microphone and say hello.</div>
  <script src="https://cdn.jsdelivr.net/npm/livekit-client@2/dist/livekit-client.umd.min.js"></script>
  <script>
    const URL="__URL__", TOKEN="__TOKEN__";
    const st=document.getElementById('status'), go=document.getElementById('go');
    go.onclick=async()=>{
      go.disabled=true;
      try{
        st.textContent="Connecting…";
        const room=new LivekitClient.Room();
        room.on(LivekitClient.RoomEvent.TrackSubscribed,(track)=>{
          if(track.kind==='audio'){const el=track.attach();el.autoplay=true;document.body.appendChild(el);}
        });
        room.on(LivekitClient.RoomEvent.Disconnected,()=>{st.textContent="Call ended.";go.disabled=false;});
        await room.connect(URL,TOKEN);
        await room.localParticipant.setMicrophoneEnabled(true);
        st.textContent="Connected — say hello. Kept may take a few seconds to reply on the free brain.";
      }catch(e){st.textContent="Error: "+e.message+" — is the worker running?";go.disabled=false;}
    };
  </script>
</body></html>
"""


async def dispatch_and_open() -> None:
    s = settings()
    if not (s.livekit_url and s.livekit_api_key and s.livekit_api_secret):
        raise SystemExit("LiveKit keys missing in .env (LIVEKIT_URL/KEY/SECRET).")

    lk = api.LiveKitAPI(
        url=s.livekit_url, api_key=s.livekit_api_key, api_secret=s.livekit_api_secret
    )
    try:
        try:
            await lk.room.create_room(api.CreateRoomRequest(name=ROOM, metadata="{}"))
        except Exception:
            pass  # already exists
        await lk.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(agent_name="katha", room=ROOM, metadata="{}")
        )
    finally:
        await lk.aclose()

    token = (
        api.AccessToken(s.livekit_api_key, s.livekit_api_secret)
        .with_identity("keeper")
        .with_name("You")
        .with_ttl(timedelta(hours=2))
        .with_grants(api.VideoGrants(room_join=True, room=ROOM))
        .to_jwt()
    )

    out = pathlib.Path("/tmp/kept-talk.html")
    out.write_text(PAGE.replace("__URL__", s.livekit_url).replace("__TOKEN__", token))

    print("Kept is waiting in the room.")
    print(f"Opening {out} in your browser…")
    opened = webbrowser.open(f"file://{out}")
    if not opened:
        print(f"Couldn't auto-open. Open this file in your browser: file://{out}")
    print("Click 'Connect & Talk', allow the mic, and say hello.")


if __name__ == "__main__":
    ensure_worker()
    asyncio.run(dispatch_and_open())

# Be More Agent — Project Context

## What is this?
BrenPoly's **be-more-agent** running on a Raspberry Pi 5 (bmo) with DSI display (800x480), Ollama (gemma3:1b), Piper TTS. A BMO face assistant.

## Start
```bash
cd /home/mch/Projects/be-more-agent && ./start.sh
```
Launches `agent.py` on DISPLAY=:0 (Wayland + Xwayland).

## Gallery Server
- **URL**: http://192.168.3.86:9090/bmo-faces-gallery.html
- **Service**: `bmo-gallery.service` (systemd, enabled, auto-starts on boot)
- **Port**: 9090
- **Serves**: `faces/` directory with 28 expressions, also `faces_v2/`
- **Also available**: `bmo-faces-v1v2.html` (V1 vs V2 comparison)
- **DO NOT** start another server on another port — it's already running as a systemd service.

## Gallery service file
- Source: `bmo-gallery.service` in repo
- Installed to: `/etc/systemd/system/bmo-gallery.service`

## Git Remotes
| Remote | URL |
|--------|-----|
| `origin` | `https://github.com/brenpoly/be-more-agent.git` (upstream) |
| `acidfilez` | `https://github.com/acidfilez/be-more-agent.git` (fork) |

- `main` tracks `origin/main`
- `git push` defaults to `acidfilez` (fork)
- `git pull` on `main` pulls from `origin/main`

## Faces
- 28 expressions in `faces/` dir, all at 800x480
- BMO green background: `(189, 255, 203)` — except `frio` which uses blue `(200, 220, 240)`
- `faces_v2/` has corrected versions of some faces
- Gallery: `bmo-faces-gallery.html`

## Network (local LAN only — NO Tailscale)
- **bmo**: 192.168.3.86 (bmo.local)
- **xero-ai**: 192.168.3.38 (xero-ai.local)
- **mac-m1-fly**: 192.168.3.34 (mac-m1-fly.local)
- **mac-m1-meli**: 192.168.3.3 (mac-m1-meli.local)
- **simba-guard**: 192.168.3.100 (simba-guard.local)
- SSH to xero-ai: `ssh mch@xero-ai` (id_ed25519_fleet key)
- Use only local IPs (192.168.3.x) or mdns names (__.local). Never use Tailscale IPs.

## Environment
- Python 3.11.2, venv at `venv/`
- **CAM 313** webcam + mic conectados (`/dev/video0`, device "Live Streamer CAM 313: USB Audio")
- Pi zero W speaker via 3.5mm jack
- Modelos: gemma3:1b (ollama), piper TTS, openwakeword

# labwc rc.xml — BMO compositor config (documentation)

The labwc (Wayland compositor) configuration for BMO lives **outside this
repo**, because it is a per-user dotfile:

    ~/.config/labwc/rc.xml

This file documents its current content and purpose so the config is
tracked even though the file itself is not committed.

## Current content

```xml
<?xml version="1.0"?>
<openbox_config xmlns="http://openbox.org/3.4/rc">
	<touch deviceName="11-0038 generic ft5x06 (79)" mapToOutput="DSI-2" mouseEmulation="yes"/>
	<windowRules>
		<!-- BMO agent (tkinter) opens fullscreen at boot -->
		<windowRule title="Pi Assistant">
			<action name="ToggleFullscreen"/>
		</windowRule>
	</windowRules>
</openbox_config>
```

## Why the window rule exists

The BMO agent (`agent.py`) opens a tkinter window titled "Pi Assistant".
At boot the window used to come up windowed (200x200, desktop visible)
instead of fullscreen. Root cause chain:

1. `agent.py` originally called `master.attributes('-fullscreen', True)`.
   labwc 0.8.x does not honor that X11 property request the way a window
   manager like Openbox would, so the window mapped windowed.
2. A labwc window rule with the `ToggleFullscreen` **action** is applied
   on first map and does force fullscreen — but only if the client did
   *not* request fullscreen itself. When tkinter's `-fullscreen` attribute
   was set, labwc treated the window as already-fullscreen at map time and
   the toggle un-fullscreened it (net result: windowed again).
3. Fix: `agent.py` no longer sets `-fullscreen` (it sets
   `geometry("800x480+0+0")` as a fallback), and the labwc rule above is
   the single source of fullscreen.

## If the window is not fullscreen after a change

```bash
# Reload labwc config (window rules included)
LABWC_PID=$(pgrep -x labwc) labwc -r

# Restart the agent so its window re-maps under the rule
pkill -f 'venv/bin/python agent.py'
cd ~/Projects/be-more-agent && DISPLAY=:0 ./start.sh
```

## Related

- `agent.py` `BotGUI.__init__` — window setup + the comment explaining the
  labwc interaction.
- labwc docs: `man labwc-config` (window rules) and `man labwc-actions`
  (`ToggleFullscreen`).

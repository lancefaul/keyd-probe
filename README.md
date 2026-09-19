# keyd-probe

Find out what an input device actually sends, then scaffold a [keyd](https://github.com/rvaiya/keyd) config.

keyd remaps keys *by name*. So the first problem every keyd user hits isn't
"what should this key do" — it's **"what does this key even send?"**

Devices lie about this constantly:

- A four-key macropad ships as **numpad 1–4**, indistinguishable from a real numpad
- A volume knob ships as **consumer-control volume keys**, one event per detent
- A single physical device exposes **three or four separate kernel interfaces**,
  with its controls split across them
- A rotary encoder may be physically **unable** to report its button held while
  the shaft turns — which silently rules out an entire class of config

None of that is discoverable from the device's box, its manual, or keyd's
documentation. `keyd-probe` tells you, then writes the config skeleton.

## Usage

```console
$ keyd-probe list
Input devices, grouped by USB id (what keyd's [ids] matches):

  0816:246e  SDINNOVATION SIDE-KEYBOARD  [managed by keyd]
      /dev/input/event257  keyboard         (base)
      /dev/input/event30   keyboard         Keyboard
      /dev/input/event31   pointer          Mouse
      /dev/input/event256  keyboard         Wireless Radio Control
      4 interfaces - controls may be split across them
```

```console
$ sudo keyd-probe watch 0816:246e --config
Watching SDINNOVATION SIDE-KEYBOARD  (0816:246e)
  4 node(s): event30, event31, event256, event257

  down  KEY_KP1                keyd: kp1             event257  scancode=0x70059
  down  KEY_VOLUMEUP           keyd: volumeup        event30   scancode=0xc00e9
  down  KEY_MUTE               keyd: mute            event30   scancode=0xc00e2
  ...

Controls discovered

  evdev                  keyd name        interface    presses  notes
  -------------------------------------------------------------------
  KEY_KP1                kp1              event257           3  auto-repeats when held; held with KEY_KP2
  KEY_KP2                kp2              event257           3  held with KEY_KP1, KEY_KP3
  KEY_VOLUMEUP           volumeup         event30           11
  KEY_MUTE               mute             event30            3  auto-repeats when held

What this means
  - Controls are split across 2 interfaces (event257, event30). One [ids]
    section covers them all, since keyd matches by USB id.
  - 4 control(s) report as numpad keys (KEY_KP1, KEY_KP2, KEY_KP3, KEY_KP4).
    These are indistinguishable from a real numpad, so scope your config by USB
    id or you will remap the numpad on your main keyboard too.
  - KEY_MUTE (the knob press) never overlapped with rotation. If you tried
    pushing it in while turning, this encoder cannot report both at once —
    push-and-turn is impossible in ANY config. Use a latched layer instead:
    `mute = toggle(fast)`, tapped to switch modes.
  - Held simultaneously: KEY_KP1, KEY_KP2, KEY_KP3. Any of these can host a
    held-modifier layer, e.g. overload().
```

That last pair of findings is the point of the tool. Whether a knob can report
its button held *while* the shaft turns decides the entire shape of your config
— a held modifier versus a latched toggle — and nothing tells you except trying
it. That output is a real capture from a device where it turned out to be
impossible.

A device can be named three ways: USB id (`0816:246e`), event node (`event30`),
or a substring of its name (`side-keyboard`).

## Why not `keyd monitor`?

`keyd monitor` is genuinely useful and overlaps with this. The differences:

| | `keyd monitor` | `keyd-probe` |
|---|---|---|
| Scope | **Every device on the system** | One device you name |
| Privacy | Logs whatever you type anywhere, in plaintext | Opens only the device under test |
| Before a config exists | Needs keyd running | Works standalone |
| Grabbed devices | — | Detects and explains the grab |
| Output | Event stream | Stream **plus** a summary, quirk analysis, and a config skeleton |

The scoping difference is the important one. `keyd monitor` is an excellent
debugging tool and a poor discovery tool, because you cannot point it at one
device while you figure out what its buttons do.

## keyd's exclusive grab

keyd calls `EVIOCGRAB` on every device it manages
([`src/device.c`](https://github.com/rvaiya/keyd/blob/master/src/device.c)),
taking exclusive ownership. **While keyd manages a device, reading its raw
nodes returns nothing at all** — which looks exactly like broken hardware.

`keyd-probe` detects this and refuses, rather than handing back a silently
empty capture. It offers both ways forward:

```console
# See the RAW hardware — what the device really sends
systemctl stop keyd && keyd-probe watch <device> ; systemctl start keyd

# See keyd's OUTPUT — what your config turns it into
keyd-probe watch <device> --output
```

`--output` reads keyd's virtual devices, so it shows post-remap events. Those
carry only devices keyd manages, so nothing else on the system leaks in.

## Requirements

- Python 3.9+, standard library only
- Root (or membership of the `input` group) to read `/dev/input`
- `keyd` on `PATH` is optional — used to verify key names against
  `keyd list-keys`, and to detect which devices it manages

## Status

Early. It does what it says, but it has been exercised against a small number
of devices. Reports of devices it describes badly are the most useful thing you
can contribute — especially multi-interface devices and rotary encoders.

## Licence

MIT

#!/usr/bin/env python3
"""Exercise the reporting and config-generation paths with synthetic observations.

These are the parts that only run after a successful capture, so they are easy
to leave untested. The fixtures mimic a real multi-interface macropad: four keys
masquerading as numpad 1-4 on one interface, a rotary encoder reporting as
consumer-control volume keys on another.

The generated config is validated by piping it through `keyd check`, so this
asserts that keyd itself accepts our output rather than that it merely looks right.
"""

import importlib.machinery
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(os.path.dirname(HERE), "keyd-probe")

spec = importlib.util.spec_from_loader(
    "keydprobe", importlib.machinery.SourceFileLoader("keydprobe", TOOL)
)
kp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kp)

FAILURES = []


def check(condition, label):
    status = "ok  " if condition else "FAIL"
    print(f"  [{status}] {label}")
    if not condition:
        FAILURES.append(label)


def make_interface(name, node, vendor="0816", product="246e"):
    iface = kp.Interface(name, vendor, product)
    iface.handlers = [node, "kbd"]
    return iface


def make_observation(code, evdev_name, node, presses=2, repeats=0, overlaps=()):
    obs = kp.Observation(code, evdev_name, node)
    obs.presses = presses
    obs.repeats = repeats
    obs.overlapped_with = set(overlaps)
    return obs


def fixture_macropad(with_overlap):
    """Four numpad-masquerading keys plus an encoder, split across two interfaces."""
    seen = {
        79: make_observation(79, "KEY_KP1", "event257"),
        80: make_observation(80, "KEY_KP2", "event257"),
        81: make_observation(81, "KEY_KP3", "event257", repeats=5),
        75: make_observation(75, "KEY_KP4", "event257"),
        115: make_observation(115, "KEY_VOLUMEUP", "event30", presses=12),
        114: make_observation(114, "KEY_VOLUMEDOWN", "event30", presses=9),
        113: make_observation(113, "KEY_MUTE", "event30", presses=3),
    }
    if with_overlap:
        seen[113].overlapped_with = {"KEY_VOLUMEUP"}
        seen[115].overlapped_with = {"KEY_MUTE"}
    order = [79, 80, 81, 75, 115, 114, 113]
    return seen, order


def run():
    keyd_keys = kp.load_keyd_keys()
    print(f"keyd key table: {len(keyd_keys) or 'unavailable'} names")
    print()

    print("key-name translation")
    check(kp.to_keyd_name("KEY_KP1", keyd_keys) == "kp1", "KEY_KP1 -> kp1")
    check(kp.to_keyd_name("KEY_VOLUMEUP", keyd_keys) == "volumeup", "KEY_VOLUMEUP -> volumeup")
    check(kp.to_keyd_name("KEY_MUTE", keyd_keys) == "mute", "KEY_MUTE -> mute")
    check(kp.to_keyd_name("KEY_LEFTCTRL", keyd_keys) == "leftcontrol",
          "KEY_LEFTCTRL -> leftcontrol (alias, not the naive lowercase)")
    check(kp.to_keyd_name("KEY_ESC", keyd_keys) == "esc", "KEY_ESC -> esc")
    if keyd_keys:
        check(kp.to_keyd_name("KEY_TOTALLY_MADE_UP", keyd_keys) is None,
              "unknown key reports None rather than inventing a name")
    print()

    ifaces = [
        make_interface("SDINNOVATION SIDE-KEYBOARD", "event257"),
        make_interface("SDINNOVATION SIDE-KEYBOARD Keyboard", "event30"),
    ]
    check(kp.shared_name(ifaces) == "SDINNOVATION SIDE-KEYBOARD",
          "shared_name finds the common device name")
    print()

    print("quirk detection - encoder that CANNOT report press+turn")
    seen, order = fixture_macropad(with_overlap=False)
    buf = io.StringIO()
    with redirect_stdout(buf):
        kp.report("0816:246e", ifaces, seen, order, keyd_keys, emit_config=False)
    out = buf.getvalue()
    check("2 interfaces" in out, "reports controls split across interfaces")
    check("numpad" in out and "main keyboard" in out, "warns numpad keys collide with a real numpad")
    check("latched layer (toggle)" in out, "recommends a latch when nothing overlapped")
    check("auto-repeats" in out, "notes the key that auto-repeats")
    print()

    print("quirk detection - encoder that CAN report press+turn")
    seen, order = fixture_macropad(with_overlap=True)
    buf = io.StringIO()
    with redirect_stdout(buf):
        kp.report("0816:246e", ifaces, seen, order, keyd_keys, emit_config=False)
    out = buf.getvalue()
    check("held-modifier layer" in out, "recommends a held modifier when presses overlapped")
    check("latched layer (toggle)" not in out, "does not also recommend a latch")
    print()

    print("generated config")
    seen, order = fixture_macropad(with_overlap=False)
    config = kp.generate_config("0816:246e", ifaces, seen, order, keyd_keys)
    check("[ids]" in config and "0816:246e" in config, "contains an [ids] section with the USB id")
    check("[main]" in config, "contains a [main] section")
    check("kp1 = kp1" in config, "emits a line per discovered control")
    check("volumeup = volumeup" in config, "includes controls from the second interface")

    import shutil
    if shutil.which("keyd"):
        with tempfile.NamedTemporaryFile("w", suffix=".conf", delete=False) as handle:
            handle.write(config + "\n")
            path = handle.name
        try:
            result = subprocess.run(["keyd", "check", path],
                                    capture_output=True, text=True, timeout=15)
            check(result.returncode == 0 and "No errors" in result.stdout,
                  "keyd itself accepts the generated config")
            if result.returncode != 0:
                print("    keyd said:", result.stdout.strip(), result.stderr.strip())
        finally:
            os.unlink(path)
    else:
        print("  [skip] keyd not installed; cannot validate generated config")

    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for item in FAILURES:
            print(f"  - {item}")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(run())

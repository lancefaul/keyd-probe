# keyd-probe: notes for Claude

A command-line tool that identifies what an input device actually sends and scaffolds a keyd
config. It exists because, setting up a macropad, every blocker was discovery, not editing: no keyd
GUI exists, and a GUI needs reliable probing underneath anyway. It is deliberately a separate tool,
not a pull request into keyd. `README.md` is the user guide; `keyd-probe.1` is the man page.

**The repository is public** (`lancefaul/keyd-probe`, MIT): keep every tracked file free of personal
details.

## Rules

- **One file, standard library only** (`keyd-probe`, Python 3.9+). No dependencies; keyd itself is
  optional (it verifies key names and detects managed devices).
- **Run `python3 tests/test_report.py` before every commit.** It checks generated configs by piping
  them through `keyd check`, so keyd's own parser is the judge.
- **Three things that are easy to regress:**
  - keyd takes an exclusive `EVIOCGRAB` on the devices it manages, so their raw nodes emit nothing.
    The tool must refuse and say why, never return an empty capture as if the device were silent.
  - keyd has no trailing-comment syntax: only lines that *begin* with `#` are ignored. Generated
    configs put every note on its own line.
  - `pkexec` resets the working directory, so every command the tool suggests uses absolute paths.
- **Never run `watch` on a device unless the owner asks.** It reads raw input events (whatever is typed,
  passwords included) and needs root; ask which device first, and never point it at their keyboard to
  test something.
- Commit straight to `master`. Releases (GitHub plus the local package) follow the `release` skill.

## Skills learn

A lesson lands here or in the `release` skill in the same commit: a device that behaved
unexpectedly, a keyd change that broke a generated config, a release step that went wrong. Never
general advice, and never anything personal.

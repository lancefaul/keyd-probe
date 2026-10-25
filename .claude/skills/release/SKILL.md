---
name: release
description: Release a new keyd-probe version — bump the PKGBUILD, tag, GitHub release, refresh the checksum, build and install the local package, and confirm the installed copy is the new one. Use when Lance says "release", "cut 0.1.2", "publish keyd-probe", or "update the package". Pushing a tag and installing need his yes.
---

# Release

The version lives in two places only: the git tag `vX.Y.Z` and `pkgver` in
`packaging/aur/PKGBUILD`. There is no version string in the script. The
installed `/usr/bin/keyd-probe` comes from the locally built package
(`pacman -Q keyd-probe`); keyd-probe is **not** on the AUR — submitting it is
Lance's call.

## Steps

1. `python3 tests/test_report.py` (must say "all checks passed").
2. In `packaging/aur/PKGBUILD`: set `pkgver`, reset `pkgrel=1`. Commit to
   `master` with the change in the message.
3. **Tag and push** (his yes): `git tag vX.Y.Z && git push origin master vX.Y.Z`.
4. **GitHub release**:
   `gh release create vX.Y.Z -R lancefaul/keyd-probe --title "keyd-probe X.Y.Z" --notes-file <notes>`.
5. **Checksum**: the PKGBUILD downloads the tag's tarball, so this only works
   after step 3. `cd packaging/aur && updpkgsums`, then commit the new
   `sha256sums` and push.
6. **Build and install**: `cd packaging/aur && makepkg -f` (its `check()` runs
   the tests again), then install with `pkexec pacman -U keyd-probe-X.Y.Z-1-any.pkg.tar.zst`.
   `makepkg -si` would call `sudo`, which can't prompt here.
7. **Check what got installed**: `pacman -Q keyd-probe` shows `X.Y.Z-1`, and
   `cmp keyd-probe /usr/bin/keyd-probe` from the repo root prints nothing.

Build output (`src/`, `pkg/`, the tarball and the package) is git-ignored.

#!/bin/bash
# CI helper, run INSIDE the stock stanfordaha/garnet:latest container (built from aha
# master) after this garnet is copied to /aha/garnet. modern_gf needs the sibling-repo
# commits that aha's `mek` branch pins (lassen gen_PE_fc, lake THESIS, ...): check them
# out in the container's Python repos, which are editable installs, so a checkout is
# enough (untracked generated files stay). Compiled repos (coreir, clockwork, Halide's
# C++) stay as the image built them; Halide-to-Hardware gets only mek's app build scripts
# (hw_support: the header staging around map_app, ...). An entry is `repo` (whole
# checkout) or `repo:path` (that path's files only, copied in: the image's
# Halide-to-Hardware is not a git repository).
# Env: AHA_REF (default mek), AHA_DEPS_REPOS (default below), AHA_ROOT (default /aha).
set -eo pipefail
export GIT_TERMINAL_PROMPT=0
AHA_URL=${AHA_URL:-https://github.com/StanfordAHA/aha}
AHA_REF=${AHA_REF:-mek}
AHA_ROOT=${AHA_ROOT:-/aha}
REPOS=${AHA_DEPS_REPOS:-"lake lassen canal archipelago MetaMapper mflowgen Halide-to-Hardware:apps/hardware_benchmarks/hw_support"}

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
git -C "$tmp" init -q aha
git -C "$tmp/aha" fetch -q --depth=1 "$AHA_URL" "$AHA_REF"
git -C "$tmp/aha" show FETCH_HEAD:.gitmodules > "$tmp/gitmodules"
echo "$(git --version); aha $AHA_REF = $(git -C "$tmp/aha" rev-parse FETCH_HEAD)"

for entry in $REPOS; do
    r=${entry%%:*}
    path=
    [ "$r" != "$entry" ] && path=${entry#*:}
    sha=$(git -C "$tmp/aha" ls-tree FETCH_HEAD "$r" | awk '{print $3}')
    url=$(git config -f "$tmp/gitmodules" "submodule.$r.url")
    branch=$(git config -f "$tmp/gitmodules" "submodule.$r.branch" || echo mek)
    if [ -z "$sha" ] || [ -z "$url" ]; then
        echo "ERROR: aha $AHA_REF has no submodule $r"; exit 1
    fi
    echo "--- $r${path:+ ($path)}: $(git -C "$AHA_ROOT/$r" rev-parse --short HEAD 2>/dev/null) -> $sha ($url)"
    # Fetch over the network in a fresh repo (the image's own repos may carry config
    # that makes git ask for credentials), by commit or else via its branch...
    git -C "$tmp" init -q "$r"
    if ! git -C "$tmp/$r" -c protocol.version=2 fetch -q --depth=1 "$url" "$sha"; then
        git -C "$tmp/$r" fetch -q "$url" "$branch"
    fi
    git -C "$tmp/$r" cat-file -e "$sha^{commit}"
    git -C "$tmp/$r" branch -f aha-pin "$sha"
    if [ -n "$path" ]; then
        git -C "$tmp/$r" archive "$sha" "$path" | tar -x -C "$AHA_ROOT/$r"
    else
        # ...then hand it to the container's repo locally and check it out
        git -C "$AHA_ROOT/$r" fetch -q --update-shallow "$tmp/$r" aha-pin
        git -C "$AHA_ROOT/$r" checkout -q -f "$sha"
    fi
done

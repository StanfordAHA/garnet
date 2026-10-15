#!/bin/bash
# CI helper, run INSIDE the stock stanfordaha/garnet:latest container (built from aha
# master) after this garnet is copied to /aha/garnet. modern_gf needs the sibling-repo
# commits that aha's `mek` branch pins (lassen gen_PE_fc, lake THESIS, ...): check them
# out in the container's Python repos, which are editable installs, so a checkout is
# enough. Compiled repos (coreir, clockwork, Halide-to-Hardware) stay as the image built
# them. Env: AHA_REF (default mek), AHA_DEPS_REPOS (default below), AHA_ROOT (default /aha).
set -eo pipefail
AHA_URL=${AHA_URL:-https://github.com/StanfordAHA/aha}
AHA_REF=${AHA_REF:-mek}
AHA_ROOT=${AHA_ROOT:-/aha}
REPOS=${AHA_DEPS_REPOS:-"lake lassen canal archipelago MetaMapper mflowgen"}

tmp=$(mktemp -d)
git -C "$tmp" init -q
git -C "$tmp" fetch -q --depth=1 "$AHA_URL" "$AHA_REF"
git -C "$tmp" show FETCH_HEAD:.gitmodules > "$tmp/gitmodules"
echo "aha $AHA_REF = $(git -C "$tmp" rev-parse FETCH_HEAD)"
for r in $REPOS; do
    sha=$(git -C "$tmp" ls-tree FETCH_HEAD "$r" | awk '{print $3}')
    url=$(git config -f "$tmp/gitmodules" "submodule.$r.url")
    if [ -z "$sha" ] || [ -z "$url" ]; then
        echo "ERROR: aha $AHA_REF has no submodule $r"; exit 1
    fi
    echo "--- $r: $(git -C "$AHA_ROOT/$r" rev-parse --short HEAD 2>/dev/null) -> $sha ($url)"
    # GitHub serves any reachable commit by sha
    git -C "$AHA_ROOT/$r" fetch -q --depth=1 "$url" "$sha"
    git -C "$AHA_ROOT/$r" checkout -q -f "$sha"
done
rm -rf "$tmp"

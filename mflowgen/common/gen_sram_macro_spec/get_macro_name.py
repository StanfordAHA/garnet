"""Extract the SRAM macro name that Lake instantiated in the generated RTL and
build exactly that macro.

Lake instantiates the hardened SRAM as a child named ``mem_stub`` whose module
master is the full macro name (see lake ``memory_interface.py`` /
``spec/storage.py``: ``add_child("mem_stub", child_stub)`` and
``SRAMStubGenerator.__init__(sram_name)``). So the RTL contains a line like:

    IN12LP_S1DB_W02048B008M16S2_H mem_stub (

We recover the macro name (first token of that line) and hand it to
``gen_srams.sh``. The instance may be uniquified by the enclosing garnet build
(e.g. ``..._H_0_0``), so we do NOT rely on the instance name — we match the
macro *module* name pattern directly as a fallback.
"""
import os
import re
import subprocess

DESIGN_V = "inputs/design.v"

# IN12LP_<FAMILY>_W#####B###M##S#_<H|L>  (canonical GF12 macro master name).
# Anchored so the trailing H/L is the whole token (not the _0_0 of an instance).
_MACRO_RE = re.compile(
    r"\bIN12LP_(?:S1DB|S1PB|SDPB|R2PB)_W\d+B\d+M\d+S\d+_[HL]\b"
)

FAMILIES = ["S1DB", "S1PB", "SDPB", "R2PB"]


def _from_mem_stub_line(text):
    """First token of the `... mem_stub (` instantiation, if present."""
    for line in text.splitlines():
        if "mem_stub (" in line:
            tok = line.split()[0]
            if _MACRO_RE.fullmatch(tok):
                return tok
    return None


def _from_pattern(text):
    """Fall back to the first macro-master name anywhere in the RTL."""
    m = _MACRO_RE.search(text)
    return m.group(0) if m else None


def find_macro_name(filename):
    with open(filename, "r") as f:
        text = f.read()
    return _from_mem_stub_line(text) or _from_pattern(text)


if __name__ == "__main__":
    print(os.getcwd())

    macro = find_macro_name(DESIGN_V)
    assert macro, (
        f"No IN12LP SRAM macro found in {DESIGN_V}. If this build uses "
        f"behavioral SRAM (use_sim_sram), it must not run gen_sram_macro_spec."
    )

    os.environ["MACRO_NAME"] = macro
    print("Extracted SRAM macro:", macro)

    family = next((t for t in FAMILIES if t in macro), None)
    assert family, f"Could not determine SRAM family from macro name '{macro}'"

    subprocess.run(["bash", "gen_srams.sh", macro, family], check=True)

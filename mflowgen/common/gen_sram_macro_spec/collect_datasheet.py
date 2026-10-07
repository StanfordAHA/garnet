"""Collect the SRAM compiler's datasheet for the macro gen_srams.sh just built.

IN12LP_MEM_genviews writes every view of the macro under genviews-output/
(gen_srams.sh links the lib/lef/gds/verilog/cdl views from there). Its
datasheet (macro area, timing, power) feeds no downstream step, so this only
gathers it for the record: links in outputs/sram_datasheet/, which
sweep_specs.py copies into artifacts/ and the results zip.

The compiler writes one CSV per characterized corner,
genviews-output/doc/<macro>_<corner>.csv (the file check_sram_period.py reads
for the minimum cycle time); find_datasheets() takes everything under doc/
and, in case a compiler version puts it elsewhere, also matches more broadly
(see is_datasheet). Every run also writes genviews_manifest.txt, listing each
file genviews produced, so a miss can be fixed from the zip alone. When nothing
matches, the manifest also gets the compiler's -help text.

The datasheets are Synopsys-confidential: they only land in the workspace and
the sweep's results zip -- never commit them (garnet is public).

Fail-soft: a missing datasheet, or an error in this script, prints a WARNING
and exits 0. A datasheet must never fail a PnR build.

outputs/sram_datasheet is deliberately NOT a declared output in
configure.yml: mflowgen stamps each declared output, so adding one would make
every existing workspace re-run this step (and all of synth/PnR after it) on
its next make.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

GENVIEWS_DIR = Path("genviews-output")
OUT_DIR = Path("outputs/sram_datasheet")
MANIFEST = Path("genviews_manifest.txt")

DATASHEET_SUFFIXES = (".ds", ".pdf", ".htm", ".html")
DOC_DIRS = ("doc", "docs")


def is_datasheet(rel):
    """rel: a file's path relative to genviews-output/."""
    low = rel.as_posix().lower()
    return ("datasheet" in low or "data_sheet" in low
            or rel.suffix.lower() in DATASHEET_SUFFIXES
            or any(p.lower() in DOC_DIRS for p in rel.parts[:-1]))


def find_datasheets(genviews_dir):
    """Datasheet files under genviews_dir, sorted. Also used by
    sweep_specs.py to zip datasheets from workspaces built before this step
    collected them."""
    genviews_dir = Path(genviews_dir)
    if not genviews_dir.is_dir():
        return []
    return sorted(f for f in genviews_dir.rglob("*")
                  if f.is_file() and is_datasheet(f.relative_to(genviews_dir)))


def _genviews_help():
    """-help text of the compiler gen_srams.sh used (same family lookup)."""
    from get_macro_name import DESIGN_V, FAMILIES, find_macro_name
    macro = find_macro_name(DESIGN_V) or ""
    family = next((t for t in FAMILIES if t in macro), "S1DB")
    tool = (f"inputs/adk/mc/v-comp_in_gf12lp_{family.lower()}"
            f"/bin/IN12LP_MEM_genviews")
    try:
        r = subprocess.run([tool, "-help"], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=60,
                           universal_newlines=True)
        return f"$ {tool} -help\n{r.stdout}"
    except (OSError, subprocess.SubprocessError) as e:
        return f"$ {tool} -help\nfailed: {e}\n"


def main():
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    found = find_datasheets(GENVIEWS_DIR)
    for src in found:
        rel = src.relative_to(GENVIEWS_DIR)
        dst = OUT_DIR / rel.name
        if dst.exists() or dst.is_symlink():   # same basename in two dirs
            dst = OUT_DIR / "_".join(rel.parts)
        # Relative link, like gen_srams.sh's outputs/ links.
        dst.symlink_to(os.path.relpath(src, OUT_DIR))

    files = (sorted(f for f in GENVIEWS_DIR.rglob("*") if f.is_file())
             if GENVIEWS_DIR.is_dir() else [])
    lines = [f"# {len(files)} file(s) under {GENVIEWS_DIR}/",
             f"# datasheet: {', '.join(str(f.relative_to(GENVIEWS_DIR)) for f in found) or 'NONE FOUND'}"]
    lines += [f"{f.stat().st_size:>12}  {f.relative_to(GENVIEWS_DIR)}"
              for f in files]
    text = "\n".join(lines) + "\n"
    if not found:
        try:
            text += "\n" + _genviews_help()
        except Exception as e:
            text += f"\n-help not run: {e!r}\n"
    MANIFEST.write_text(text)

    if found:
        print(f"SRAM datasheet: {len(found)} file(s) -> {OUT_DIR}/")
        for f in sorted(OUT_DIR.iterdir()):
            print(f"  {f.name} -> {os.readlink(f)}")
    else:
        print(f"**WARNING: no SRAM datasheet found under {GENVIEWS_DIR}/; "
              f"see {MANIFEST} for what genviews produced.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # never fail the build over a datasheet
        print(f"**WARNING: collect_datasheet.py failed: {e!r}", file=sys.stderr)
        OUT_DIR.mkdir(parents=True, exist_ok=True)

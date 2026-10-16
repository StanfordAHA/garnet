"""The CGRA fabric is built at the lake spec's data_width.

A spec with data_width W gives tracks of W + 1 bits (data + ready-valid), the PE / IO /
pond / MEM ports at W + 1, a W-bit lassen PE (gen_PE_fc), and GLB words of W bits. 16
without a spec. See mflowgen/CLAUDE.md "Fabric data width follows the spec".
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

GARNET = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def _spec(path, width):
    fw = 2 if width == 64 else 4  # dw64 x fw4 has no SRAM macro
    path.write_text(json.dumps(dict(data_width=width, in_ports=2, out_ports=2, storage_capacity=8192,
                                    vec_width=fw)))
    return str(path)


def test_lake_spec_data_width(tmp_path, monkeypatch):
    from cgra.util_onyx import lake_spec_data_width
    monkeypatch.delenv("LAKE_SPEC_CONFIG", raising=False)
    assert lake_spec_data_width() == 16
    assert lake_spec_data_width(_spec(tmp_path / "s.json", 32)) == 32
    monkeypatch.setenv("LAKE_SPEC_CONFIG", _spec(tmp_path / "s64.json", 64))
    assert lake_spec_data_width() == 64


def _app(path, *port_widths):
    ports = [[f"p{i}", ["Array", w, "BitIn"]] for i, w in enumerate(port_widths)]
    path.write_text(json.dumps({"top": "global.app", "namespaces": {"global": {"modules": {
        "app": {"type": ["Record", ports + [["valid", "Bit"]]]}}}}}))
    return str(path)


def test_app_of_another_width_is_refused(tmp_path):
    from garnet import Garnet
    fabric32 = SimpleNamespace(data_width=32)
    Garnet.check_app_data_width(fabric32, _app(tmp_path / "a32.json", 32, 32))
    with pytest.raises(RuntimeError, match=r"\[16\] bits wide.*data width is 32"):
        Garnet.check_app_data_width(fabric32, _app(tmp_path / "a16.json", 16, 16))


# Hides metamapper.data_width from everything outside the metamapper package, as when
# garnet runs against a MetaMapper that predates it (MetaMapper's own modules then don't
# import it either).
_HIDE_MM_DATA_WIDTH = """
import builtins, sys
_real_import = builtins.__import__
def _import(name, globals=None, locals=None, fromlist=(), level=0):
    importer = (globals or {}).get('__name__', '') or ''
    hidden = name == 'metamapper.data_width' or (name == 'metamapper' and 'data_width' in (fromlist or ()))
    if hidden and level == 0 and not importer.startswith('metamapper'):
        raise ImportError('metamapper.data_width hidden for this test')
    return _real_import(name, globals, locals, fromlist, level)
builtins.__import__ = _import
"""


def _run_without_mm_data_width(code, **kw):
    return subprocess.run([sys.executable, "-c", _HIDE_MM_DATA_WIDTH + code], cwd=GARNET,
                          capture_output=True, text=True, **kw)


def test_mapper_without_metamapper_data_width_maps_16_bits():
    # The build machine's container (stanfordaha/garnet:latest) has a MetaMapper without
    # metamapper.data_width: mapping there works at 16 and refuses other widths clearly.
    out = _run_without_mm_data_width((
        "from mapper.netlist_util import data_width, set_data_width\n"
        "assert data_width() == 16\n"
        "set_data_width(16)\n"
        "try:\n"
        "    set_data_width(32)\n"
        "except ImportError as e:\n"
        "    print('REFUSED', e)\n"))
    assert out.returncode == 0, out.stderr[-3000:]
    assert "REFUSED mapping for a 32-bit CGRA needs MetaMapper with metamapper.data_width" in out.stdout


def test_container_steps_fetch_the_same_lassen_branch():
    # gen_rtl, memtile-power-test-gen and application each check out aha mek's lassen
    # branch in the stock container; keep the three in step.
    scripts = ["mflowgen/common/rtl/gen_rtl.sh", "mflowgen/common/memtile-power-test-gen/run.sh",
               "mflowgen/common/application/run.sh"]
    branches = set()
    for s in scripts:
        text = (GARNET / s).read_text()
        subprocess.run(["bash", "-n", str(GARNET / s)], check=True)
        m = re.findall(r"git --git-dir=/tmp/lassen_cdw\.git fetch -q https://github\.com/StanfordAHA/lassen\.git "
                       r"([\w./-]+):refs/heads/([\w./-]+)", text)
        assert len(m) == 1, s
        assert m[0][0] == m[0][1]
        assert f"git checkout -f -B {m[0][0]} FETCH_HEAD" in text, s
        branches.add(m[0][0])
    assert branches == {"thesis"}


# ---- Fabric RTL at each width (garnet.py runs in the repo root, like test_garnet) ----

def _ports(verilog, module):
    m = re.search(rf"^module {module} \((.*?)\);", verilog, re.S | re.M)
    assert m, f"module {module} not in garnet.v"
    out = {}
    for line in m.group(1).splitlines():
        mm = re.match(r"\s*(input|output)\s+(?:(?:wire|logic|reg)\s+)?(?:\[(\d+):0\]\s*)?(\w+)", line)
        if mm:
            out[mm.group(3)] = int(mm.group(2)) + 1 if mm.group(2) else 1
    return out


@pytest.fixture(scope="module", params=(8, 16, 32, 64), ids=lambda w: f"dw{w}")
def fabric(request, tmp_path_factory):
    """A 4x2 static fabric from a spec at this width. garnet.py runs with
    metamapper.data_width hidden: RTL generation must not need it (the container case)."""
    width = request.param
    tmp = tmp_path_factory.mktemp(f"dw{width}")
    spec = _spec(tmp / "spec.json", width)
    args = ["--width", "4", "--height", "2", "--verilog", "--use_sim_sram", "--glb_tile_mem_size", "128",
            "--lake-spec-config", spec, "--lake-spec-mode", "static", "--use-non-split-fifos"]
    # GARNET_HOME: garnet.py writes the GLB / GLC / MU headers there; never another checkout
    env = dict(os.environ, GARNET_HOME=str(GARNET), LAKE_SPEC_CONFIG=spec, LAKE_SPEC_MODE="static",
               USE_NON_SPLIT_FIFOS="1")
    # garnet.py writes into these; a fresh clone doesn't track the empty directories
    for d in ("matrix_unit/header", "global_buffer/header", "global_buffer/systemRDL/output",
              "global_controller/header", "global_controller/systemRDL/output"):
        (GARNET / d).mkdir(parents=True, exist_ok=True)
    code = f"import runpy; sys.argv = ['garnet.py'] + {args!r}; runpy.run_path('garnet.py', run_name='__main__')"
    for attempt in range(3):  # garnet.py has a flaky native crash (SIGSEGV / SIGABRT)
        (GARNET / "garnet.v").unlink(missing_ok=True)
        out = _run_without_mm_data_width(code, env=env)
        # A run that printed DONE and wrote garnet.v is done even if it then died at exit
        # (SIGABRT "double free or corruption"), as in mflowgen/common/rtl/garnet_build.sh
        done = (GARNET / "garnet.v").exists() and (out.returncode == 0 or "- garnet.py DONE" in out.stdout)
        if done:
            break
    assert done, out.stderr[-3000:]
    headers = tmp / "headers"
    for d in ("global_buffer/header", "global_controller/header", "matrix_unit/header"):
        shutil.copytree(GARNET / d, headers / d)
    return SimpleNamespace(width=width, track=width + 1, verilog=(GARNET / "garnet.v").read_text(),
                           headers=headers)


def test_fabric_ports_at_the_spec_width(fabric):
    t, v = fabric.track, fabric.verilog
    # data ports at the track width (plus 1-bit ones where the core has them), nothing else
    for module, prefix in (("MemCore", "MEM_"), ("PE", "PE_"), ("PondCore", "PondTop_")):
        ports = _ports(v, module)
        data = {w for n, w in ports.items() if re.fullmatch(rf"{prefix}(in|out)put_width_\d+_num_\d+", n)}
        assert t in data and data <= {1, t}, (module, data)
        assert not [n for n in ports if re.search(r"_b_\d+$", n)], f"{module}: bit-split ports"
    for tile in ("Tile_PE", "Tile_MemCore"):
        tracks = {n.rsplit("_B", 1)[1] for n in _ports(v, tile) if re.fullmatch(r"SB_T\d_\w+_SB_(IN|OUT)_B\d+", n)}
        assert tracks == {"1", str(t)}, (tile, tracks)
    # the PE core's instruction: 36 + 3 * width bits (gen_PE_fc(width))
    assert re.search(rf"input \[{36 + 3 * fabric.width - 1}:0\] inst,", v)
    io = _ports(v, "Tile_IOCoreReadyValid")
    assert any(re.fullmatch(rf"(f2io|io2f)_{t}(_\w+)?", n) for n in io), sorted(io)[:20]
    param = (fabric.headers / "global_buffer/header/global_buffer_param.h").read_text()
    assert re.search(rf"#define CGRA_DATA_WIDTH {fabric.width}\b", param)


@pytest.mark.parametrize("mode,ok", [("fit", True), ("overlap", False), ("past_end", False),
                                     ("bank_toggle", True)])
def test_testbench_refuses_io_data_past_its_glb_bank(fabric, tmp_path, mode, ok):
    if shutil.which("gcc") is None:
        pytest.skip("needs gcc")
    exe = tmp_path / "glb_ranges_test"
    lib = GARNET / "tests/test_app/lib"
    subprocess.run(["gcc", "-w", "-o", str(exe), str(HERE / "glb_ranges_test.c"),
                    str(lib / "gen.c"), str(lib / "parser.c"), str(lib / "tiny-json.c"), "-lm",
                    f"-I{fabric.headers}/global_buffer/header", f"-I{fabric.headers}/global_controller/header",
                    f"-I{fabric.headers}/matrix_unit/header"], check=True)
    out = subprocess.run([str(exe), mode], capture_output=True, text=True)
    if ok:
        assert out.returncode == 0 and "GLB_RANGES_OK" in out.stdout, out.stdout + out.stderr
    else:
        assert out.returncode == 1 and "ERROR: GLB:" in out.stdout, out.stdout + out.stderr

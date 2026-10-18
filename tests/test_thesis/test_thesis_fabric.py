"""garnet.py --thesis {static,rv}: the static-dense and ready-valid-dense thesis fabrics.

Both carry only what their execution model needs (cgra/util_thesis.py):
static: no FIFOs and no ready-valid in the tiles, no FIFO bypass config;
rv: ready-valid with every tile port's FIFO in the path, no bypass config;
both: no sparse cores, data tracks of data_width bits (no end-of-stream bit).
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

GARNET = Path(__file__).resolve().parents[2]

SPARSE_MODULES = ("intersect", "crddrop", "locator", "Repeat", "repeat_signal_generator",
                  "stream_arbiter", "pass_through", "reg_cr", "reduce_pe_cluster",
                  "fiber_access", "buffet", "scanner")


def _modules(verilog):
    """module name -> body"""
    return dict(re.findall(r"^module (\w+)\b(.*?)^endmodule", verilog, re.S | re.M))


def _ports(verilog, module):
    m = re.search(rf"^module {module} \((.*?)\);", verilog, re.S | re.M)
    assert m, f"module {module} not in garnet.v"
    out = {}
    for line in m.group(1).splitlines():
        mm = re.match(r"\s*(input|output)\s+(?:(?:wire|logic|reg)\s+)?(?:\[(\d+):0\]\s*)?(\w+)", line)
        if mm:
            out[mm.group(3)] = int(mm.group(2)) + 1 if mm.group(2) else 1
    return out


def _instantiators(modules, child):
    return {name for name, body in modules.items() if re.search(rf"^\s*{child}\b", body, re.M)}


@pytest.fixture(scope="module", params=("static", "rv"))
def fabric(request, tmp_path_factory):
    mode = request.param
    tmp = tmp_path_factory.mktemp(f"thesis_{mode}")
    spec = tmp / "spec.json"
    spec.write_text(json.dumps(dict(data_width=16, in_ports=2, out_ports=2, storage_capacity=8192,
                                    vec_width=4)))
    args = ["--thesis", mode, "--width", "4", "--height", "2", "--verilog", "--use_sim_sram",
            "--glb_tile_mem_size", "128", "--lake-spec-config", str(spec)]
    # GARNET_HOME: garnet.py writes the GLB / GLC / MU headers there; never another checkout
    env = dict(os.environ, GARNET_HOME=str(GARNET), PYTHONHASHSEED="0")
    for v in ("LAKE_SPEC_CONFIG", "LAKE_SPEC_MODE", "LAKE_POND_SPEC_CONFIG", "USE_NON_SPLIT_FIFOS",
              "DENSE_READY_VALID"):
        env.pop(v, None)
    # garnet.py writes into these; a fresh clone doesn't track the empty directories
    for d in ("matrix_unit/header", "global_buffer/header", "global_buffer/systemRDL/output",
              "global_controller/header", "global_controller/systemRDL/output"):
        (GARNET / d).mkdir(parents=True, exist_ok=True)
    for attempt in range(3):  # garnet.py has a flaky native crash (SIGSEGV / SIGABRT)
        (GARNET / "garnet.v").unlink(missing_ok=True)
        out = subprocess.run([sys.executable, "garnet.py"] + args, cwd=GARNET, env=env,
                             capture_output=True, text=True)
        # A run that printed DONE and wrote garnet.v is done even if it then died at exit
        done = (GARNET / "garnet.v").exists() and (out.returncode == 0 or "- garnet.py DONE" in out.stdout)
        if done:
            break
    assert done, out.stdout[-2000:] + out.stderr[-3000:]
    verilog = (GARNET / "garnet.v").read_text()
    return SimpleNamespace(mode=mode, verilog=verilog, modules=_modules(verilog))


def test_no_sparse_cores(fabric):
    sparse = [m for m in fabric.modules if any(s in m for s in SPARSE_MODULES)]
    assert not sparse, sparse


def test_no_fifo_bypass_config(fabric):
    for word in ("bypass_rv", "fine_grain_fifo_bypass"):
        assert word not in fabric.verilog, word


def test_tracks_are_data_width_bits(fabric):
    for tile in ("Tile_PE", "Tile_MemCore"):
        tracks = {n.rsplit("_B", 1)[1] for n in _ports(fabric.verilog, tile)
                  if re.fullmatch(r"SB_T\d_\w+_SB_(IN|OUT)_B\d+", n)}
        assert tracks == {"1", "16"}, (tile, tracks)
    for module, prefix in (("MemCore", "MEM_"), ("PE", "PE_"), ("PondCore", "PondTop_")):
        data = {w for n, w in _ports(fabric.verilog, module).items()
                if re.fullmatch(rf"{prefix}(in|out)put_width_\d+_num_\d+", n)}
        assert data <= {1, 16} and 16 in data, (module, data)


def test_static_fabric_has_no_fifos_or_ready_valid(fabric):
    if fabric.mode != "static":
        pytest.skip("static only")
    assert "Tile_io_core" in fabric.modules
    fifo_modules = [m for m in fabric.modules if re.search(r"fifo|FIFO|Fifo", m)]
    for f in fifo_modules:
        # The GLB's DMA FIFOs (outside the tiles, the same in both fabrics) are the only ones
        users = _instantiators(fabric.modules, f)
        assert users and all(u.startswith("glb_") for u in users), (f, users)
    for tile in ("Tile_PE", "Tile_MemCore"):
        rv = [n for n in _ports(fabric.verilog, tile) if n.endswith(("_ready", "_valid"))]
        assert not rv, (tile, rv[:10])


def test_rv_fabric_fifos_on_every_port(fabric):
    if fabric.mode != "rv":
        pytest.skip("rv only")
    assert "Tile_IOCoreReadyValid" in fabric.modules
    assert any(m.startswith("FifoRegWrapper") for m in fabric.modules)  # switch-box FIFOs
    pe = _ports(fabric.verilog, "PE")
    data_ports = [n for n in pe if re.fullmatch(r"PE_(in|out)put_width_\d+_num_\d+", n)]
    assert len(data_ports) == 8  # data0-2, bit0-2, res, res_p: no sparse-only ports
    # every port is ready-valid, with its tile FIFO (the pre-fill configurable one)
    fifos = set(re.findall(r"^\s*cfg_reg_fifo\w* (\w+)_(?:in|out)put_fifo\b", fabric.modules["PE_inner"], re.M))
    for p in data_ports:
        assert f"{p}_valid" in pe and f"{p}_ready" in pe, p
        assert p[len("PE_"):] in fifos, (p, fifos)

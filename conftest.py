import pytest
import magma
from gemstone.generator import clear_generator_cache
import tempfile
import shutil
import os
import glob
from lassen.sim import PE_fc
import magma as m
from peak import family

collect_ignore = [
    # TODO(rsetaluri): Remove this once it is moved to canal!
    "experimental",  # directory for experimental projects
    "src",  # pip folder that contains dependencies like magma
    "parsetab.py",
    "CoSA"
]


def cad_available():
    return os.path.isdir("/cad") and shutil.which("xrun") is not None


@pytest.fixture(autouse=True)
def magma_test():
    clear_generator_cache()
    magma.clear_cachedFunctions()
    magma.frontend.coreir_.ResetCoreIR()
    magma.generator.reset_generator_cache()


def pytest_addoption(parser):
    parser.addoption('--longrun', action='store_true', dest="longrun",
                     default=False, help="enable longrun decorated tests")


def pytest_configure(config):
    if not config.option.longrun:
        setattr(config.option, 'markexpr', 'not longrun')


def fp_files(use_dw=True):
    prefix = "DW" if use_dw else "CW"
    filenames = [f"{prefix}_fp_add.v", f"{prefix}_fp_mult.v"]
    if cad_available():
        if use_dw:
            dirname = "/cad/synopsys/dc_shell/J-2014.09-SP3/dw/sim_ver/"
        else:
            dirname = "/cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CW/"
    else:
        root_dir = os.path.dirname(__file__)
        dirname = os.path.join(root_dir, "peak_core")
    result_filenames = []
    for name in filenames:
        filename = os.path.join(dirname, name)
        assert os.path.isfile(filename)
        result_filenames.append(filename)
    return result_filenames


def get_mapping_fn(interconnect):

    mem_remap = None
    pe_remap = None

    for core_key, core_value in interconnect.tile_circuits.items():
        actual_core = core_value.core
        pnr_tag = actual_core.pnr_info()
        if isinstance(pnr_tag, list):
            continue
        pnr_tag = pnr_tag.tag_name
        print(pnr_tag)
        if pnr_tag == "m" and mem_remap is None:
            mem_remap = actual_core.get_port_remap()
        elif pnr_tag == "p" and pe_remap is None:
            pe_remap = actual_core.get_port_remap()
        elif mem_remap is not None and pe_remap is not None:
            break
    
    return pe_remap, mem_remap

@pytest.fixture
def get_mapping():
    return get_mapping_fn


def run_tb_fn(tester, cwd=None, trace=False, include_PE=False, **magma_args):
    use_verilator = False
    use_dw = False
    root_dir = os.path.dirname(__file__)
    with tempfile.TemporaryDirectory() as tempdir:
        if cwd is not None:
            tempdir = cwd
        print("cwd")
        print(cwd)
        print(tempdir)
        rtl_lib = []
        for genesis_verilog in glob.glob(os.path.join(root_dir, "genesis_verif/*.*")):
            shutil.copy(genesis_verilog, tempdir)
            rtl_lib.append(os.path.basename(genesis_verilog))
        for filename in fp_files(use_dw):
            shutil.copy(filename, tempdir)
            rtl_lib.append(os.path.basename(filename))
        for aoi_mux in glob.glob(os.path.join(root_dir, "tests/*.sv")):
            shutil.copy(aoi_mux, tempdir)
            rtl_lib.append(os.path.basename(aoi_mux))
        for glb_module in glob.glob(os.path.join(root_dir, "tests/test_memory_core/*.sv")):
            shutil.copy(glb_module, tempdir)
            rtl_lib.append(os.path.basename(glb_module))
        if include_PE:
            # rtl_lib.append(os.path.join(cwd,"PE.v"))
            pe_prefix = "PEGEN_"
            pe_child = PE_fc(family.MagmaFamily())
            m.compile(f"garnet_PE",
                      pe_child,
                      output="coreir-verilog",
                      coreir_libs={"float_CW"},
                      verilog_prefix=pe_prefix)
            m.clear_cachedFunctions()
            m.frontend.coreir_.ResetCoreIR()
            m.generator.reset_generator_cache()
            m.logging.flush_all()  # flush all staged logs

            rtl_lib.append("/aha/garnet/garnet_PE.v")

        if use_dw:
            coreir_lib_name = "float_DW"
        else:
            coreir_lib_name = "float_CW"

        runtime_kwargs = {"magma_output": "coreir-verilog",
                          "magma_opts": {"coreir_libs": {coreir_lib_name},
                                         "inline": False},
                          "include_verilog_libraries": rtl_lib,
                          "directory": tempdir,
                          "flags": ["-Wno-fatal"],
                          "disp_type": "realtime",
                          "num_cycles": 100000 * 10
        }
        if not use_verilator:
            target = "system-verilog"
            runtime_kwargs["simulator"] = "xcelium"
            runtime_kwargs["flags"] = ["-sv"]
            if trace:
                runtime_kwargs["dump_waveforms"] = True
        else:
            target = "verilator"
            if trace:
                runtime_kwargs["flags"].append("--trace")

        runtime_kwargs["magma_opts"].update(magma_args)

        tester.compile_and_run(target=target,
                               tmp_dir=False,
                               skip_compile=False,
                               **runtime_kwargs)



@pytest.fixture
def run_tb():
    return run_tb_fn

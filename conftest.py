import pytest
from magma import clear_cachedFunctions
import magma
from gemstone.generator import clear_generator_cache
from coreir.lib import libcoreir_c

collect_ignore = [
    # TODO(rsetaluri): Remove this once it is moved to canal!
    "experimental",  # directory for experimental projects
    "src",  # pip folder that contains dependencies like magma
    "parsetab.py",
    "CoSA"
]


@pytest.fixture(autouse=True)
def magma_test():
    clear_cachedFunctions()
    ctx = magma.backend.coreir_.CoreIRContextSingleton().get_instance()
    if ctx in magma.backend.coreir_._context_to_modules:
        del magma.backend.coreir_._context_to_modules[ctx]
    # Set flag so __del__ doesn't free twice
    ctx.external_ptr = True
    # Force memory free to avoid memory leak issue, see
    # https://github.com/rdaly525/coreir/issues/896
    # and https://github.com/StanfordAHA/garnet/pull/638
    # TODO: We should add a cleaner API for this to magma/pycoreir and update
    # this code accordingly
    libcoreir_c.COREDeleteContext(ctx.context)
    magma.frontend.coreir_.ResetCoreIR()
    clear_generator_cache()


def pytest_addoption(parser):
    parser.addoption('--longrun', action='store_true', dest="longrun",
                     default=False, help="enable longrun decorated tests")


def pytest_configure(config):
    if not config.option.longrun:
        setattr(config.option, 'markexpr', 'not longrun')

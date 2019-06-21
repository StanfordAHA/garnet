import pytest
from magma import clear_cachedFunctions
import magma.backend.coreir_ as coreir_
from gemstone.generator import clear_generator_cache

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
    coreir_.CoreIRContextSingleton().reset_instance()
    clear_generator_cache()


def pytest_addoption(parser):
    parser.addoption('--longrun', action='store_true', dest="longrun",
                     default=False, help="enable longrun decorated tests")
    parser.addoption('--width', type=int, default=4, dest="width", help="CGRA width")
    parser.addoption('--height', type=int, default=2, dest="height", help="CGRA height")


def pytest_generate_tests(metafunc):
    option_value = metafunc.config.option.name
    if "width" in metafunc.fixturenames and option_value is not None:
        metafunc.parametrize("width", [option_value], indirect=True)
    if "height" in metafunc.fixturenames and option_value is not None:
        metafunc.parametrize("height", [option_value], indirect=True)


def pytest_configure(config):
    if not config.option.longrun:
        setattr(config.option, 'markexpr', 'not longrun')

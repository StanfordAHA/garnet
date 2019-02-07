import pytest
from magma import clear_cachedFunctions
import magma.backend.coreir_ as coreir_

collect_ignore = [
    "experimental",  # directory for experimental projects
    "src",  # pip folder that contains dependencies like magma
    "parsetab.py",
    "CoSA"
]


@pytest.fixture(autouse=True)
def magma_test():
    clear_cachedFunctions()
    coreir_.__reset_context()


def pytest_addoption(parser):
    parser.addoption('--longrun', action='store_true', dest="longrun",
                     default=False, help="enable longrun decorated tests")


def pytest_configure(config):
    if not config.option.longrun:
        setattr(config.option, 'markexpr', 'not longrun')

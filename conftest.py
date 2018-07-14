import pytest
from magma.circuit import magma_clear_circuit_cache
from magma import clear_cachedFunctions

collect_ignore = ["src"]  # pip folder that contains dependencies like magma


@pytest.fixture(autouse=True)
def magma_test():
    import magma.config
#    magma.config.set_compile_dir('callee_file_dir')
    magma_clear_circuit_cache()
    clear_cachedFunctions()
    magma.backend.coreir_.__reset_context()

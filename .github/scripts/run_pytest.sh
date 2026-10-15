# Set up correct python environment maybe
source /aha/bin/activate

# pip install pytest-cov pytest-pycodestyle
# pycodestyle: tests/test_style checks every tracked .py file against setup.cfg
pip install pytest-cov pycodestyle

# NO COLOR!! Color is the worst.
# export PYTEST_ADDOPTS="--color=yes"
export PYTEST_ADDOPTS=

cd /aha/garnet

# -rfEs => show extra info on skipped tests, see `-r` in `pytest --help`
pytest -rfEs \
       --cov global_controller \
       --cov io_core           \
       --cov memory_core       \
       --ignore=filecmp.py     \
       --ignore=Genesis2/      \
       -v --cov-report term-missing tests

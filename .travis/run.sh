# add Genesis to the path
pip install genesis2

# force color
export PYTEST_ADDOPTS="--color=yes"

cd /garnet/

pytest --codestyle          \
    --cov global_controller \
    --cov io_core           \
    --cov memory_core       \
    --ignore=filecmp.py     \
    --ignore=Genesis2/      \
    -v --cov-report term-missing tests

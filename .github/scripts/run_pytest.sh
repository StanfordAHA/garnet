set +x

# Set up correct python environment maybe
# LAKE_DIR=$(dirname $(dirname `python -c "import lake; print(lake.__file__)"`))
# source ${LAKE_DIR}/scripts/setenv.sh
source /aha/bin/activate

# force color
export PYTEST_ADDOPTS="--color=yes"

cd /aha/garnet
pytest --pycodestyle           \
       --cov global_controller \
       --cov io_core           \
       --cov memory_core       \
       --ignore=filecmp.py     \
       --ignore=Genesis2/      \
       -v --cov-report term-missing tests

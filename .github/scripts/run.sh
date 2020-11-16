LAKE_DIR=$(dirname $(dirname `python -c "import lake; print(lake.__file__)"`))
source ${LAKE_DIR}/scripts/setenv.sh

# force color
export PYTEST_ADDOPTS="--color=yes"

# get the garnet root
# .github/scripts/run.sh
ROOT=$(dirname $(dirname $(dirname $BASH_SOURCE)))
cd ${ROOT}

pytest --pycodestyle           \
       --cov global_controller \
       --cov io_core           \
       --cov memory_core       \
       --ignore=filecmp.py     \
       --ignore=Genesis2/      \
       -v --cov-report term-missing tests

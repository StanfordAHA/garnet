cd / && git clone https://github.com/dillonhuff/clockwork && cd clockwork && git checkout lower_ubuffer
export LAKE_CONTROLLERS="/clockwork/lake_controllers/"
export LAKE_STREAM="/clockwork/lake_stream/"

# force color
export PYTEST_ADDOPTS="--color=yes"

cd /garnet/

pytest --pycodestyle           \
       --cov global_controller \
       --cov io_core           \
       --cov memory_core       \
       --ignore=filecmp.py     \
       --ignore=Genesis2/      \
       -v --cov-report term-missing tests

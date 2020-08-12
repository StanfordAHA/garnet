# add Genesis to the path
export GENESIS_HOME=/Genesis2/Genesis2Tools
export PATH=$GENESIS_HOME/bin:$GENESIS_HOME/gui/bin:$PATH
export PERL5LIB=$GENESIS_HOME/PerlLibs/ExtrasForOldPerlDistributions:$PERL5LIB

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

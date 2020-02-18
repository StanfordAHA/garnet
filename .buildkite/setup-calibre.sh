# Note loading calibre mucks up the path to the default python. This tries to fix that
# 1. Find *before* path to python3
echo "setup-calibre.sh: saving your path to python3"
p3path=`type -P python3`
p3path=`dirname ${p3path}`

source /cad/modules/tcl/init/sh
module load base
module load icadv/12.30.712
module load calibre/2019.1

# Part 2 of python3 fix: put original p3 path ahead of new calibre path
echo "setup-calibre.sh: restoring your path to python3"
[ "$p3path" ] && export PATH="$p3path:$PATH"

# N.B. the python3 that calibre wants to load is version 3.6.6 (as of
# 02/2020)! Presumably your python3 is that version or better!!
p3version=`python3 -c 'import sys; print(sys.version_info[0]*10000+sys.version_info[1]*100+sys.version_info[2])'`
echo "Found python version $p3version -- should be at least 30606 (3.6.6)"
if [ $p3version -lt 30606 ] ; then
  echo ""; echo "ERROR found python version $p3version -- should be >= 30606 (3.6.6) for Calibre"
  echo ""
fi




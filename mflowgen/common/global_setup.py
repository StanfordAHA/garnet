import os, sys

def patch(patchfile):
    '''
    Overwrite file in cloned repo with the local patchfile
    E.g. if patchfile="cadence-innovus-init/configure.yml"
    we copy local file patch/<patchfile> to MFLOWGEN_REO/nodes/<patchfile>
    BUT ONLY IF the two files are different
    '''
    import shutil
    from mflowgen.utils import get_top_dir

    # Where this script lives e.g.
    # /sim/buildkite-agent/builds/papers-2/tapeout-aha/mflowgen/common
    callee_dir = os.path.dirname(os.path.realpath(__file__))

    # mflowgen repo e.g. /sim/buildkite-agent/mflowgen.master
    mfrepo_dir = get_top_dir()

    # Copy callee_dir/init_scripts/pre-init.tcl => $REPO/nodes/cadence-innovus-init/scripts/
    # e.g. patchfile = 'cadence-innovus-init/scripts/pre-init.tcl'
    src = os.path.join(callee_dir, 'patch', patchfile)
    dst = os.path.join(mfrepo_dir, 'nodes', patchfile)

    # Copy if different
    info = f'...{patchfile}...'
    with open(src) as fsrc:
        with open(dst) as fdst:
            if fsrc.read() != fdst.read():
                shutil.copy(src, dst)
                info += 'PATCHED NOW'
            else:
                info += 'this was already done previously...'
    print(info)
                

def global_setup(caller=None):
    # E.g. caller_dir = /build/papers-4/tapeout-aha/mflowgen/mflowgen/Tile_PE
    caller_dir = os.path.dirname(os.path.realpath(caller))
    caller_name = os.path.basename(caller_dir)
    print(f"--- {caller_name} global_setup()")

    # Replace mflowgen default scripts withour own versions
    patch('cadence-innovus-init/scripts/pre-init.tcl')
    patch('cadence-innovus-cts/scripts/reporting.tcl')
    patch('mentor-calibre-lvs/lvs.runset.template')
    patch('mentor-calibre-lvs/configure.yml')


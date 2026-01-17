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
    patchfile = 'cadence-innovus-init/scripts/pre-init.tcl'
    src = os.path.join(callee_dir, 'patch', patchfile)
    dst = os.path.join(mfrepo_dir, 'nodes', patchfile)

    # Copy if different
    with open(src) as fsrc:
        with open(dst) as fdst:
            if fsrc.read() != fdst.read():
                print(f"...copying {src} to {dst}...")
                shutil.copy(src, dst)
            else:
                print(f"...no copy b/c {src} == {dst}...")
                

def global_setup(caller=None):
    # E.g. caller_dir = /build/papers-4/tapeout-aha/mflowgen/mflowgen/Tile_PE
    caller_dir = os.path.dirname(os.path.realpath(caller))
    caller_name = os.path.basename(caller_dir)
    print(f"+++ global_setup() called from {caller_name}/construct.py")

    # Replace mflowgen default scripts withour own versions
    patch('cadence-innovus-init/scripts/pre-init.tcl')
    patch('cadence-innovus-cts/scripts/reporting.tcl')



# now copy patch/cadence-innovus-cts/scripts/reporting.tcl

##############################################################################
# TRASH

# def trash():
#     # E.g. /sim/buildkite-agent/builds/papers-2/tapeout-aha/mflowgen/common
#     print("Hey I wonder where does this script live?")
#     print("I think it is here maybe:")
#     print(os.path.dirname(os.path.realpath(__file__)))
# 
#     # E.g. /sim/buildkite-agent/builds/papers-2/tapeout-aha/mflowgen/common
#     print("Okay okay but where is mflowgen repo tho")
#     print("Is it here:")
#     print(os.getcwd())
# 
#     # Time to get fancy
#     # Replace mflowgen pre-init with fixed version
#     # repo_dir = os.getcwd()
# 
# 
#     # caller_dir = os.path.dirname(os.path.realpath(caller__file__))
#     # caller_dir = sys.modules["__main__"].__file__
#     # dst = os.path.join(caller_dir, '../nodes/cadence-innovus-init/scripts/')
# 
#     caller_dir = get_top_dir()

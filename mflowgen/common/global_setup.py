import os, sys

from mflowgen.utils import get_top_dir

def global_setup(caller=None):
    print("+++ Hello woild I am global setup howdja do")
    print("I was called by", os.path.realpath(caller))
    print("I was called from dir", os.path.dirname(os.path.realpath(caller))

    # E.g. /sim/buildkite-agent/builds/papers-2/tapeout-aha/mflowgen/common
    print("Hey I wonder where does this script live?")
    print("I think it is here maybe:")
    print(os.path.dirname(os.path.realpath(__file__)))

    # E.g. /sim/buildkite-agent/builds/papers-2/tapeout-aha/mflowgen/common
    print("Okay okay but where is mflowgen repo tho")
    print("Is it here:")
    print(os.getcwd())

    # Time to get fancy
    # Replace mflowgen pre-init with fixed version
    # Copy callee_dir/init_scripts/pre-init.tcl => repo_dir/nodes/cadence-innovus-init/scripts/
    callee_dir = os.path.dirname(os.path.realpath(__file__))
    # repo_dir = os.getcwd()

    # caller_dir = os.path.dirname(os.path.realpath(caller__file__))
    # caller_dir = sys.modules["__main__"].__file__
    # dst = os.path.join(caller_dir, '../nodes/cadence-innovus-init/scripts/')

    caller_dir = get_top_dir()
    dst = os.path.join(caller_dir, 'nodes/cadence-innovus-init/scripts/')


    import shutil
    src = os.path.join(callee_dir, 'init-scripts/pre-init.tcl')
    print(f"--- OMG gonna try and copy {src} to {dst}")
    shutil.copy(src, dst)


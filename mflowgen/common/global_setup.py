import os

def global_setup(caller__file__):
    print("--- Hello woild I am global setup howdja do")

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
    repo_dir = os.getcwd()
    import shutil
    src = os.path.join(callee_dir, 'init_scripts/pre-init.tcl')
    print(f"--- OMG gonna try and copy {src} to {repo_dir}")
    shutil.copy(src, repo_dir)


from pathlib import Path
import os
import subprocess
import sys
import copy
import json

def add_subparser(subparser):
    parser = subparser.add_parser(Path(__file__).stem, aliases=['pipeline'], description='AHA flow command for pipelining a mapped halide application, doing place and route, and generating a bitstream to configure the CGRA')
    parser.add_argument("app", help="Required parameter specifying which halide application to compile")
    parser.add_argument("--base", default=None, type=str, help="Optional parameter for specifying a base directory of an app")
    parser.add_argument("--no-parse", action="store_true", help="Skips the parse_design_meta.py script")
    parser.add_argument("--log", action="store_true", help="Creates a log for command output")
    parser.add_argument("--layer", type=str, help="Specifies layer parameters if running 'aha pipeline apps/resnet_output_stationary', options for LAYER are in application_parameters.json")
    parser.add_argument("--env-parameters", default="", type=str, help="Specifies which environmental parameters to use from application_parameters.json, options for ENV_PARAMETERS are in application_parameters.json")
    parser.set_defaults(dispatch=dispatch)


def subprocess_call_log(cmd, cwd, env=None, log=False, log_file_path="log.log",
                        do_cmd=subprocess.check_call):
    '''Can set e.g. do_cmd=Popen to run job in background'''
    # if do_cmd == subprocess.check_call: print('--- PNR/scl: check_call (run) garnet.py')
    # elif do_cmd == subprocess.Popen:    print('--- PNR/scl: Popen (background) garnet.py')
    if log:
        print("[log] Command  : {}".format(" ".join(cmd)))
        print("[log] Log Path : {}".format(log_file_path), end="  ...", flush=True)
        with open(log_file_path, "a") as flog:
            do_cmd(
                cmd,
                cwd=cwd,
                env=env,
                stdout=flog,
                stderr=flog
            )
        print("done")
    else:
        do_cmd(
            cmd,
            env=env,
            cwd=cwd
        )


def load_environmental_vars(env, app, layer=None, env_parameters=None):
    filename = os.path.realpath(os.path.dirname(__file__)) + "/application_parameters.json"
    new_env_vars = {}
    app_name = str(app) if layer is None else str(layer)

    if not os.path.exists(filename):
        print(f"{filename} not found, not setting environmental variables")
    else:
        fin = open(filename, 'r')
        env_vars_fin = json.load(fin)
        if "global_parameters" in env_vars_fin:
            if env_parameters is None or str(env_parameters) not in env_vars_fin["global_parameters"]:
                new_env_vars.update(env_vars_fin["global_parameters"]["default"])
            else:
                new_env_vars.update(env_vars_fin["global_parameters"][str(env_parameters)])

        if app_name in env_vars_fin:
            if env_parameters is None or str(env_parameters) not in env_vars_fin[app_name]:
                new_env_vars.update(env_vars_fin[app_name]["default"])
            else:
                new_env_vars.update(env_vars_fin[app_name][str(env_parameters)])

    for n, v in new_env_vars.items():
        env[n] = v



def dispatch(args, extra_args=None):
    args.app = Path(args.app)
    env = copy.deepcopy(os.environ)
    env["COREIR_DIR"] = str(args.aha_dir / "coreir")
    env["COREIR_PATH"] = str(args.aha_dir / "coreir")
    env["LAKE_PATH"] = str(args.aha_dir / "lake")
    env["CLOCKWORK_PATH"] = str(args.aha_dir / "clockwork")

    load_environmental_vars(env, args.app, layer=args.layer, env_parameters=args.env_parameters)

    if args.base is None:
        app_dir = Path(
            f"{args.aha_dir}/Halide-to-Hardware/apps/hardware_benchmarks/{args.app}"
        )
    else:
        app_dir = (Path(args.base) / args.app).resolve()
    
    if os.path.exists(str(app_dir / "bin/input.raw")):
        ext = ".raw"
    else:
        ext = ".pgm"

    log_path = app_dir / Path("log")
    log_file_path = log_path / Path("aha_pnr.log")

    if args.log:
        subprocess.check_call(["mkdir", "-p", log_path])
        subprocess.check_call(["rm", "-f", log_file_path])

    print (f"Using testbench file extension: {ext}.")

    map_args = [
        "--no-pd",
        "--interconnect-only",
        "--input-app",
        str(app_dir / "bin/design_top.json"),
        "--input-file",
        str(app_dir / f"bin/input{ext}"),
        "--output-file",
        str(app_dir / f"bin/{args.app.name}.bs"),
        "--gold-file",
        str(app_dir / f"bin/gold{ext}"),
        "--input-broadcast-branch-factor", "2",
        "--input-broadcast-max-leaves", "4",
        "--rv",
        "--sparse-cgra",
        "--sparse-cgra-combined",
        "--pipeline-pnr"
    ]

    need_daemon = False
    do_cmd = subprocess.check_call
    if '--daemon' in extra_args:

        # Do a '--daemon status' to see if daemon exists yet
        cmd = [sys.executable, "garnet.py", "--daemon", "status"]
        p = subprocess.run(cmd, text=True, cwd=args.aha_dir / "garnet",
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # When running as daemon, must use non-blocking "Popen" and not "check_call"
        need_daemon = 'no daemon found' in p.stdout
        if need_daemon:
            print(f"--- found no daemon, setting do_cmd to Popen", flush=True)
            do_cmd = subprocess.Popen
        else:
            print(f"--- found the daemon, leaving do_cmd alone", flush=True)

    subprocess_call_log (
        cmd=[sys.executable, "garnet.py"] + map_args + extra_args,
        cwd=args.aha_dir / "garnet",
        log=args.log,
        log_file_path=log_file_path,
        env=env,
        do_cmd=do_cmd,
    )

    # Daemon runs in the background; need this to tell us when the PNR is done
    if need_daemon:
        print(f'--- BEGIN LAUNCHED NEW DAEMON in pnr; waiting now...')
        subprocess.run([sys.executable, 'garnet.py', '--daemon', 'wait'], cwd='/aha/garnet')

    # generate meta_data.json file
    if not args.no_parse:
        if not str(args.app).startswith("handcrafted"):
            # get the full path of the app
            arg_path = f"{args.aha_dir}/Halide-to-Hardware/apps/hardware_benchmarks/{args.app}"
            subprocess_call_log (
                cmd=[sys.executable,
                 f"{args.aha_dir}/Halide-to-Hardware/apps/hardware_benchmarks/hw_support/parse_design_meta.py",
                 "bin/design_meta_halide.json",
                 "--top", "bin/design_top.json",
                 "--place", "bin/design.place"],
                cwd=arg_path,
                log=args.log,
                log_file_path=log_file_path,
                env=env
            )

    print('--- DONE PNR'); sys.stdout.flush(); sys.stderr.flush(); sys.stdin.flush()

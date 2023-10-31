import os
import sys
import json
import subprocess
from argparse import Namespace

GarnetDaemon_HELP = '''
DESCRIPTION:
    garnet.py can run as a daemon to save you time when generating bitstreams
    for multiple apps using the same garnet circuit. Use the "launch" command
    to build a circuit and keep state in the background. The "use-daemon" command
    reuses the background state to more quickly do pnr and bitstream generation.

      --daemon launch     -> process args and launch a daemon
      --daemon use-daemon -> use existing daemon to process 
      --daemon kill       -> kill the daemon

EXAMPLE:
    garnet.py --width 4 --height 2 --daemon launch
    garnet.py <app1-args> --daemon use-daemon
    garnet.py <app2-args> --daemon use-daemon
    garnet.py --daemon kill

NOTE! 'use-daemon' width and height must match 'launch-daemon'!!!
'''

class GarnetDaemon:
    pid = 0
    choices = ['help','launch', 'use-daemon', 'kill']
    filenames = {
        "pid"    : "/tmp/garnet-daemon-pid",    # Process ID of daemon
        "state0" : "/tmp/garnet-daemon-state0", # Original state (args) of daemon
        "reload" : "/tmp/garnet-daemon-reload", # Desired new state (args)
        "tty"    : "/tmp/garnet-daemon-tty",    # Desired new tty
    }

    def do_cmd(cmd):
        'Executes <cmd>, returns True or False according to whether command succeeded'
        return subprocess.run(cmd.split()).returncode == 0

    def status(dbg=1):
        g = GarnetDaemon
        pid = g.pid
        if dbg: print(f'Checking status of process {pid}')
        cmd = f'test -d /proc/{pid}'
        pid_exists = g.do_cmd( f'test -d /proc/{pid}' )
        if pid_exists:
            print(f'- found running daemon {pid}')

            f = g.filenames["state0"]
            state0_exists = g.do_cmd( f'test -f {f}' )
            if not state0_exists:
                print(f'- WARNING: daemon state corrupted: suggest you do "kill {pid}"')
                return
            args0 = g.load_args(g.filenames['state0'])
            print(f'- found daemon {pid} original state args =\n  {args0}')
        else:
            print("- no daemon found")



    # TODO
    def save_my_pid(filename, dbg=1):
        'Save pid to indicated filename'
        g = GarnetDaemon
        g.pid = os.getpid()
        if dbg: print(f'found pid={g.pid}; saving to {filename}')
        with open(filename, 'w') as f:
            f.write(f'{g.pid}\n')
        f.close()
        if dbg: print(f'I am Damon the daemon, my pid is {g.pid}')

    def save_my_args(args, filename, dbg=1):
        'Save current state (args) to indicated filename'
        argdic = vars(args)
        sorted_argdic=dict(sorted(argdic.items()))
        f = open(filename, 'w')
        json.dump(sorted_argdic, f)
        f.close()
        if dbg: print(f'- Saved args to {filename}')
        
    def load_args(filename, dbg=1):
        'Load state (args) from indicated filename'
        f = open(filename, 'r')
        args_dict = json.load(f)
        f.close()
        if dbg: print(f'- Restored args from {filename}')
        return Namespace(**args_dict)

    def save_my_tty(filename, dbg=1):
        'Save tty path to <filename> arg'
        rval = subprocess.run(['tty'], capture_output=True)
        tty = rval.stdout.decode()
        with open(filename, 'w') as f: f.write(tty)
        f.close()

    def load_tty(filename, dbg=1):
        'Redirect stdout/err to tty indicated in <filename> arg'
        f = open(filename, 'r'); tty = f.read().strip(); f.close()
        term = open(tty, 'w')  # E.g. tty = '/dev/pts/8'
        sys.stdout = term; sys.stderr = term

    def sigstop(dbg=1):
        'Stop and wait'
        g = GarnetDaemon
        assert g.pid == os.getpid()
        if dbg: print(f'Stop and wait: kill -STOP {str(g.pid)}')

    def restart(dbg=1):
        
#         rval = subprocess.run(["kill", "-STOP", str(g.pid)])
#         ttypath="/dev/pts/75"
#         term = open(ttypath, 'w')
#         sys.stdout = term
#         sys.stderr = term

        print("i was gone but now am back")

    def launch_daemon(args, dbg=1):
        g = GarnetDaemon
        g.save_my_pid(g.filenames["pid"])
        g.save_my_args(args, g.filenames["state0"])

    def stop_and_wait_for_cont(): pass
    def read_new_args(): pass
    def kill_daemon():
        # TODO delete filename['pid']
        exit()

    def check_for_daemon(args):
        g = GarnetDaemon

        if args.daemon == "help":
            print(GarnetDaemon_HELP)
            exit()

        elif args.daemon == "launch":
            # Save pid and initial state (args)
            is_daemon = True
            launch_daemon(args)
            return is_daemon

        elif args.daemon == "use-daemon":
            # TODO verify that width and height match---or maybe do thatin the daemon---or BOTH
            save_my_args(args, filenames["reload"])
            send_cont_signal_to_daemon()
            exit()             

    def read_state_and_continue(arg_filename, tty_filename, dbg=1):
        # TODO error/warning if file no exist
        args = load_args(arg_filename)
        load_tty(tty_filename)


    def wait(dbg=1):
        g = GarnetDaemon
        if dbg: print("Stop and wait for someone to send a SIGCONT signal")
        g.sigstop()

        
#         # Continue on receipt of SIGCONT
#         args = g.read_state_and_continue()
#         return args


#         args = read_new_args
#         if args.daemon == "kill":
#             kill_daemon()
#             exit()
#         else:
#             return args

import os, sys, signal, subprocess
import json
from argparse import Namespace

# FIXME/TODO CONSIDER:
# when you use 'self', and you change the class name, all is copacetic
# when you use 'g=GarnetDaemon'...whuh oh!  oh boy! nooooo

# FIXME/TODO double-check README etc.
# FIXME/TODO should probably have a cleanup() method that deletes tmp files etc.
# called from kill() maybe

GarnetDaemon_HELP = '''
DESCRIPTION:
  garnet.py can run as a daemon to save you time when generating bitstreams
  for multiple apps using the same garnet circuit. Use the "launch" command
  to build a circuit and keep state in the background. The "use-daemon" command
  reuses the background state to more quickly do pnr and bitstream generation.

      --daemon launch -> process args and launch a daemon
      --daemon use    -> use existing daemon to process 
      --daemon kill   -> kill the daemon

EXAMPLE:
    garnet.py --width 4 --height 2 --daemon launch
    garnet.py <app1-args> --daemon use
    garnet.py <app2-args> --daemon use
    garnet.py --daemon kill

NOTE! 'daemon.use' width and height must match 'daemon.launch'!!!
'''

# See README.txt for more info

class GarnetDaemon:

    # Permissible daemon commands
    choices = [ 'help','launch', 'use', 'kill', 'status', 'force', 'force-launch' ]

    # Disk storage for persistent daemon state
    fn_pid    = "/tmp/garnet-daemon-pid"    # Process ID of daemon
    fn_state0 = "/tmp/garnet-daemon-state0" # Original state (args) of daemon
    fn_reload = "/tmp/garnet-daemon-reload" # Desired new state (args)

    # "PUBLIC" methods: initial_check(), loop()

    def initial_check(args):
        '''Process command found in <args>.daemon'''
        if args.daemon == None: return

        elif args.daemon == "help":
            GarnetDaemon.help(args); exit()

        elif args.daemon == "use":
            print("hello here i am doing a 'daemon use'", flush=True)
            GarnetDaemon.use(args); exit()

        elif args.daemon == "kill":
            GarnetDaemon.kill(dbg=1); exit()

        elif args.daemon == "status":
            GarnetDaemon.status(args); exit()

        elif args.daemon == "launch":
            GarnetDaemon.die_if_daemon_exists()

        elif args.daemon == "force-launch" or args.daemon == "force":
            print(f'- hello here i am forcing a launch')
            GarnetDaemon.kill(dbg=1)
            args.daemon = "launch"   # is this bad?



    def loop(args, dbg=1):
        '''Launch daemon and/or watch for updates'''
        gd = GarnetDaemon; command = args.daemon
        print(f'- daemon.py/loop(): in the loop. command={command}')
        assert command == "launch" or command == "use", \
            f'Found command "{command}", should have been "launch" or "use"'

        # On launch, save pid and initial state in "state0" file
        if command == "launch":
            pid = os.getpid()
            gs = gd.grid_size(args)    # E.g. "4x2"
            print(f'\n--- LAUNCHING {gs} DAEMON {pid}')
            gd.save_state0(args)
            print(f'- DAEMON STOPS and waits...\n')
            sys.stdout.flush()

        # Stop and wait for CONT signal from client
        gd.sigstop()

        # On CONT, load new args from 'reload' file
        print(f'\n\n--- DAEMON RESUMES')
        return gd.load_args()

    # ------------------------------------------------------------------------
    # "Private" methods for processing individual daemon commands:
    #   def help()
    #   def use(args)
    #   def kill(dbg=1)
    #   def status(args)

    def help():
        print(GarnetDaemon_HELP)
        return GarnetDaemon_HELP

    def use(args):
        print("hello here i am using", flush=True)
        GarnetDaemon.daemon_wait(args) # Wait for daemon to exist
        GarnetDaemon.save_args(args)   # Save args where the daemon will find them
        GarnetDaemon.sigcont()         # Tell daemon to CONTinue
        exit()                         # Kill yourself, daemon will take it from here...

    def kill(dbg=1):
        if GarnetDaemon.daemon_exists():
            pid = GarnetDaemon.retrieve_pid()  # FIXME there are way too many retrive_pid calls!!!
            if dbg: print(f'- found daemon pid {pid}, killing it now')
            GarnetDaemon.sigkill()
        else:
            print(f'- daemon is already dead')

    def daemon_exists(pid=None):
        import psutil
        if not pid: pid = GarnetDaemon.retrieve_pid()
        process_exists = f'test -d /proc/{pid}'
        if not GarnetDaemon.do_cmd(process_exists): return False
        process_status = psutil.Process(int(pid)).status()
        if process_status == 'zombie': return False
        return True

    def status(args, dbg=0):
        gd = GarnetDaemon;
        if dbg: print(f'\n--- STATUS: daemon status requested')

        if dbg: print(f'- checking for orphans')
        GarnetDaemon.check_for_orphans()

        pid = GarnetDaemon.retrieve_pid()
        if dbg: print(f'- checking status of process {pid}')

        state0_file = gd.fn_state0
        cmd = f'test -d /proc/{pid}'

#         see_if_daemon_exists = f'test -d /proc/{pid}'
#         if not gd.do_cmd(see_if_daemon_exists):
        if not GarnetDaemon.daemon_exists():
            print("- no daemon found")
            return False
        else:
            print(f'- found running daemon {pid}')

            see_if_state0_exists = f'test -f {state0_file}'
            if not gd.do_cmd(see_if_state0_exists):
                print(f'- WARNING: cannot find daemon state file "{state0_file}"')
                print(f'- WARNING: daemon state corrupted: suggest you do "kill {pid}"')
                return

            # Make sure grid sizes match, at least!
            state0_args = gd.load_args(state0_file)
            grid_size = gd.grid_size(state0_args)
            print(f'- found {grid_size} daemon {pid} w launch-state args = {state0_args.__dict__}')
            gd.args_match_or_die(state0_args, args)
            return True

    # ------------------------------------------------------------------------
    # "Private" methods for saving and restoring daemon state
    #     def save_state0(args)
    #     def save_args(args, fname)
    #     def load_args()

    def save_state0(args, dbg=0):
        GarnetDaemon.register_pid()
        GarnetDaemon.save_args(args, fname=GarnetDaemon.fn_state0)

    def save_args(args, fname=None, dbg=0):
        'Save current state (args) to arg-save (reload) file'

        # Save args as a sorted dict
        argdic = vars(args)
        sorted_argdic=dict(sorted(argdic.items()))

        if not fname: fname = GarnetDaemon.fn_reload
        with open(fname, 'w') as f: json.dump(sorted_argdic, f)
        if dbg: print(f'- saved args {args} to {fname}')
        
    def load_args(fname=None, dbg=0):
        'Load state (args) from save-args (reload) file'
        if not fname: fname = GarnetDaemon.fn_reload
        with open(fname, 'r') as f: args_dict = json.load(f)
        new_args = Namespace(**args_dict)
        if dbg: print(f'- restored args {new_args} from {fname}')
        return new_args

    # ------------------------------------------------------------------------
    # "Private" methods for interfacing with the daemon
    #     def daemon_wait(args):
    #     def die_if_daemon_exists():
    #     def check_for_orphans():
    #     def all_daemon_processes_except(*args):
    #     def args_match_or_die(daemon_args, client_args):

    def daemon_wait(args, dbg=1):
        '''Check daemon status, do not continue until/unless daemon exists'''
        import time
        wait = 2; max = 5 * 60;   # Give up after five minutes
        while not GarnetDaemon.status(args):
            print(f'WARNING Cannot find daemon (yet); will wait {wait} seconds and retry')
            time.sleep(wait); wait = wait + wait
            if wait > max:
                sys.stderr.write('ERROR Timeout waiting for daemon. Did you gorget to launch it?\n')
                exit(13)
                break
        if dbg: print(f'daemon_wait(): found the daemon')

    def die_if_daemon_exists():
        '''If existing daemon is found, issue an error message and die'''
        if GarnetDaemon.daemon_exists():
            g = GarnetDaemon
            # g.status(None, match_or_die=False)
            state0_args = g.load_args(g.fn_state0)
            gs = g.grid_size(state0_args)
            pid = g.retrieve_pid()
            errmsg  = f'**********************************************************************\n'
            errmsg += f'ERROR found existing ({gs}) daemon, pid={pid}\nTo fix:\n'
            errmsg += f'- kill existing daemon and retry: kill -9 {pid}\n'
            errmsg += f'- use existing daemon i.e. "--daemon use" instead of "--daemon launch"\n'
            errmsg += f'- try again but this time use "--daemon force-launch"\n'
            errmsg += f'**********************************************************************'
            assert False, '\n' + errmsg

    def check_for_orphans():
        '''Looks for orphan daemon processes, issues warnings recommending kill'''

        # Get all daemon processes EXCEPT:
        # - exclude "official" daemon
        # - exclude self because we might be in the process of launching
        pdaemon = int(GarnetDaemon.retrieve_pid()); pself = os.getpid()
        orphan_pids = GarnetDaemon.all_daemon_processes_except(pdaemon,pself)
        if orphan_pids == []:
            return False  # No orphans found
        else:
            print(f'********************************************************')
            for p in orphan_pids:
                print(f'WARNING found orphan daemon {p}, you should kill it!')

            # print(f'--------------------------------------------------------')
            pidsstring_list = list(map(str, orphan_pids))
            pidstring = " ".join(pidstring_list)
            print(f'ps      {pidstring}')
            print(f'kill -9 {pidstring}')
            print(f'********************************************************')
            return True  # Found orphans

    def all_daemon_processes_except(*args):
        '''Return a list of all daemon processes except those listed in args'''
        import psutil
        # Find all processes with args "--daemon" and "launch"
        def match(pid):
            try:    cmdline = psutil.Process(pid).cmdline()
            except: return False
            return  ("--daemon" in cmdline) and ("launch" in cmdline)
        daemon_pids = list(filter( lambda pid: match(pid), psutil.pids() ))
        for pid in args:
            if pid in daemon_pids: daemon_pids.remove(pid)
        return daemon_pids
        

    def args_match_or_die(daemon_args, client_args):
        '''Daemon and client args must match exactly, else ERR and DIE'''
        gd = GarnetDaemon
        dgrid = gd.grid_size(daemon_args, 'daemon')
        cgrid = gd.grid_size(client_args, 'client')
        if dgrid != cgrid:
            errmsg = f'\n\nERROR: Daemon uses {dgrid} grid; '\
                + f'must kill and restart daemon if you want {cgrid}\n'
            sys.stderr.write(errmsg); exit(13)

    # ------------------------------------------------------------------------
    # Misc utilites: wrappers for shell commands
    #     def do_cmd(cmd):
    #     def sigstop(pid=None, dbg=1):
    #     def sigcont(pid=None, dbg=1):
    #     def sigkill(pid): os.kill(pid, signal.SIGKILL)

    def do_cmd(cmd):
        'Executes <cmd>, returns True or False according to whether command succeeded'
        p = subprocess.run(cmd, shell=True)
        return p.returncode == 0

    # Stop, but do not kill, pid. Can continue again w "sigcont"
    def sigstop(pid=None, dbg=1):


#         import getpipes    # FIXME need a better name than "getpipes" :(
#         procs = getpipes.find_proc_stop_order()
#         if dbg:
#             print(f'\nI think I found the procs to STOP, in this order:')
#             print(f'  {procs}')
#             sys.stdout.flush()
#         
# # Oops one of theseis the pytest program maybe?
# #      [2530480, 2530481, 2530484]
# # 
# #  % ps
# #     PID TTY          TIME CMD
# #   25833 pts/2    00:00:03 bash
# # 2530481 pts/2    00:00:00 tee
# # 2530484 pts/2    00:00:00 python3
# # 2530733 pts/2    00:00:00 ps
# 
#         procs.remove(min(procs))
#         print(f'\nOops no, take out pytest, new order is maybe:\n')
#         print(f'  {procs}')
#         sys.stdout.flush()
#         
#         subprocess.run('ps -o pid,stat,tty,comm'.split()); sys.stdout.flush()
# 
# #         for p in procs:
# #             print(f'Want to stop: {p}\n\n', flush=True)
# # 
# #             print(f'\nstopping {p}\n\n', flush=True)
# #             os.kill(p, signal.SIGSTOP)
# #         return

        if not pid: pid = GarnetDaemon.retrieve_pid()
        
        # print(f'\nstopping final {pid}\n\n', flush=True)
        # VERY IMPORTANT: job can hang forever is do not do this final flush!!!
        sys.stdout.flush(); sys.stderr.flush()
        os.kill(int(pid), signal.SIGSTOP)

    # Send a "CONTinue" signal to a process
    def sigcont(pid=None, dbg=1):
        if not pid: pid = GarnetDaemon.retrieve_pid()
        print(f'sending CONT to {pid}')
        os.kill(int(pid), signal.SIGCONT)

    # TERM did not work, using KILL instead.
    def sigkill(pid=None):
        if not pid: pid = GarnetDaemon.retrieve_pid()
        os.kill(int(pid), signal.SIGKILL)

    # ------------------------------------------------------------------------
    # Misc utilites: retrieve daemon info
    #   def grid_size(args, who='daemon'):
    #   def retrieve_pid(fname=None, dbg=1):

    # Returns e.g. "4x2" if args request 4x2 grid
    def grid_size(args, who='daemon'):
        assert 'width'  in args, f"No width specified for {who}"
        assert 'height' in args, f"No height specified for {who}"
        return f'{args.width}x{args.height}'

    def register_pid(fname=None, dbg=0):
        'Write pid to pid-save file'
        pid = os.getpid()
        if not fname: fname = GarnetDaemon.fn_pid
        with open(fname, 'w') as f: f.write(str(pid) + '\n')
        if dbg: print(f'- wrote pid {pid} to file {fname}')

    def retrieve_pid(fname=None, dbg=0):
        'Get pid from pid-save file'
        if not fname: fname = GarnetDaemon.fn_pid
        try:
            with open(fname, 'r') as f: pid = f.read().strip()
            if dbg: print(f'- got pid {pid} from file {fname}')
            return pid
        except:
            print(f'WARNING could not read from daemon pid file {fname}')
            return None

##############################################################################
# TESTING, see test_daemon.py
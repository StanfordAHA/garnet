import os, sys, signal, subprocess
import time

try:
    import psutil
except:
    subprocess.run('pip install psutil'.split())
    import psutil

import json
from argparse import Namespace

# TODO still not cleaning up after daemons: see ls /tmp/garnet-daemon-* {pid,state0,reload}
# - 'daemon kill' should delete these, yes? and
# - and 'daemon status' should issue warnings?

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
      --daemon status -> print daemon status and exit
      --daemon force  -> same as kill + launch

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
    # TODO these are constants, sort of, should be all caps, maybe
    choices = [ 'help','launch', 'use', 'kill', 'status', 'force', 'wait' ]

    # Disk storage for persistent daemon state
    FN_PID    = "/tmp/garnet-daemon-pid"    # Daemon pid
    FN_STATUS = "/tmp/garnet-daemon-status" # Daemon status: 'busy' or 'ready'
    FN_STATE0 = "/tmp/garnet-daemon-state0" # Original state (args) of daemon
    FN_RELOAD = "/tmp/garnet-daemon-reload" # Desired new state (args)
    DAEMONFILES = [ FN_PID, FN_STATUS, FN_STATE0, FN_RELOAD ]

    # Convenient place to save pid instead of doing 'os.getpid()' all the time
    PID = os.getpid()
    
    # Convenient place to save args instead of passing them around via method calls (dangerous?)
    args = None

    # This is where we save unsaveable args :(
    saved_glb_params = None
    saved_pe_fc = None

    # Limit orphan checks to ONCE per session etc.
    did_orphan_already=False
    already_found_files=False

    # "PUBLIC" methods: initial_check(), loop()

    def initial_check(args):
        '''Process command found in <args>.daemon'''

        if args.daemon == None: return

        if args.daemon == "force":
            print(f'- hello here i am forcing a launch')
            GarnetDaemon.kill(dbg=1)
            args.daemon = "launch"

        if args.daemon == "help":
            GarnetDaemon.help(args); exit()

        elif args.daemon == "use":
            print("hello here i am doing a 'daemon use'", flush=True)
            GarnetDaemon.use(args); exit()

        elif args.daemon == "kill":
            GarnetDaemon.kill(dbg=1); exit()

        elif args.daemon == "status":
            GarnetDaemon.status(args); exit()

        elif args.daemon == "launch":
            GarnetDaemon.launch(args)

        elif args.daemon == "wait":
            GarnetDaemon.wait_daemon(args); exit()

    def launch(args):
        gd = GarnetDaemon
        gd.die_if_daemon_exists()
        gd.register_pid(); gs = gd.grid_size(args)    # E.g. "4x2"
        print(f'\n--- LAUNCHING {gs} DAEMON {gd.PID}')
        gd.put_status('busy')
        gd.save_state0(args)

    def loop(args, dbg=1):
        '''Launch daemon and/or watch for updates'''
        gd = GarnetDaemon; command = args.daemon
        print(f'- daemon.py/loop(): in the loop. command={command}')
        assert command == "launch" or command == "use", \
            f'Found command "{command}", should have been "launch" or "use"'

        # On launch, save pid and initial state in "state0" file
        if command == "launch":
            print(f'- DAEMON STOPS and waits...\n')
            sys.stdout.flush(); sys.stderr.flush()

        # Register status; stop and wait for CONT signal from client
        GarnetDaemon.put_status('ready')
        gd.sigstop()

        # Okay but how do we now who sent the CONT and if it's legit?
        # Answer: require client set status='load-and-go' before sending CONT
        while GarnetDaemon.get_status() != 'load-and-go':
            print(f'\nWARNING got CONT signal but "load-and-go" not set. Re-stopping...')
            gd.sigstop()

        # On CONT, register status and load new args from 'reload' file
        print(f'\n\n--- DAEMON RESUMES')
        GarnetDaemon.put_status('busy')
        return gd.load_args()

    # ------------------------------------------------------------------------
    # "Private" methods for processing individual daemon commands:
    #   def help()
    #   def use(args)
    #   def kill(dbg=1)
    #   def status(args)
    #   def wait_daemon(args):

    def help():
        print(GarnetDaemon_HELP)
        return GarnetDaemon_HELP

    def use(args):
        GarnetDaemon.wait_daemon(args)       # Wait for daemon to exist
        GarnetDaemon.save_args(args)         # Save args where the daemon will find them
        GarnetDaemon.args_match_or_die(args) # Grid size must match!!! (todo combine w/sigcont?)
        GarnetDaemon.sigcont()               # Tell daemon to CONTinue
        exit()                               # Kill yourself, daemon will take it from here...

    def kill(dbg=1):
        if GarnetDaemon.daemon_exists():
            pid = GarnetDaemon.retrieve_pid()  # FIXME there are way too many retrive_pid calls!!!
            if dbg: print(f'- found daemon pid {pid}, killing it now')
            GarnetDaemon.sigkill()
            time.sleep(1) # Maybe wait a second to let it die
        else:
            print(f'- daemon is already dead')

        print(f'- cleanup on aisle "/tmp"')
        GarnetDaemon.cleanup()

    def daemon_exists(pid=None):
        if not pid: pid = GarnetDaemon.retrieve_pid(dbg=0)
        process_exists = f'test -d /proc/{pid}'
        if not GarnetDaemon.do_cmd(process_exists): return False
        pstatus = psutil.Process(pid).status()
        if pstatus == 'zombie': return False
        return pid

    def status(args, verbose=True, dbg=0):
        gd = GarnetDaemon;
        if dbg: print(f'\n--- STATUS: daemon status requested')

        if dbg: print(f'- checking for orphans')
        GarnetDaemon.check_for_orphans()

        pid = GarnetDaemon.retrieve_pid()
        if dbg: print(f'- checking status of process {pid}')

        if not GarnetDaemon.daemon_exists():
            if verbose: print("- no daemon found")

            # Do this once per session only
            if    gd.already_found_files: return 'dead'
            else: gd.already_found_files = True
            for f in gd.DAEMONFILES: 
                if os.path.exists(f): print(f'WARNING found daemon file {f}')
            return 'dead'

        # Don't 'if dbg' this, pytest needs it
        if verbose: print(f'- found running daemon {pid}')

        state0_file = gd.FN_STATE0

        if not gd.do_cmd(f'test -f {state0_file}'):
            print(f'- WARNING: cannot find daemon state file "{state0_file}"')
            print(f'- WARNING: daemon state corrupted: suggest you do "kill {pid}"')
            return

        state0_args = gd.load_args(state0_file)
        grid_size = gd.grid_size(state0_args)
        if verbose: print(f'- found running {grid_size} daemon {pid}')

        with open(GarnetDaemon.FN_STATUS, 'r') as f:
            status = f.read()
            if verbose: print('- daemon_status: ' + status)
        return status

    def wait_daemon(args):
        '''Check daemon status, do not continue until/unless daemon exists AND IS READY'''
        gd = GarnetDaemon; gd.args = args
        time.sleep(2)
        while True:
            if GarnetDaemon.status(args) == 'ready': break
            # Each set of waits is broken down into groups b/c of stdout tees and lesses and flushes and such

            print(f'- daemon busy, will retry once per second for twenty seconds')
            print(f'- (in four groups of five seconds each)')
            if gd.check_daemon(20,   1, ngroups=4): break

            print(f'- daemon still busy, will do twenty more tries @ 2 sec each')
            if gd.check_daemon(20,   2, ngroups=4): break

            print(f'- 20 tries @ one minute per try:')  # Total 21 min wait
            if gd.check_daemon(20,  60, ngroups=4): break

            print(f'- 20 tries @ two minutes per try:') # Total 1 hr wait
            if gd.check_daemon(20, 120, ngroups=2): break

            print(f'- 12 tries @ 5 min / try"') # Total 2 hr wait
            if gd.check_daemon(12, 300, ngroups=3): break

            # sys.stderr.write('ERROR Timeout waiting for daemon. Did you forget to launch it?\n')
            sys.stderr.write('ERROR Timeout after two hours waiting for daemon.\n')
            sys.stderr.write('Maybe try again later.\n')
            exit(13)
            break

        print('\n--- DAEMON READY, continuing...')

    # ------------------------------------------------------------------------
    # "Private" methods for saving and restoring daemon state
    #     def save_state0(args)
    #     def save_args(args, fname)
    #     def load_args()

    def save_state0(args, dbg=0):
        GarnetDaemon.save_args(args, fname=GarnetDaemon.FN_STATE0)

    def save_args(args, fname=None, dbg=0):
        'Save current state (args) to arg-save (reload) file'

        # Oops well maybe that's okay
        # print(f'resetting glb params arg', flush=True)
        # for a in vars(args).items(): print(f'arg {a} has type {type(a)}')
        # try/except because these args do not exist in pytest trials...
        try:
            GarnetDaemon.saved_glb_params = args.glb_params
            args.glb_params = "SORRY cannot save/restore GlobalBufferParams!"

            GarnetDaemon.saved_pe_fc = args.pe_fc
            args.pe_fc = "SORRY cannot save/restore pe_fc of type <family_closure)!"
        except:
            print(f'WARNING could not save glb_params and/or pe_fc')

        # Save args as a sorted dict
        argdic = vars(args)
        sorted_argdic=dict(sorted(argdic.items()))

        if not fname: fname = GarnetDaemon.FN_RELOAD
        with open(fname, 'w') as f: json.dump(sorted_argdic, f)
        if dbg: print(f'- saved args {args} to {fname}')
        
        # try/except because these args do not exist in pytest trials...
        try:
            args.glb_params = GarnetDaemon.saved_glb_params
            args.pe_fc      = GarnetDaemon.saved_pe_fc
        except:
            print(f'WARNING could not restore glb_params and/or pe_fc')


    def load_args(fname=None, dbg=0):
        'Load state (args) from save-args (reload) file'
        if not fname: fname = GarnetDaemon.FN_RELOAD
        with open(fname, 'r') as f: args_dict = json.load(f)
        new_args = Namespace(**args_dict)

        # Oops well maybe that's okay
        try:
            print(f'restore args.{glb_params,pe_fc}')
            # assert args.GlobalBufferParams == "SORRY cannot save/restore GlobalBufferParams!"
            new_args.glb_params = GarnetDaemon.saved_glb_params
            new_args.pe_fc = GarnetDaemon.saved_pe_fc
        except: pass

        if dbg: print(f'- restored args {new_args} from {fname}')
        if dbg: print("- loaded args {json.dumps(args_dict, indent=4))}")
        return new_args

    # ------------------------------------------------------------------------
    # "Private" methods for interfacing with the daemon
    #     def die_if_daemon_exists():
    #     def check_for_orphans():
    #     def all_daemon_processes_except(*args):
    #     def args_match_or_die(daemon_args, client_args):

    def wait_stage(wait_secs, ntries):
        'Check daemon once every <wait_secs> seconds, timeout after <max> tries'
        sys.stdout.write(f'- wait{ntries} '); sys.stdout.flush()
        for i in range(ntries):
            time.sleep(wait_secs)
            sys.stdout.write('.'); sys.stdout.flush()
            status = GarnetDaemon.status(GarnetDaemon.args, verbose=False)
            if status == 'ready': print('', flush=True)
            if status == 'ready': return True
        print('', flush=True)
        return False

    def check_daemon(ntries, secs_per_try, ngroups=1):
        errmsg = f'\nERROR there is no daemon, did you forget to launch it?'
        assert GarnetDaemon.daemon_exists(), errmsg
        tries_per_group = int(ntries/ngroups)
        for g in range(ngroups):
            if GarnetDaemon.wait_stage(secs_per_try, tries_per_group): return True
        return False

    def die_if_daemon_exists():
        '''If existing daemon is found, issue an error message and die'''
        if GarnetDaemon.daemon_exists():
            g = GarnetDaemon
            # g.status(None, match_or_die=False)
            state0_args = g.load_args(g.FN_STATE0)
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

        # Only need to check for orphans ONCE per session 
        if GarnetDaemon.did_orphan_already: return True
        GarnetDaemon.did_orphan_already = True

        # Get all daemon processes EXCEPT:
        # - exclude "official" daemon
        # - exclude self because we might be in the process of launching
        # Why lambda? So it won't complain if element not found omg
        orphan_pids = GarnetDaemon.all_daemon_procs()
        def mydel(group, x):
            if x in group: group.remove(x)
        mydel(orphan_pids, GarnetDaemon.retrieve_pid() ) # "official" daemon is not orphan
        mydel(orphan_pids, GarnetDaemon.PID            )  # self is not orphan

        if orphan_pids == []: return False  # No orphans found

        print(f'********************************************************')
        for p in orphan_pids:
            print(f'WARNING found orphan daemon {p}, you should kill it!')

        # print(f'--------------------------------------------------------')
        pidstring_list = list(map(str, orphan_pids))
        pidstring = " ".join(pidstring_list)
        print(f'ps      {pidstring}')
        print(f'kill -9 {pidstring}')
        print(f'********************************************************')
        return True  # Found orphans

    def all_daemon_procs():
        '''Return a list of all daemon processes'''
        # Look for  procs w args "--daemon" AND "launch"
        # AND "garnet.py" b/c do not want false positive when
        # "aha garnet --deamon launch" spawns "garnet.py --daemon launch"
        def match(pid):
            try:    cmdline = psutil.Process(pid).cmdline()
            except: return False
            return  ("--daemon" in cmdline) and ("launch" in cmdline) and ("garnet.py" in cmdline)
        daemon_pids = list(filter( lambda pid: match(pid), psutil.pids() ))
        return daemon_pids
        
    def args_match_or_die(client_args):
        '''Daemon and client args must match exactly, else ERR and DIE'''
        gd = GarnetDaemon
        daemon_args = gd.load_args(GarnetDaemon.FN_STATE0)

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
        # Tell daemon that it's okay to process this particular CONT
        GarnetDaemon.put_status('load-and-go')

        if not pid: pid = GarnetDaemon.retrieve_pid()
        if dbg: print(f'- sending CONT to {pid}', flush=True)
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

    def put_status(jobstatus, pid=None, fname=None, dbg=1):
        "Save daemon status e.g. 'busy' or 'ready'"
        if not fname: fname = GarnetDaemon.FN_STATUS
        with open(fname, 'w') as f: f.write(jobstatus)
        
    def get_status(fname=None):
        "Get daemon status e.g. 'busy' or 'ready'"
        if not fname: fname = GarnetDaemon.FN_STATUS
        try:
            with open(fname, 'r') as f: status = f.read()
            # print(f'1 status={status}')
            return status
        except:
            print(f'WARNING could not read from daemon status file {fname}')
            return None
        
    def register_pid(pid=None, fname=None, dbg=0):
        'Write pid to pid-save file'
        if not pid:   pid = GarnetDaemon.PID
        if not fname: fname = GarnetDaemon.FN_PID
        with open(fname, 'w') as f: f.write(str(pid) + '\n')
        if dbg: print(f'- wrote pid {pid} to file {fname}')

    def retrieve_pid(fname=None, dbg=0):
        'Get pid from pid-save file'
        if not fname: fname = GarnetDaemon.FN_PID
        if not os.path.exists(fname):
            if dbg: print(f'- could not find daemon pid file {fname}')
            return None
        else:
            with open(fname, 'r') as f: pid = int(f.read().strip())
            if dbg: print(f'- got pid {pid} from file {fname}')
            return pid

    def cleanup(dbg=0):
        'If daemon is dead, delete files from /tmp, else ERROR'
        dpid = GarnetDaemon.daemon_exists()
        assert not dpid, f'\nERROR cannot cleanup, found existing daemon {dpid}'
        for f in GarnetDaemon.DAEMONFILES:
            try: os.remove(f)
            except OSError: pass
        return True

##############################################################################
# TESTING, see test_daemon.py
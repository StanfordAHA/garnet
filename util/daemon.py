import os, sys, signal, subprocess
import json
from argparse import Namespace

# FIXME/TODO CONSIDER:
# when you use 'self', and you change the class name, all is copacetic
# when you use 'g=GarnetDaemon'...whuh oh!  oh boy! nooooo


# FIXME/TODO double-check README etc.
# FIXME/TODO should probably have a cleanup() method that deletes tmp files etc.
# called from kill() maybe

README='''
PUBLIC contents
  help()    - daemon help (garnet_specific)
  status()  - print status of existing daemon, if any
  run()     - launch daemon and/or watch for updates
  kill()    - send KILL to daemon pid

PRIVATE contents
  pid             - daemon's process id
  filenames       - files where daemon stores its state (pid, state0, reload)
  do_cmd(cmd)     - executes cmd, returns status e.g. "do_cmd('ls -ld /tmp')
  register_pid()  - save current process id to path "fn"
  save_args(args) - save args object to "reload" file as json dump
  load_args()     - load and return args from "reload" file
  sigstop()       - kill -STOP <self>
  sigkill()       - kill -KILL <self>

SAMPLE USAGE

  def garnet.main(args):
      if args.daemon == "use_daemon": daemon.reload()
      elif args.daemon == "status":   daemon.status()
      elif args.daemon == "kill":     daemon.kill()
      garnet = create_cgra(...)
      while True:
        if args.do_verilog: do_verlog()
        if args.do_pnr: do_pnr()
        if not args.daemon: break
        args = daemon.run(args)

# WHERE
# 
#   def kill_daemon(): < kill -9 pid >
#   def use_daemon(args):
#       < save args >
#       < send CONT to daemon pid >
#       < exit() >
# 
#   def daemon.run(args):
#       < assert LAUNCH or USE >
#       < if LAUNCH: save state >
#       < wait >
#       < Can only continue if args.daemon == USE, right? >
#       < assert USE >
#       < load new state >
'''


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

class GarnetDaemon:

    # "PRIVATE" variables but this is the only indication because underbars are ugly

    pid = 0
    choices = ['help','launch', 'use-daemon', 'kill']
    filenames = {
        "pid"    : "/tmp/garnet-daemon-pid",    # Process ID of daemon
        "state0" : "/tmp/garnet-daemon-state0", # Original state (args) of daemon
        "reload" : "/tmp/garnet-daemon-reload", # Desired new state (args)
    }

    # PUBLIC methods

    def help():
        print(GarnetDaemon_HELP)
        return GarnetDaemon_HELP

    def status():
        g = GarnetDaemon; pid = g.pid
        print(f'--- Checking status of process {pid}')
        state0_file = g.filenames["state0"]
        cmd = f'test -d /proc/{pid}'
        if g.do_cmd( f'test -d /proc/{pid}' ):
            print(f'- found running daemon {pid}')
            if not g.do_cmd( f'test -f {state0_file}' ):
                print(f'- WARNING: daemon state corrupted: suggest you do "kill {pid}"')
                return
            state0_args = g.load_args(state0_file)
            print(f'- found daemon {pid} w launch-state args =\n  {state0_args}')
        else:
            print("- no daemon found")

    def run(args):
        'daemon.run()     - launch daemon and/or watch for updates'
        g = GarnetDaemon

        # Check that command is LAUNCH or USE
        command = args.daemon
        assert command == "launch" or command == "use"

        # On launch, save state and STOP
        if command == "launch":
            g.register_pid()
            g.save_args(args)
            assert g.pid == os.getpid()  # Should only be stopping SELF
            g.sigstop(g.pid)             # Stop and wait
        
        # On CONTinue, reload state and return
        args = g.load_args(); assert args.daemon == "use"  # Right? RIGHT???
        return args

    def kill(dbg=1):
        'KILL the daemon'
        g = GarnetDaemon
        g.sigkill(g.pid)

    # "PRIVATE" methods but this is the only indication because underbars are ugly


    def do_cmd(cmd):
        'Executes <cmd>, returns True or False according to whether command succeeded'
        # return subprocess.run(cmd.split(), shell=True).returncode == 0
        return subprocess.run(cmd, shell=True).returncode == 0

    def register_pid(fname=None, dbg=1):
        'Save (my) pid to pid-save file'
        g = GarnetDaemon
        g.pid = os.getpid()
        if not fname: fname = g.filenames['pid']
        if dbg: print(f'- found pid={g.pid}; saving to {fname}')
        with open(fname, 'w') as f: f.write(f'{g.pid}\n')
        if dbg: print(f'I am Damon the daemon, my pid is {g.pid}')

    def retrieve_pid(fname=None, dbg=1):
        'Get pid from pid-save file'
        if not fname: fname = GarnetDaemon.filenames['pid']
        with open(fname, 'r') as f: pid = f.read().strip()
        if dbg: print(f'- retrieved pid "{pid}" from "{fname}"')
        return pid

    def save_args(args, fname=None, dbg=1):
        'Save current state (args) to arg-save (reload) file'

        # Save args as a sorted dict
        argdic = vars(args)
        sorted_argdic=dict(sorted(argdic.items()))

        if not fname: fname = GarnetDaemon.filenames['reload']
        with open(fname, 'w') as f: json.dump(sorted_argdic, f)
        if dbg: print(f'- saved    args  to  {fname}')
        
    def load_args(fname=None, dbg=1):
        'Load state (args) from save-args (reload) file'
        if not fname: fname = GarnetDaemon.filenames['reload']
        with open(fname, 'r') as f: args_dict = json.load(f)
        if dbg: print(f'- restored args from {fname}')
        return Namespace(**args_dict)

    # Stop, but do not kill, pid. Can continue again w "sigcont"
    def sigstop(pid, dbg=1): os.kill(pid, signal.SIGSTOP)

    def sigcont(pid, dbg=1): os.kill(pid, signal.SIGCONT)


#         cmd = f'kill -STOP {str(g.pid)}'
#         if dbg: print(f'Stop and wait: {cmd}')
#         g.do_cmd(cmd)

    # Using TERM instead of KILL b/c a meme shamed me into it
    def sigkill(pid): os.kill(pid, signal.SIGTERM)

##############################################################################
# TESTING, see test_daemon.py

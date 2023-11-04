import os, sys, signal, subprocess
from argparse import Namespace
from daemon import GarnetDaemon
import time

# FIXME/TODO build (below) at test_test_daemon thingy that checks to
# see that there is a test for every method in daemon.py, see?

##############################################################################
# TESTING

# grep def\  util/daemon.py | grep -v ^# | sed 's/    def /def test_/'

# def test_help():
#     HELP = GarnetDaemon.help()
#     print(HELP)
#     assert HELP == GarnetDaemon_HELP

# def test_status():
# def test_run(args):
# def test_kill(): GarnetDaemon.sigkill()

# pytest --capture=no --noconftest --color=no util/daemon.py

# bookmark
# Continue w next test above

def test_do_cmd():
    print(f'\n--- DO_CMD')
    assert     GarnetDaemon.do_cmd("exit 0")
    assert not GarnetDaemon.do_cmd("exit 13")

# test_do_cmd(); exit()

def test_pid_save_and_restore():
    print(f'\n--- TEST_PID_SAVE_AND_RESTORE')
    tmpfile = f'/tmp/GarnetDaemon.test_pid_save_and_restore.{int(time.time())}'

    GarnetDaemon.register_pid(tmpfile, dbg=1)
    pid = GarnetDaemon.retrieve_pid(tmpfile, dbg=1)
    os.remove(tmpfile)
    print(f'- got pid {pid} from "{tmpfile}"')
    mypid = os.getpid(); mypid = str(mypid)
    assert mypid == pid, \
        f'My pid ({type(mypid)}{mypid}) != retrieved ({type(pid)}{pid})'

# test_pid_save_and_restore(); exit()

def test_register_pid():
    print(f'\n---  TEST_REGISTER_PID: see test_pid_save_restore()')
    # TODO

def test_retrieve_pid():
    print(f'\n---  TEST_RETRIEVE_PID: see test_pid_save_restore()')


# DONE: working as of 231104
def test_arg_save_and_restore():
    print(f'\n--- TEST_ARG_SAVE_AND_RESTORE():')
    args = Namespace( foo='bar', bar='baz' )
    tmpfile = f'/tmp/GarnetDaemon.test_arg_save_and_restore.{int(time.time())}'
    GarnetDaemon.save_args(args, tmpfile, dbg=1)  # Save to tmpfile
    new_args = GarnetDaemon.load_args(tmpfile)    # Load from tmpfile
    os.remove(tmpfile)
    print(f'- original args: {args}')
    print(f'- reloaded args: {new_args}')
    assert args == new_args

# DONE: working as of 231104
def test_save_args():
    print("\n--- TEST_SAVE_ARGS: see test_arg_save_and_restore()")

# DONE: working as of 231104
def test_load_args():
    print("\n--- TEST_LOAD_ARGS: see test_arg_save_and_restore()")

# DONE: working as of 231103
def test_sigstop():
    print(f'\n--- TEST_SIGSTOP: start writing dots to a file')
    tmpfile = f'/tmp/test_sigstop.{int(time.time())}'
    subprocess.run([ "bash", "-c", "/bin/rm -f /tmp/test_sigstop*"])
    p = subprocess.Popen([ 
        "bash", "-c", 
        f"while [ 1 ]; do echo -n .; sleep 1; done > {tmpfile}"
    ])
    pid = p.pid
    
    print(f'\nRun for awhile, see how many dots we gots')
    # Let it run awhile, then stop it and see how many dots
    time.sleep(4)
    print(f'- stopping (but not killing) {pid}')
    GarnetDaemon.sigstop(pid)
    with open(tmpfile, 'r') as f: dots0 = f.read()
    print(f'- found dots0 "{dots0}"')
    
    print(f'\nWait awhile, verify that dots did not change')
    time.sleep(4)
    GarnetDaemon.sigstop(pid)
    with open(tmpfile, 'r') as f: dots1 = f.read()
    print(f'- found dots1 "{dots1}"')
    assert dots0 == dots1

    print(f'\nRestart the process, run for awhile, verify different dots')
    GarnetDaemon.sigcont(pid)
    time.sleep(4)
    with open(tmpfile, 'r') as f: dots2 = f.read()
    print(f'- found dots2 "{dots2}"')
    assert dots1 != dots2

    print(f'\nClean up')
    p.terminate()
    subprocess.run([ "bash", "-c", "/bin/rm -f /tmp/test_sigstop*"])

# DONE: working as of 231102
def test_sigkill():
    # Give it ten minutes I dunno
    p = subprocess.Popen([ "bash", "-c", "sleep 600" ]); pid = p.pid
    print(f'\n--- TEST_SIGKILL: Started ten-minute sleep process {pid}')
    # GarnetDaemon.do_cmd(f'ls -ld /proc/{pid}')
    # Kill it!
    print(f'Killing {pid}')
    GarnetDaemon.sigkill(pid)
    # Poke it and see if it's dead
    try:
        import psutil
        p = psutil.Process(pid)
        stat = p.status()
    except:
        print(f'Process {pid} no longer exists. Success!'); return

    # Did not need this after all (yet)
    # assert stat == 'zombie'
    # print(f'Process {pid} is now a zombie. Good enough!'); return

test_sigkill()

import os, sys, signal, subprocess
from argparse import Namespace
from daemon import GarnetDaemon
import time

def min_sleep():
    import time; time.sleep(1)


# Don't need unit tests if comprehensive tests are good.
# But yes do turn them on for comprehensive/interactive testing.
# Not much difference either, way, at this point, really...may as well not skip...
SKIP_UNIT_TESTS = True
SKIP_UNIT_TESTS = False

# Useful globals (is this bad?)
MYPATH = os.path.realpath(__file__)  # E.g. "/aha/garnet/daemon/test_daemon.py"
MYDIR = os.path.dirname(MYPATH)

def DAEMON(w=4,h=2): return f'python3 {MYPATH} --width {w} --height {h} --daemon'
DAEMON7x13 = DAEMON(7,13)
DAEMON3x5  = DAEMON(3, 5)
DAEMON = DAEMON(7,13) # This is the default? Really?? Good for testing maybe i dunno.


# How to: interactive pytest run with full stdout::
#   pytest --capture=no --noconftest --color=no daemon/test_daemon.py

# Test of tests: for each method in daemon.py, there should be a test here in test_daemon.py
def test_tests(dbg=0):
    '''For each func def "f" in daemon.py, verify there exists "test_f" in test_daemon.py'''
    announce()

    daemon_home = MYDIR + "/daemon.py"
    if dbg: print(f'i think i am "{MYPATH}"')
    if dbg: print(f'i think i am in dir "{MYDIR}"')
    if dbg: print(f'i think daemon.py is here: "{daemon_home}"')

    find_dfuncs = f"egrep '^    def ' {daemon_home} | sed 's/(.*//' | sed 's/^    def //'"
    daemon_defs = subprocess.run(find_dfuncs, 
        capture_output=True, text=True, shell=True).stdout.split()
    if dbg: print(f'module defs={daemon_defs}')
    
    find_tfuncs = f"egrep '^def ' {MYPATH} | sed 's/(.*//' | sed 's/^def //'"
    test_defs = subprocess.run(find_tfuncs, 
        capture_output=True, text=True, shell=True).stdout.split()
    if dbg: print(f'test defs={test_defs}')

    badstr = ""
    goodstr = ""
    found_bad = False
    for d in daemon_defs:
        if f"test_{d}" in test_defs:
            goodstr = goodstr + f'    test_{d}()\n'
        else:
            badstr = badstr + f'    {d}()\n'
    if goodstr != "":
        print('\nFound tests:\n' + goodstr)
    if badstr != "":
        print("ERROR could not find test(s) for:\n" + badstr)
        assert False, "Could not find tests for:\n" + badstr

##################################################################
# Prototype daemon for testing. Can do e.g.
#     alias daemon="python3 $GARNET/util/test_daemon.py --daemon"
#     daemon launch     # launches 4x2 daemon i guess
#     daemon use        # uses 4x2 daemon i guess
#     daemon use        # uses 4x2 daemon i guess
#     daemon kill       # kills the daemon
#     daemon launch --width 7 --height 13   # launches 7x13 daemon
#     etc.
# (Also see 'def __main()' far below.)

def my_test_daemon():
    # announce() NO! not a test omg
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--width',  type=int, default=4)
    parser.add_argument('--height', type=int, default=2)
    parser.add_argument('--daemon', type=str, choices=GarnetDaemon.choices, default=None)
    parser.add_argument('--animal', type=str, default='mousie')
    args = parser.parse_args()

    GarnetDaemon.initial_check(args)
        # "launch" => ERROR if daemon exists already else continue
        # "force"  => kill existing daemon, then continue
        # "status" => echo daemon status and exit
        # "use"    => send args to daemon and exit
        # "kill"   => kill existing daemon and exit
        # "help"   => echo help and exit

    # Build CGRA (stub)
    grid_size = GarnetDaemon.grid_size(args)
    garnet_ckt = f"{grid_size} garnet circuit number {os.getpid()}"
    print(f'\nBuilt {garnet_ckt}')

    # Daemonology; TODO this could be a separate method call
    while True:
        if not args.daemon: break

        # WAIT for a client to send new args for processing
        print('\nLOOPING')
        args = GarnetDaemon.loop(args)
        print(f'- loaded new args {args} i guess?')

    exit()

########################################################################
# Comprehensive full-system tests using prototype daemon
#    test_daemon_launch()                 # kill-status-launch-wait-status-kill-status
#    test_kill_launch_kill_status_klks()  # A test that failed once upon a time
#    test_double_launch()
#    test_incompatible_daemon()

def kill_existing_daemon():
    print(f"Kill existing daemon (p.stdout should say 'already dead')"); sys.stdout.flush()
    p = subprocess.run(f'{DAEMON} kill'.split())

def kill_running_daemon():
    print("Kill the daemon (p.stdout should NOT say 'already dead')"); sys.stdout.flush()
    p = subprocess.run(f'{DAEMON} kill'.split()); sys.stdout.flush()

def launch_daemon_and_verify(daemon=DAEMON):
    kill_existing_daemon(); verify_no_daemon()
    print(f'Launch a daemon', flush=True)
    p = subprocess.Popen(f'{DAEMON} launch'.split()); pid0 = p.pid
    print(f'- wait two seconds', flush=True)
    min_sleep()
    # time.sleep(2)
    pid1 = verify_daemon_running(); assert pid0 == pid1
    # TODO look for e.g. 'Built 7x13' ? Merge w force_launch below?
    return pid0

def force_launch_and_capture(capture_file):
    cmd=f'{DAEMON} force |& tee {capture_file}'
    p1 = subprocess.Popen(['bash', '-c', cmd])
    min_sleep()

    print('\nAPRES LAUNCH')
    daemon_out = print_file_contents_w_prefix('DAEMON: ', capture_file)

    assert 'Built 7x13' in daemon_out
    print('\nFirst assertion PASSED')


def verify_no_daemon():
    print(f'Check daemon status, should be "no daemon found"'); sys.stdout.flush()
    p = subprocess.run(f'{DAEMON} status'.split(), text=True, capture_output=True)
    print(p.stdout); assert('no daemon found') in p.stdout

def verify_daemon_running():
    print('Check daemon status, should be "found running daemon"'); sys.stdout.flush()
    p = subprocess.run(f'{DAEMON} status'.split(), text=True, capture_output=True)
    print(p.stdout); assert('found running daemon') in p.stdout

    # Extra credit: return pid of running daemon
    import re
    pid = re.search(r'found running daemon ([0-9]+)', p.stdout).group(1)
    return int(pid)

########################################################################
# TESTS

def test_daemon_launch():  # kill-launch-kill
    'Launch daemon, see if it is running; kill the daemon, see if it is dead'
    announce()
    launch_daemon_and_verify()

def test_double_launch():  # kill-launch-launch-kill
    'Should complain if try to launch a second daemon when one is already running'
    announce()
    launch_daemon_and_verify()    # Launch first daemon

    print('Attempting to launch a second daemon, should get an error message')
    p = subprocess.Popen(f'{DAEMON} launch'.split(), stderr=subprocess.PIPE, text=True)
    # time.sleep(10)
    # time.sleep(2)
    min_sleep()
    # First verify that process died on its own:
    status = p.poll()
    assert status, 'Oops second daemon should have errored out by now'

    for line in p.stderr.readlines():
        if 'found existing' in line:
            print(f'Successfully found double-launch error "{line.strip()}"'); break

    # Note because it did not use 'nohup', first daemon will die when pytest ends and that's okay.

def test_force_launch():
    'If daemon already exists, --force-launch should kill it without erroring out.'
    announce(); daemon = DAEMON
    pid1 = launch_daemon_and_verify()


    print(f'Force-launch a second daemon, it should kill the first one'); sys.stdout.flush()
    p = subprocess.Popen(f'{DAEMON} force-launch'.split())
    
    # Wait a bit, then see if the new daemon is running
    # time.sleep(10)
    # time.sleep(2)
    min_sleep()
    pid2 = verify_daemon_running()
    print(f'Checking first (dead) daemon {pid1} not same as new daemon {pid2}...')
    assert int(pid2) != int(pid1)
    print('...okay!')

# test_daemon_use()
#   launch, look for 'Built 7x13' and NOT 'continuing with'
#   use --animal owl, look for 'continuing with 7x13' AND 'using animal: owl' AND NOT 'Built' 
#   use --animal ostrich, osprey, octopus, etc.

def print_file_contents_w_prefix(prefix, filename):
    with open(filename, 'r') as f: file_contents = f.read()
    lines = prefix + f'\n{prefix}' .join(file_contents.split('\n'))
    print(lines)
    sys.stdout.flush()
    return file_contents

def test_daemon_use():
    # from subprocess import Popen, PIPE
    announce()
    tmpfile = f'GarnetDaemon.test_daemon_use.{int(time.time())}'
    force_launch_and_capture(tmpfile)

    p2 = subprocess.run(f'{DAEMON} use --animal foxy'.split(), text=True, capture_output=True)
    sys.stdout.flush()
    min_sleep()

    print('\nWAKEUP and flush')
    daemon_out = print_file_contents_w_prefix('DAEMON: ', tmpfile)

    os.remove(tmpfile)
    assert 'using animal: foxy' in daemon_out
    print('\nSecond assertion PASSED')

    print('\nKILL the daemon\n')
    subprocess.run(f'{DAEMON} kill'.split())

def test_incompatible_daemon():
    'launch a 7x13 daemon; use a 3x5 daemon; check for error'
    announce()
    tmpfile = f'GarnetDaemon.test_incompatigle_daemon.{int(time.time())}'
    force_launch_and_capture(tmpfile)
    os.remove(tmpfile)

    p2 = subprocess.run(f'{DAEMON3x5} use --animal zebra'.split(), text=True, capture_output=True)
    # p2 = subprocess.run(f'{DAEMON3x5} use --animal zebra'.split())
    print(p2.stdout) # FIXME/ERROR pt.stdout says "found 3x5 daemon"
    print(p2.stderr)
    assert "ERROR: Daemon uses" in p2.stderr
    print('\nSLEEP 2\n')
    sys.stdout.flush()
    # time.sleep(2)
    min_sleep()


    print('\nKILL the daemon\n')
    subprocess.run(f'{DAEMON} kill'.split())

def test_help():
    announce()
    print('')
    print('------------------------------------------------------------------------')
    print("VISUAL CHECK: DOES THIS LOOK RIGHT TO YOU?")
    print('------------------------------------------------------------------------')
    GarnetDaemon.help()

########################################################################
# Unit tests (optional)

# Okay to use comprehensive test(s) for these, for now
def test_initial_check(): announce_unit('later')
def test_loop():          announce_unit('later')
def test_use():           announce_unit('later')

def test_kill(dbg=1):
    if announce_unit(): return

    # Start a dummy process
    p = subprocess.Popen("sleep 500".split()); pid = p.pid

    # Register it as though it were the daemon
    fname = GarnetDaemon.fn_pid
    with open(fname, 'w') as f: f.write(f'{pid}\n')
    print(f'- wrote pid {pid} to file "{fname}" maybe')

    # Check that it's still running
    print(f"- ps {pid}")
    exists = subprocess.run(f"ps {pid}", shell=True); assert exists

    # Kill it maybe, then poke it and see if it's dead
    GarnetDaemon.kill(dbg=1)
    assert poke_it_and_see_if_its_dead(pid)

def test_daemon_exists():
    announce_unit(': sufficiently covered by other tests already')

def test_status():      announce_unit('later')
def test_save_state0(): announce_unit('later')

def test_save_args(): announce_unit(': see test_arg_save_and_restore()')
def test_load_args(): announce_unit(': see test_arg_save_and_restore()')
def test_arg_save_and_restore():
    if announce_unit(): return
    args = Namespace( foo='bar', bar='baz' )
    tmpfile = f'/tmp/GarnetDaemon.test_arg_save_and_restore.{int(time.time())}'
    GarnetDaemon.save_args(args, tmpfile, dbg=1)  # Save to tmpfile
    new_args = GarnetDaemon.load_args(tmpfile)    # Load from tmpfile
    os.remove(tmpfile)
    print(f'- original args: {args.__dict__}')
    print(f'- reloaded args: {new_args.__dict__}')
    assert args == new_args

def test_daemon_wait(): announce_unit('later')
def test_die_if_daemon_exists(): announce_unit('later')
def test_check_for_orphans(): announce_unit('later')
def test_all_daemon_processes_except(): announce_unit('later')
def test_args_match_or_die(): announce_unit('later')

def test_do_cmd():
    if announce_unit(): return
    assert     GarnetDaemon.do_cmd("exit 0")
    assert not GarnetDaemon.do_cmd("exit 13")

def test_sigstop():
    if announce_unit(msg=": start writing dots to a file"): return

    # Start writing dots to a file
    tmpfile = f'/tmp/test_sigstop.{int(time.time())}'
    subprocess.run([ "bash", "-c", "/bin/rm -f /tmp/test_sigstop*"])
    p = subprocess.Popen([
        "bash", "-c", 
        f"while [ 1 ]; do echo -n .; sleep 1; done > {tmpfile}"
    ])
    
    print(f'\n- run for awhile, see how many dots we gots')
    time.sleep(2); pid = p.pid

    print(f'- stop (but do not kill) dot-writing process {pid}')
    GarnetDaemon.sigstop(pid)
    with open(tmpfile, 'r') as f: dots0 = f.read()
    print(f'- found dots0 "{dots0}"')
    
    print(f'\nWait awhile, verify that dots did not change')
    time.sleep(2); GarnetDaemon.sigstop(pid)
    with open(tmpfile, 'r') as f: dots1 = f.read()
    print(f'- found dots1 "{dots1}"')
    assert dots0 == dots1

    print(f'\nRestart the process, run for awhile, verify different dots')
    GarnetDaemon.sigcont(pid)
    time.sleep(2)
    with open(tmpfile, 'r') as f: dots2 = f.read()
    print(f'- found dots2 "{dots2}"')
    assert dots1 != dots2

    print(f'\nClean up')
    p.terminate()
    subprocess.run([ "bash", "-c", "/bin/rm -f /tmp/test_sigstop*"])

def test_sigcont(): announce_unit(msg=": see test_sigstop()")

def test_sigkill():
    if announce_unit(): return

    # Give it a 5-min timeout I dunno...so it will eventually die on its own if things go south
    p = subprocess.Popen([ "bash", "-c", "sleep 600" ]); pid = p.pid
    print(f'- started sleep process {pid}')
    # GarnetDaemon.do_cmd(f'ls -ld /proc/{pid}')

    # Kill it!
    print(f'Killing {pid}')
    GarnetDaemon.sigkill(pid)

    # See if its dead
    assert poke_it_and_see_if_its_dead(pid)

# TODO should do this, maybe, and not as a unit test, maybe
def test_grid_size(): announce('todo')

def test_pid_save_and_restore():
    if announce_unit(): return
    tmpfile = f'/tmp/GarnetDaemon.test_pid_save_and_restore.{int(time.time())}'
    GarnetDaemon.register_pid(fname=tmpfile, dbg=1)
    pid = GarnetDaemon.retrieve_pid(fname=tmpfile, dbg=1)
    os.remove(tmpfile)
    assert int(os.getpid()) == int(pid), f'My pid ({mypid} != retrieved pid {pid})'

def test_retrieve_pid(): announce_unit(': see test_pid_save_restore()')
def test_register_pid(): announce_unit(': see test_pid_save_restore()')

########################################################################
# Helper functions

# Used by test_kill, test_sigkill
def poke_it_and_see_if_its_dead(pid):
    try:
        import psutil
        p = psutil.Process(pid)  # Fails if proc gone entirely
        stat = p.status().status # Fails if proc is a zombie (I guess?)
        # Success means failure
        return False
    except:
        print(f'Process {pid} no longer exists. Success!')
        return True

def skip_unit_tests():
    if SKIP_UNIT_TESTS:
        print('- skipping unit tests'); return True
    else:               return False

def announce(msg=''):
    import inspect
    curframe    = inspect.currentframe()
    callerframe = inspect.getouterframes(curframe, 2)
    caller = callerframe[1][3]
    print('\n========================================================================')
    if msg == 'todo' or msg == 'later':
        msg = '- TODO do not yet have a test for this'
    print(f"--- TEST: {caller}(){msg}")
    sys.stdout.flush()
    
# Return True if we are supposed to skip this test
def announce_unit(msg=''):
    announce(msg)
    if SKIP_UNIT_TESTS: print('- skipping unit tests')
    return SKIP_UNIT_TESTS


########################################################################
# main()

# Run the proto daemon if this script called with args e.g. "--daemon launch"
if __name__ == "__main__":
    if len( sys.argv ) > 1: my_test_daemon()

# DONE
# - run complete pytest, clean up the messy output
# - run complete pytest, speed up the slow pauses
# - make sure everyone has the appropriate announce()
# - run with skip-test FALSE
# - run with skip-tests TRUE

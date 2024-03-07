import os, sys, subprocess
from argparse import Namespace
from daemon import GarnetDaemon
import time

def min_sleep(): time.sleep(1)

# Can optionally skip unit tests
# TODO separate test_daemon.py, test_units.py?
SKIP_UNIT_TESTS = True
SKIP_UNIT_TESTS = False

# Useful globals
MYPATH = os.path.realpath(__file__)  # E.g. "/aha/garnet/daemon/test_daemon.py"
MYDIR  = os.path.dirname(MYPATH)

def DAEMON(w=4,h=2): return f'python3 {MYPATH} --width {w} --height {h} --daemon'
DAEMON7x13 = DAEMON(7,13)
DAEMON3x5  = DAEMON(3, 5)
DAEMON     = DAEMON(7,13) # This is the default? Really?? Good for testing maybe i dunno.

# How to: interactive pytest run with full stdout::
#     pytest --capture=no --noconftest --color=no daemon/test_daemon.py

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
#     daemon kill       # kills the daemon
#     daemon launch --width 7 --height 13   # launches 7x13 daemon
#     etc.
# Can use --animal arg to test arg save/reload
# (Also see 'def __main()' far below.)

def mydaemon():
    # announce() NO! not a test omg

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--width',  type=int, default=4)
    parser.add_argument('--height', type=int, default=2)
    parser.add_argument('--daemon', type=str, choices=GarnetDaemon.choices, default=None)
    parser.add_argument('--animal', type=str, default='mousie')
    parser.add_argument('--buildtime', type=int, default=0)
    args = parser.parse_args()

    GarnetDaemon.initial_check(args)
        # "launch" => ERROR if daemon exists already else continue
        # "force"  => kill existing daemon, then continue
        # "status" => echo daemon status and exit
        # "use"    => send args to daemon and exit
        # "kill"   => kill existing daemon and exit
        # "help"   => echo help and exit

    # Build CGRA/animal (stub)
    grid_size = GarnetDaemon.grid_size(args)
    garnet_ckt = f"{grid_size} garnet circuit number {os.getpid()}"
    print(f'\nPretend like it takes {args.buildtime} seconds to build the circuit')
    print(f'- waiting {args.buildtime} seconds...', flush=True)
    time.sleep(args.buildtime)
    print(f'\nBuilt {garnet_ckt} animal {args.animal}')
    print(f'- using animal: {args.animal}')

    # Daemonology; TODO this could be a separate method call
    while True:
        childpid = os.fork() # Fork a child
        if childpid > 0:
            pid, status = os.waitpid(childpid, 0) # Wait for child to finish
            print(f'Child process {childpid} finished with exit status {status}')
            assert pid == childpid # Right???

            # IF we're not running as a daemon, we're done here.
            if not args.daemon: break

            # ELSE parent (daemon) WAITs for a client to send new args for processing
            print('\nLOOPING')
            args = GarnetDaemon.loop(args)
            continue

        # Forked child process does the work, then exits
        print(f'- loaded new args {args} i guess?')
        print(f'- gonna build a: {args.animal} grid')
        print( ' -updated/used the grid')
        print(f'- using animal: {args.animal}')
        exit() # Or should it be 'break'?

    exit()

########################################################################
# Comprehensive full-system tests using prototype daemon

def test_daemon_launch():  # kill-launch-kill
    'Launch daemon, see if it is running; kill the daemon, see if it is dead'
    announce(); launch_daemon_and_verify()
    kill_existing_daemon()

def test_double_launch():  # kill-launch-launch-kill
    'Should complain if try to launch a second daemon when one is already running'
    announce(); launch_daemon_and_verify()    # Launch first daemon

    print('Attempting to launch a second daemon, should get an error message')
    p = subprocess.Popen(f'{DAEMON} launch'.split(), stderr=subprocess.PIPE, text=True)
    min_sleep()
    # First verify that process died on its own:
    status = p.poll()
    assert status, 'Oops second daemon should have errored out by now'

    for line in p.stderr.readlines():
        if 'found existing' in line:
            print(f'Successfully found double-launch error "{line.strip()}"'); break

    # Note because it did not use 'nohup', first daemon will die when pytest ends and that's okay.
    kill_existing_daemon()

def test_force_launch():
    'If daemon already exists, --force should kill it without erroring out.'
    announce(); daemon = DAEMON
    pid1 = launch_daemon_and_verify()

    print('Force-launch a second daemon, it should kill the first one'); sys.stdout.flush()
    p = subprocess.Popen(f'{DAEMON} force'.split())
    
    # Wait a bit, then see if the new daemon is running
    min_sleep()
    pid2 = verify_daemon_running()
    print(f'Checking first (dead) daemon {pid1} not same as new daemon {pid2}...')
    assert int(pid2) != int(pid1)
    print('...okay!')
    kill_existing_daemon()

def test_slow_test():
    'Test daemon-wait mechanism for too-early "daemon use" attempts'
    announce()
    tmpfile = f'deleteme-GarnetDaemon.test_slow_test.{int(time.time())}'

    expect(f'{DAEMON} kill', '')
    expect(f'{DAEMON} status', 'no daemon found')

    # Launch a slow daemon, takes 12 seconds to finish its task
    force_launch_and_capture(tmpfile, cmd='force --buildtime 12')

    print('--- STATUS')
    expect(f'{DAEMON} status', 'daemon_status: busy')

    catnew_reset()
    print('--- SLOTH');      try_animal('sloth',      tmpfile)
    print('--- SLOW LORIS'); try_animal('slow-loris', tmpfile)
    os.remove(tmpfile)

    expect(f'{DAEMON} kill', 'killing it now')

# test_daemon_use()
#   launch, look for 'Built 7x13' and NOT 'continuing with'
#   use --animal foxy, look for 'continuing with 7x13' AND 'using animal: foxy' AND NOT 'Built'

def test_daemon_use():
    # from subprocess import Popen, PIPE
    announce()
    catnew_reset()
    tmpfile = f'deleteme-GarnetDaemon.test_daemon_use.{int(time.time())}'
    force_launch_and_capture(tmpfile)
    verify_successful_build(tmpfile)  # (calls catnew)
    print('\nFirst assertion PASSED')

    # TODO maybe use expect() instead???

    p2 = subprocess.run(f'{DAEMON} use --animal foxy'.split(), text=True, capture_output=True)

    print('\nKILL the daemon\n')
    subprocess.run(f'{DAEMON} kill'.split())

    print('\nWAKEUP and flush')
    daemon_out = catnew(tmpfile)
    print_w_prefix('DAEMON: ', daemon_out)
    os.remove(tmpfile)
    assert 'using animal: foxy' in daemon_out
    print('\nSecond assertion PASSED')
    # FIXME/TODO where is first assertion? what's going on here?

def test_daemon_auto():
    'Same as test_daemon_use except "auto" instead'
    announce()
    catnew_reset()

    print('\nKILL any existing daemon\n')
    subprocess.run(f'{DAEMON} kill'.split())

    tmpfile = f'deleteme-GarnetDaemon.test_daemon_auto.{int(time.time())}'
    force_launch_and_capture(tmpfile, cmd='auto')
    verify_successful_build(tmpfile)  # (calls catnew)
    print('\nFirst assertion PASSED')

    p2 = subprocess.run(f'{DAEMON} auto --animal foxy'.split(), text=True, capture_output=True)
    sys.stdout.flush()
    min_sleep()
    p3 = subprocess.run(f'{DAEMON} wait'.split(), text=True, capture_output=True)

    print('\nKILL the daemon\n')
    subprocess.run(f'{DAEMON} kill'.split())

    print('\nWAKEUP and flush')
    daemon_out = catnew(tmpfile)
    print_w_prefix('DAEMON: ', daemon_out)
    os.remove(tmpfile)
    assert 'using animal: foxy' in daemon_out
    print('\nSecond assertion PASSED')
    # FIXME/TODO where is first assertion? what's going on here?





def test_incompatible_daemon():
    'Launch a 7x13 daemon; try to use a 3x5 daemon; verify error'
    announce()
    tmpfile = f'deleteme-GarnetDaemon.test_incompatible_daemon.{int(time.time())}'
    force_launch_and_capture(tmpfile)
    verify_successful_build(tmpfile)
    print('\nFirst assertion PASSED')
    os.remove(tmpfile)

    # status check should *not* err out for size difference!
    p1 = subprocess.run(f'{DAEMON3x5} status'.split(), text=True, capture_output=True)
    print(p1.stdout); print(p1.stderr)
    assert "ERROR: Daemon uses" not in p1.stderr
    print('Second assertion PASSED')
    sys.stdout.flush(); min_sleep()

    p2 = subprocess.run(f'{DAEMON3x5} use --animal zebra'.split(), text=True, capture_output=True)
    # p2 = subprocess.run(f'{DAEMON3x5} use --animal zebra'.split())
    print(p2.stdout) # FIXME/ERROR pt.stdout says "found 3x5 daemon"
                     # Eh? what's wrong with that??
    print(p2.stderr)
    assert "ERROR: Daemon uses" in p2.stderr
    print('Third assertion PASSED (task failed successfully)')
    sys.stdout.flush(); min_sleep()

    print('\nKILL the daemon\n'); subprocess.run(f'{DAEMON} kill'.split())

def test_help():
    announce()
    print('')
    print('------------------------------------------------------------------------')
    print("VISUAL CHECK: DOES THIS LOOK RIGHT TO YOU?")
    print('------------------------------------------------------------------------')
    subprocess.run(f'{DAEMON} help'.split())

########################################################################
# Unit tests (optional)

# Okay to use comprehensive test(s) for these, for now
def test_initial_check(): announce_unit('later')
def test_loop():          announce_unit('later')
def test_use():           announce_unit('later')
def test_launch():        announce_unit('later')

def test_kill(dbg=1):
    if announce_unit(): return

    # Start a dummy process
    p = subprocess.Popen("sleep 500".split()); pid = p.pid

    # Register it as though it were the daemon
    GarnetDaemon.register_pid(pid)
    print(f'- wrote pid {pid} to pid-save file maybe')

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
    args = Namespace( ENV=dict(os.environ), foo='bar', bar='baz' )
    tmpfile = f'/tmp/deleteme-GarnetDaemon.test_arg_save_and_restore.{int(time.time())}'
    orig_args_dict = (args.__dict__).copy() # save_args adds e.g. args.pe_fc=None
    GarnetDaemon.save_args(args, tmpfile, dbg=1)  # Save to tmpfile
    new_args = GarnetDaemon.load_args(tmpfile)    # Load from tmpfile
    new_args_dict = new_args.__dict__
    os.remove(tmpfile)
    print(f'- original args: {orig_args_dict}')
    print(f'- reloaded args: { new_args_dict}')
    assert orig_args_dict == new_args_dict

def test_die_if_daemon_exists(): announce_unit('later')
def test_check_for_orphans(): announce_unit('later')
def test_args_match_or_die(): announce_unit('later')
def test_all_daemon_procs():  announce_unit('later')
def test_wait_daemon(): announce_unit('later')

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
    
    print('\n- run for awhile, see how many dots we gots')
    time.sleep(2); pid = p.pid

    print(f'- stop (but do not kill) dot-writing process {pid}')
    GarnetDaemon.sigstop(pid)
    with open(tmpfile, 'r') as f: dots0 = f.read()
    print(f'- found dots0 "{dots0}"')
    
    print('\nWait awhile, verify that dots did not change')
    time.sleep(2); GarnetDaemon.sigstop(pid)
    with open(tmpfile, 'r') as f: dots1 = f.read()
    print(f'- found dots1 "{dots1}"')
    assert dots0 == dots1

    print('\nRestart the process, run for awhile, verify different dots')
    GarnetDaemon.sigcont(pid)
    time.sleep(2)
    with open(tmpfile, 'r') as f: dots2 = f.read()
    print(f'- found dots2 "{dots2}"')
    assert dots1 != dots2

    print('\nClean up')
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
    tmpfile = f'/tmp/deleteme-GarnetDaemon.test_pid_save_and_restore.{int(time.time())}'
    GarnetDaemon.register_pid(fname=tmpfile, dbg=1)
    pid = GarnetDaemon.retrieve_pid(fname=tmpfile, dbg=1)
    os.remove(tmpfile); mypid = os.getpid()
    assert mypid == pid, f'My pid ({mypid} != retrieved pid {pid})'

def test_status_save_and_restore():
    if announce_unit(): return
    tmpfile = f'/tmp/deleteme-GarnetDaemon.test_status_save_and_restore.{int(time.time())}'
    s1 = 'waiting'
    GarnetDaemon.put_status(s1, fname=tmpfile)
    s2 = GarnetDaemon.get_status(fname=tmpfile)
    os.remove(tmpfile)
    assert s1 == s2, f'Loaded status {s1} != retrieved status {s2})'

def test_register_pid(): announce_unit(' - see test_pid_save_restore()')
def test_retrieve_pid(): announce_unit(' - see test_pid_save_restore()')
def test_put_status():   announce_unit(' - see test_status_save_restore()')
def test_get_status():   announce_unit(' - see test_status_save_restore()')

def test_cleanup():      announce_unit(': TBD')
def test_wait_stage():   announce_unit(': TBD')
def test_check_daemon(): announce_unit(': TBD')

def test_save_the_unsaveable():    announce_unit(': TBD')

########################################################################
# Helper functions

def catnew_reset():
    global FILE_INDEX; FILE_INDEX = 0

def catnew(filename, reset=False):
    'cat everything in file since last newcat() call'
    if reset: catnew_reset()

    with open(filename, 'r') as f: file_contents = f.read()
    lines = file_contents.split('\n')

    # Cut out the first n lines, where n=FILE_INDEX; update FILE_INDEX
    global FILE_INDEX
    del lines[:FILE_INDEX]; FILE_INDEX += len(lines)
    return '\n'.join(lines)

def print_w_prefix(prefix, text):
    lines = text.split('\n')
    formatted_contents = prefix + f'\n{prefix}' .join(lines)
    print(formatted_contents)
    sys.stdout.flush()
    return 

def try_animal(animal, tmpfile):
    assert expect(f'{DAEMON} use --animal {animal}', 'sending CONT')
    print(f'- sacrificing {animal} to daemon', flush=True)

    # Show what happened since last time daemon was used
    daemon_out = catnew(tmpfile, reset=False)
    print_w_prefix('DAEMON: ', daemon_out)

    assert f'using animal: {animal}' in daemon_out

def expect(cmd, expect):
    '''Run <cmd> and display output. Return True if output contains <spect> string'''
    # TODO for extra credit maybe <expect> could be a regex omg
    # print('launching expect process')
    p = subprocess.run(
        cmd.split(), text=True, 
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # Print stdout
    print(f'({cmd}) ')
    prefix='    '
    print((prefix+p.stdout).replace('\n',f'\n{prefix}'), flush=True)
    print('', flush=True)

    # Did we get what we expected?
    if expect in p.stdout: return True
    else:                  return False

def kill_existing_daemon():
    print("Kill existing daemon (p.stdout should say 'already dead')",flush=True)
    p = subprocess.run(f'{DAEMON} kill'.split())
    GarnetDaemon.cleanup()

def kill_running_daemon():
    print("Kill the daemon (p.stdout should NOT say 'already dead')", flush=True)
    p = subprocess.run(f'{DAEMON} kill'.split()); sys.stdout.flush()

def launch_daemon_and_verify(daemon=DAEMON):
    kill_existing_daemon()
    print('Launch a daemon', flush=True)
    p = subprocess.Popen(f'{DAEMON} launch'.split()); pid0 = p.pid
    print('- wait two seconds', flush=True)
    min_sleep()
    pid1 = verify_daemon_running(); assert pid0 == pid1
    # TODO look for e.g. 'Built 7x13' ? Merge w force_launch below?
    return pid0

def verify_successful_build(capture_file):
    print('\nAPRES LAUNCH')
    daemon_out = catnew(capture_file, reset=True)
    print_w_prefix('DAEMON: ', daemon_out)
    assert 'Built 7x13' in daemon_out

def force_launch_and_capture(capture_file, cmd='force'):
    cmd=f'{DAEMON} {cmd} |& tee {capture_file}'
    p1 = subprocess.Popen(['bash', '-c', cmd])
    min_sleep()
    time.sleep(2) # try it without for awhile # NOPE it really needs to stay apparently
    return p1

def verify_daemon_running():
    print('Check daemon status, should be "found running daemon"'); sys.stdout.flush()
    p = subprocess.run(f'{DAEMON} status'.split(), text=True, capture_output=True)
    print(p.stdout); assert('found running daemon') in p.stdout

    # Extra credit: return pid of running daemon
    import re
    pid = re.search(r'found running daemon ([0-9]+)', p.stdout).group(1)
    return int(pid)

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

def announce(msg=''):
    import inspect
    curframe = inspect.currentframe(); print_header(curframe, msg)
    
# Return True if we are supposed to skip this test
def announce_unit(msg=''):
    import inspect
    curframe = inspect.currentframe(); print_header(curframe, msg)
    if SKIP_UNIT_TESTS: print('- skipping unit tests')
    return SKIP_UNIT_TESTS

def print_header(curframe, msg):
    import inspect
    callerframe = inspect.getouterframes(curframe, 2)
    caller = callerframe[1][3]
    print('\n========================================================================')
    if msg == 'todo' or msg == 'later': msg = ' - TODO'
    print(f"--- TEST: {caller}(){msg}")
    sys.stdout.flush()


#########################################################################
# main(): run proto daemon if script called w args e.g. "--daemon launch"
if __name__ == "__main__":
    if len( sys.argv ) > 1: mydaemon()


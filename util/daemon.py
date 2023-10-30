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
    choices = ['help','launch', 'use-daemon', 'kill']
    filenames = {
        "pid"    : "/tmp/garnet-daemon-pid",
        "state0" : "/tmp/garnet-daemon-state0",
        "reload" : "/tmp/garnet-daemon-reload",
    }

    # TODO
    def save_my_pid(): pass
    def save_my_args(args, filename): pass
    def send_cont_signal_to_daemon(): pass
    def stop_and_wait_for_cont(): pass
    def read_new_args(): pass

    def check_for_daemon(args):

        if args.daemon == "help":
            print(GarnetDaemon_HELP)
            exit()

        elif args.daemon == "launch":
            is_daemon = True
            save_my_pid()
            save_my_args(args, filenames["state0"])
            return is_daemon

        elif args.daemon == "use-daemon":
            # TODO verify that width and height match---or maybe do thatin the daemon---or BOTH
            save_my_args(args, filenames["reload"])
            send_cont_signal_to_daemon()
            exit()             

    def wait():
        stop_and_wait_for cont()
        
        # Continue on receipt of SIGCONT
        args = read_new_args
        if args.daemon == "kill":
            exit()
        else:
            return args

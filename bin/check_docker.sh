#!/bin/bash
# (Designed for use by requirements_check.sh)

# DOCKER ACCESSIBILITY CHECK
# E.g. possible errors:
# 
# ERROR: Got permission denied while trying to connect to the Docker
# daemon socket at unix:///var/run/docker.sock:
# Get http://%2Fvar%2Frun%2Fdocker.sock/v1.40/info:
# dial unix /var/run/docker.sock: connect: permission denied
# 
# ERROR: Cannot connect to the Docker daemon at unix:///var/run/docker.sock.
# Is the docker daemon running?
# 
unset FAIL
echo "--- DOCKER CHECK"
tmpfile=/tmp/tmp.deleteme.$$
docker info |& egrep ^ERROR > $tmpfile && FAIL=true
if [ "$FAIL" == "true" ]; then
    echo "+++ WARNING: DOCKER PROBLEMS"
    echo "Looks like you are unable to use docker for some reason."
    echo "This will be trouble if you're expecting to generate RTL from a container."
    echo "This is the error message I got from trying to do 'docker info':"
    echo ""
    cat $tmpfile
    /bin/rm $tmpfile
    echo ""

    echo "Do you have permission?"
    echo "You should be in the 'docker' group."
    echo "You appear to be in these groups:"
    echo "    % groups"
    groups | sed 's/^/    /'
    echo ""

    echo "Does the socket have the correct permissions?"
    echo "    % ls -l /var/run/docker.sock"
    ls -l /var/run/docker.sock | sed 's/^/    /'
    echo ""
    echo "    % getfacl -p /var/run/docker.sock"
    getfacl -p /var/run/docker.sock | sed 's/^/        /'

    echo "Is the docker daemon running? Try this:"
    echo "    sudo systemctl status docker ; # Check status"
    echo "    sudo systemctl start docker  ; # (Re)start if not running"
    echo ""

    echo "--- Continuing..."
    echo ""
else
    echo "Docker check looks okay."
fi
unset FAIL

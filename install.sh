#!/bin/bash

if [ "$PYTHON" == "" ]; then
    PYTHON="python"
fi

# Use embedded virtualenv
REAL=`python -c 'import os,sys;print os.path.realpath(sys.argv[1])' "$0"`
VIRTUALENV="$PYTHON $(dirname $REAL)/support/virtualenv.py"

if [ ! -e venv ]; then 
    echo "Initializing virtualenv folder (venv)"
    $VIRTUALENV --no-site-packages venv
fi

#. venv/bin/activate

if [ "$1" == "" ]; then
	echo "Installing required libraries"
	venv/bin/pip install -r requirements.txt >> install.log 2>&1
elif [ "$1" == "ldap" ]; then
	echo "Installing ldap libraries"
	venv/bin/pip install python-ldap >> install.log 2>&1
elif [ "$1" == "kerberos" ]; then
	echo "Installing kerberos libraries"
	venv/bin/pip install kerberos >> install.log 2>&1
fi

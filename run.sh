#!/bin/bash

if [ "$(whoami)" != "root" ]; then
    echo "You must be root"
    exit 1
fi

cd $(dirname $0)

start() {
    if [ ! -e tmp ]; then
        mkdir tmp
	chown nginx tmp
    fi
    if [ -e tmp/uwsgi.pid ]; then
        echo "Is this already running?"
        exit
    fi

    #venv/bin/uwsgi --immediate-uid nginx --pidfile tmp/uwsgi.pid -s 127.0.0.1:8001 -d tmp/uwsgi.log -w wsgi:app
    venv/bin/uwsgi --uid nginx --gid nginx --pidfile tmp/uwsgi.pid -s tmp/uwsgi.sock -d tmp/uwsgi.log -w wsgi:app
    sleep 2
    chmod 770 tmp/uwsgi.sock
}

stop() {
    if [ -e tmp/uwsgi.pid ]; then
        PID=$(cat tmp/uwsgi.pid)
        i=0
        while [[ $i -lt 3 && -e /proc/$PID ]]; do
            echo "Killing uWSGI server... ($PID)"
            kill $PID
            sleep 5
            let i="$i+1"
        done
        if [ -e /proc/$PID ]; then
            echo "Really killing $PID..."
            kill -9 $PID
        fi
        rm tmp/uwsgi.pid
	if [ -e tmp/uwsgi.sock ]; then
		rm tmp/uwsgi.sock
	fi
    fi
}

status() {
    if [ -e tmp/uwsgi.pid ]; then
        PID=$(cat tmp/uwsgi.pid)
        if [ -e /proc/$PID ]; then
            echo "Status: running ($PID)"
        else
            echo "Status: zombie ($PID)"
        fi
    else
        echo "Status: not running"
    fi
}

case "$1" in 
start)
    start
    ;;
status)
    status
    ;;
stop)
    stop
    ;;
restart)
    stop && start
    ;;
*)
    echo "Usage: $0 start|stop|status"
    ;;
esac

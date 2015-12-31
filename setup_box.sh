#!/bin/sh

if [[ $# -ne 1 ]]; then
    echo "setup_box.sh: Set up a connected fishbox Raspberry Pi from the main fixbox server."
    echo
    echo "Usage: $0 hostname"
    echo
    echo "The Pi must be running and connected to the same network as the server."
    exit 1
fi

hostname=$1

cmd="ssh-copy-id pi@$hostname"
$cmd

if [[ $? -ne 0 ]]; then
    echo "Error running ${cmd}.  Setup aborted."
    exit 1
fi

cmd="ssh pi@$hostname \"cd fishycam; python fishremote.py > /dev/null &\""
$cmd

if [[ $? -ne 0 ]]; then
    echo "Error running ${cmd}.  Setup aborted."
    exit 1
fi

echo "Setup complete for ${hostname}."

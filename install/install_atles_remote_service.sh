#!/bin/sh

if [ $# -ne 1 ]; then
    echo "install_atles_remote_service.sh: Install the atles_remote service on the local machine."
    echo
    echo "Usage: sudo $0 ATLES_DIR"
    echo
    echo "This generally will be run for you by setup_box.sh, and shouldn't"
    echo "need to be run separately."
    exit 1
fi


DIR=$1
NAME=atles_remote
SCRIPT=$DIR/install/$NAME.initscript

if [ ! -f $SCRIPT ]; then
    echo "Initscript $SCRIPT does not exist."
    exit 1
fi

cp $SCRIPT /etc/init.d/$NAME
chmod +x /etc/init.d/$NAME
update-rc.d $NAME defaults

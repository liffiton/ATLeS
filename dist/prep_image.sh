#!/bin/sh

echo "Prepping in $1...  press Enter to continue (CTL-C to stop)"

read dummy

rm $1/etc/systemd/system/multi-user.target.wants/atles_remote.service
rm $1/etc/systemd/system/atles_remote.service
rm -r $1/home/pi/.python_history
rm -r $1/home/pi/.lesshst
rm -r $1/home/pi/.bash_history
rm -r $1/home/pi/.ssh/
rm -r $1/home/pi/ATLeS/data/
rm -r $1/var/backups/*
rm -r $1/var/cache/*
rm -r $1/var/log/*
rm -r $1/var/spool/*
rm -r $1/var/tmp/*
rm -r $1/var/swap

echo "Files removed."
echo "Please manually add 'init=/usr/lib/raspi-config/init_resize.sh' to the image's /boot/cmdline.txt."

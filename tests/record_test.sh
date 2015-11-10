#!/bin/sh
#
# Usage: record_test.sh RECLENGTH
#
# Reclength given in seconds

if [ $# -lt 1 ] ; then
    echo "USage: $0 RECLENGTH"
    exit
fi

w=240
h=180
fps=10
shutter=50000   # take v4l2 exposure setting, multiply by 100 (from units of 0.1ms to us)
l_sec=$1
length=$((l_sec * 1000))

filename="testvid_`date +%Y%m%d-%H%M`.h264"

cmd="raspivid -o $filename -w $w -h $h -fps $fps -ss $shutter -t $length -ex verylong -ISO 400 -awb off -awbg 1.2,1 -p 100,100,320,240"

echo $cmd
$cmd


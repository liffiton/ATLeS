---
layout: page
title: Box Software Installation and Setup
---

## Writing an Image to a New Card

  1) Put card into card reader in a Linux machine.

  2) Unmount the partitions if auto-mounted (Ubuntu auto-mounts them)

       sudo umount /dev/[device of auto-mounted partition[s]]

  3) Use gunzip | dd to decompress and write the image to the card

       gunzip -c fishypi.gz | sudo dd bs=1M of=/dev/[device of entire card]


## Setting Up a Newly Cloned System

Login as pi/fishypi.

Run `sudo raspi-config`:
  1) Expand filesystem to fit
  2) Set hostname


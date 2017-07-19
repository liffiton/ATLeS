---
title: Box Software Cloning
---

# Box Software Cloning

These instructions are for developers who wish to create a new base OS image to install on ATLeS box Raspberry Pis.

[TODO: Issues w/ current build]
 * ~pi/fishycam is cloned from hyperion

## Making a New Image

To save a disk image of a working/configured Raspberry Pi SD card:

1. Put card into card reader in a Linux machine.

2. Unmount the partitions if auto-mounted (Ubuntu auto-mounts them)

       $ sudo umount /dev/[device of auto-mounted partition[s]]

3. Use `gparted` to shrink the root partition on the card to just
   the used space plus a small buffer.  (E.g., with 2.20GiB used,
   `resize2fs` wouldn't let me make it 2500MiB, but 3000MiB was okay.)

4. Determine the number of blocks now occupied.
   (Adapted from: [http://raspberrypi.stackexchange.com/a/8314](http://raspberrypi.stackexchange.com/a/8314))

       $ sudo fdisk -l /dev/[device of entire card (e.g., sdd)]
   
   Prints the partition table.

   Record 'End' of final partition and sector size.

5. Use `dd | gzip` to create the image using the size from the previous step.
    
       $ sudo dd bs=[sector size] count=[end of final partition + 1] if=/dev/[device of entire card] | gzip > fishypi_`date +%Y%m%d`.img.gz
